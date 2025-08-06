from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from .models import db, Utilisateur, Evenement, FicheImplique
from werkzeug.security import check_password_hash
from datetime import datetime
from functools import wraps

main_bp = Blueprint("main_bp", __name__)

# Déco login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("main_bp.login"))
        return f(*args, **kwargs)
    return decorated_function

# Récupération de l'utilisateur connecté
def get_user():
    if "user_id" in session:
        return Utilisateur.query.get(session["user_id"])
    return None

# Page de connexion
@main_bp.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = Utilisateur.query.filter_by(nom_utilisateur=username).first()

        if user and user.check_password(password):
            session["user_id"] = user.id
            return redirect(url_for("main_bp.evenement_new"))
        else:
            flash("Nom d’utilisateur ou mot de passe incorrect", "danger")

    return render_template("login.html")

# Déconnexion
@main_bp.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect(url_for("main_bp.login"))

# Création d’un événement (admin/codep uniquement)
@main_bp.route("/evenement/new", methods=["GET", "POST"])
@login_required
def evenement_new():
    user = get_user()

    if not user or not (user.is_admin or user.role == "codep"):
        flash("Accès refusé : seuls les administrateurs ou CODEP peuvent créer un événement.", "danger")
        return redirect(url_for("main_bp.login"))

    if request.method == "POST":
        nom = request.form["nom"]
        type_evt = request.form["type_evt"]

        # Génération du numéro unique de l'événement
        now = datetime.now()
        base_numero = f"038{now.strftime('%y%m')}"
        existing = Evenement.query.filter(Evenement.numero.like(f"{base_numero}%")).count()
        numero = f"{base_numero}{str(existing + 1).zfill(2)}"

        evenement = Evenement(numero=numero, nom=nom, type=type_evt)
        db.session.add(evenement)
        db.session.commit()

        # Associer automatiquement l’admin/codep à l’événement
        if user.role == "codep" or user.is_admin:
            user.evenement = evenement
            db.session.commit()

        flash("Événement créé avec succès.", "success")
        return redirect(url_for("main_bp.dashboard"))

    evenements = Evenement.query.all()
    return render_template("evenement_new.html", user=user, evenements=evenements)

# Sélection d’un événement existant
@main_bp.route("/evenement/select", methods=["POST"])
@login_required
def select_evenement():
    user = get_user()
    evenement_id = request.form.get("evenement_id")

    if evenement_id:
        evenement = Evenement.query.get(int(evenement_id))
        if evenement:
            user.evenement = evenement
            db.session.commit()
            return redirect(url_for("main_bp.dashboard"))

    flash("Erreur lors de la sélection de l’évènement.", "danger")
    return redirect(url_for("main_bp.evenement_new"))

# Tableau de bord
@main_bp.route("/dashboard")
@login_required
def dashboard():
    user = get_user()

    if not user.evenement:
        flash("Aucun événement sélectionné.", "warning")
        return redirect(url_for("main_bp.evenement_new"))

    fiches = FicheImplique.query.filter_by(evenement_id=user.evenement.id).all()
    return render_template("dashboard.html", user=user, evenement=user.evenement, impliques=fiches)

@main_bp.route("/fiche/new", methods=["GET", "POST"])
@login_required
def fiche_new():
    user = get_current_user()
    if not user or not user.evenement_id:
        return redirect(url_for("main_bp.evenement_new"))

    if request.method == "POST":
        nom = request.form.get("nom")
        prenom = request.form.get("prenom")
        humain = request.form.get("humain") == "on"
        numero = generate_numero_fiche(user.evenement_id)

        fiche = FicheImplique(
            numero_fiche=numero,
            nom=nom,
            prenom=prenom,
            humain=humain,
            nom_createur=user.nom,
            prenom_createur=user.prenom,
            createur_id=user.id,
            evenement_id=user.evenement_id
        )
        db.session.add(fiche)
        db.session.commit()
        return redirect(url_for("main_bp.dashboard"))

    return render_template("fiche_new.html", user=user)



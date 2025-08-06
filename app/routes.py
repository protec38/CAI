from flask import Blueprint, render_template, request, redirect, url_for, session
from .models import db, Utilisateur, Evenement, FicheImplique
from datetime import datetime

main_bp = Blueprint("main_bp", __name__)

# 🔐 Déco : vérifie que l'utilisateur est connecté
def login_required(f):
    from functools import wraps

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("main_bp.login"))
        return f(*args, **kwargs)

    return decorated_function

# 🔐 Récupère l'utilisateur connecté
def get_current_user():
    user_id = session.get("user_id")
    if user_id:
        return Utilisateur.query.get(user_id)
    return None

# 🟢 Page de login
@main_bp.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = Utilisateur.query.filter_by(nom_utilisateur=username).first()
        if user and user.check_password(password):
            session["user_id"] = user.id
            return redirect(url_for("main_bp.evenement_new"))

    return render_template("login.html")

# 🔴 Déconnexion
@main_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("main_bp.login"))

# ✅ Création ou sélection d’un événement
@main_bp.route("/evenement/new", methods=["GET", "POST"])
@login_required
def evenement_new():
    user = get_current_user()

    if not user.is_admin and user.role != "codep":
        return redirect(url_for("main_bp.dashboard"))

    if request.method == "POST":
        if "create_event" in request.form:
            nom = request.form["nom"]
            type_evt = request.form["type_evt"]

            nouvel_evt = Evenement(nom=nom, type=type_evt)
            db.session.add(nouvel_evt)
            db.session.commit()

            # Associe tous les admin et codep à ce nouvel événement
            users = Utilisateur.query.filter(
                (Utilisateur.is_admin == True) | (Utilisateur.role == "codep")
            ).all()
            for u in users:
                u.evenement_id = nouvel_evt.id
            db.session.commit()

            session["evenement_id"] = nouvel_evt.id
            return redirect(url_for("main_bp.dashboard"))

        elif "selected_event" in request.form:
            selected_event_id = request.form["selected_event"]
            session["evenement_id"] = selected_event_id
            return redirect(url_for("main_bp.dashboard"))

    evenements = Evenement.query.order_by(Evenement.date_creation.desc()).all()
    return render_template("evenement_new.html", user=user, evenements=evenements)

# 📋 Tableau de bord de l'événement actif
@main_bp.route("/dashboard")
@login_required
def dashboard():
    user = get_current_user()
    evenement_id = session.get("evenement_id")

    if not evenement_id:
        return redirect(url_for("main_bp.evenement_new"))

    evenement = Evenement.query.get(evenement_id)
    fiches = FicheImplique.query.filter_by(evenement_id=evenement_id).all()

    return render_template("dashboard.html", user=user, evenement=evenement, impliques=fiches)

# ➕ Nouvelle fiche impliqué
@main_bp.route("/fiche/new", methods=["GET", "POST"])
@login_required
def fiche_new():
    user = get_current_user()
    evenement_id = session.get("evenement_id")

    if not evenement_id:
        return redirect(url_for("main_bp.evenement_new"))

    if request.method == "POST":
        fiche = FicheImplique(
            numero_fiche=request.form["numero_fiche"],
            humain=request.form.get("humain") == "on",
            nom=request.form["nom"],
            prenom=request.form["prenom"],
            date_naissance=datetime.strptime(request.form["date_naissance"], "%Y-%m-%d") if request.form["date_naissance"] else None,
            nationalite=request.form["nationalite"],
            adresse=request.form["adresse"],
            telephone=request.form["telephone"],
            personne_a_prevenir=request.form["personne_a_prevenir"],
            tel_personne_a_prevenir=request.form["tel_personne_a_prevenir"],
            recherche_personne=request.form["recherche_personne"],
            difficulte=request.form["difficulte"],
            competences=request.form["competences"],
            effets_perso=request.form["effets_perso"],
            nom_createur=user.nom,
            prenom_createur=user.prenom,
            destination=request.form["destination"],
            moyen_transport=request.form["moyen_transport"],
            evenement_id=evenement_id,
            createur_id=user.id,
        )
        db.session.add(fiche)
        db.session.commit()
        return redirect(url_for("main_bp.dashboard"))

    return render_template("fiche_new.html", user=user)

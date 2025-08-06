from flask import Blueprint, render_template, redirect, url_for, request, session, flash
from . import db, bcrypt
from .models import Utilisateur, Evenement, FicheImplique
from datetime import datetime
from functools import wraps

main_bp = Blueprint("main_bp", __name__)

# 🔐 Décorateur de connexion
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("main_bp.login"))
        return f(*args, **kwargs)
    return decorated_function

# 🔄 Récupère l'utilisateur courant
def get_current_user():
    if "user_id" in session:
        return Utilisateur.query.get(session["user_id"])
    return None

# 🟢 Route : Login
@main_bp.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = Utilisateur.query.filter_by(nom_utilisateur=username).first()
        if user and user.check_password(password):
            session["user_id"] = user.id
            if user.role in ["admin", "codep"]:
                return redirect(url_for("main_bp.evenement_new"))
            else:
                return redirect(url_for("main_bp.dashboard"))
        else:
            flash("Identifiants invalides.")
    return render_template("login.html")

# 🔴 Déconnexion
@main_bp.route("/logout")
@login_required
def logout():
    session.pop("user_id", None)
    return redirect(url_for("main_bp.login"))

# 🔁 Création et sélection d'événements
@main_bp.route("/evenement/new", methods=["GET", "POST"])
@login_required
def evenement_new():
    user = get_current_user()
    if user.role not in ["admin", "codep"]:
        flash("Accès refusé.")
        return redirect(url_for("main_bp.dashboard"))

    evenements = Evenement.query.order_by(Evenement.date_creation.desc()).all()

    if request.method == "POST":
        if "select_evt" in request.form:
            selected_id = request.form["select_evt"]
            user.evenement_id = selected_id
            db.session.commit()
            return redirect(url_for("main_bp.dashboard"))

        if "nom" in request.form and "type_evt" in request.form:
            nom = request.form["nom"]
            type_evt = request.form["type_evt"]
            numero_base = datetime.utcnow().strftime("%y%m%d")
            last_evt = Evenement.query.order_by(Evenement.id.desc()).first()
            index = f"{(last_evt.id + 1) if last_evt else 1:02d}"
            numero = f"{numero_base}{index}"
            evenement = Evenement(nom=nom, type=type_evt, numero=numero)
            db.session.add(evenement)
            db.session.commit()

            # Associer tous les admins/codep existants à l'événement
            admins = Utilisateur.query.filter(Utilisateur.role.in_(["admin", "codep"])).all()
            for a in admins:
                a.evenement_id = evenement.id
            user.evenement_id = evenement.id
            db.session.commit()

            return redirect(url_for("main_bp.dashboard"))

    return render_template("evenement_new.html", user=user, evenements=evenements)

# 📋 Dashboard
@main_bp.route("/dashboard")
@login_required
def dashboard():
    user = get_current_user()
    if not user.evenement_id:
        return redirect(url_for("main_bp.evenement_new"))

    evenement = Evenement.query.get(user.evenement_id)
    fiches = FicheImplique.query.filter_by(evenement_id=evenement.id).all()
    return render_template("dashboard.html", user=user, evenement=evenement, impliques=fiches)

# ➕ Créer une fiche impliquée
@main_bp.route("/fiche/new", methods=["GET", "POST"])
@login_required
def fiche_new():
    user = get_current_user()
    if not user.evenement_id:
        flash("Aucun événement sélectionné.")
        return redirect(url_for("main_bp.evenement_new"))

    if request.method == "POST":
        nom = request.form["nom"]
        prenom = request.form["prenom"]
        date_naissance = request.form["date_naissance"]
        date_naissance = datetime.strptime(date_naissance, "%Y-%m-%d").date() if date_naissance else None
        humain = True if request.form.get("humain") == "on" else False
        nationalite = request.form.get("nationalite", "")
        adresse = request.form.get("adresse", "")
        telephone = request.form.get("telephone", "")
        personne_a_prevenir = request.form.get("personne_a_prevenir", "")
        tel_personne_a_prevenir = request.form.get("tel_personne_a_prevenir", "")
        recherche_personne = request.form.get("recherche_personne", "")
        difficulte = request.form.get("difficulte", "")
        competences = request.form.get("competences", "")
        effets_perso = request.form.get("effets_perso", "")

        evenement = Evenement.query.get(user.evenement_id)
        last_fiche = FicheImplique.query.filter_by(evenement_id=evenement.id).order_by(FicheImplique.id.desc()).first()
        index = (last_fiche.id + 1) if last_fiche else 1
        numero_fiche = f"{evenement.numero}{index:03d}"

        fiche = FicheImplique(
            numero_fiche=numero_fiche,
            nom=nom,
            prenom=prenom,
            humain=humain,
            date_naissance=date_naissance,
            nationalite=nationalite,
            adresse=adresse,
            telephone=telephone,
            personne_a_prevenir=personne_a_prevenir,
            tel_personne_a_prevenir=tel_personne_a_prevenir,
            recherche_personne=recherche_personne,
            difficulte=difficulte,
            competences=competences,
            effets_perso=effets_perso,
            nom_createur=user.nom,
            prenom_createur=user.prenom,
            createur_id=user.id,
            evenement_id=user.evenement_id
        )
        db.session.add(fiche)
        db.session.commit()

        return redirect(url_for("main_bp.dashboard"))

    return render_template("fiche_new.html", user=user)

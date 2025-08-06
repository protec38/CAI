from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from .models import Utilisateur, Evenement, FicheImplique
from . import db
from werkzeug.security import check_password_hash
from functools import wraps
from datetime import datetime

main_bp = Blueprint("main_bp", __name__)

# 🔒 Décorateur pour vérifier l’authentification
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("main_bp.login"))
        return f(*args, **kwargs)
    return decorated_function

# 🔧 Fonction utilitaire
def get_current_user():
    return Utilisateur.query.get(session["user_id"])

# 🔐 Page de connexion
@main_bp.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        nom_utilisateur = request.form["username"]
        mot_de_passe = request.form["password"]
        user = Utilisateur.query.filter_by(nom_utilisateur=nom_utilisateur).first()

        if user and user.check_password(mot_de_passe):
            session["user_id"] = user.id
            return redirect(url_for("main_bp.evenement_new"))
        else:
            flash("Nom d'utilisateur ou mot de passe invalide.", "danger")

    return render_template("login.html")

# 🔓 Déconnexion
@main_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("main_bp.login"))

# 📋 Création + sélection d’un événement
@main_bp.route("/evenement/new", methods=["GET", "POST"])
@login_required
def evenement_new():
    user = get_current_user()

    if request.method == "POST":
        # Création d’un événement
        nom_evt = request.form["nom_evt"]
        type_evt = request.form["type_evt"]

        last_evt = Evenement.query.order_by(Evenement.id.desc()).first()
        next_id = last_evt.id + 1 if last_evt else 1
        numero_evt = str(next_id).zfill(8)

        nouvel_evt = Evenement(
            numero=numero_evt,
            nom=nom_evt,
            type=type_evt,
            date_creation=datetime.utcnow(),
        )
        db.session.add(nouvel_evt)
        db.session.commit()

        # Lier automatiquement l'utilisateur admin/codep à l'événement
        if user.is_admin or user.role == "codep":
            user.evenement_id = nouvel_evt.id
            db.session.commit()

        flash("Événement créé avec succès !", "success")
        return redirect(url_for("main_bp.dashboard"))

    evenements = Evenement.query.all()
    return render_template("evenement_new.html", user=user, evenements=evenements)

# 🔁 Sélection d’un événement existant
@main_bp.route("/evenement/select", methods=["POST"])
@login_required
def select_evenement():
    user = get_current_user()
    evt_id = request.form.get("evenement_id")

    if evt_id:
        user.evenement_id = int(evt_id)
        db.session.commit()
        return redirect(url_for("main_bp.dashboard"))
    else:
        flash("Veuillez sélectionner un événement.", "warning")
        return redirect(url_for("main_bp.evenement_new"))

# 🏠 Tableau de bord
@main_bp.route("/dashboard")
@login_required
def dashboard():
    user = get_current_user()
    if not user.evenement_id:
        flash("Aucun événement sélectionné.", "warning")
        return redirect(url_for("main_bp.evenement_new"))

    evenement = Evenement.query.get(user.evenement_id)
    fiches = FicheImplique.query.filter_by(evenement_id=evenement.id).all()

    return render_template("dashboard.html", user=user, evenement=evenement, impliques=fiches)

# ➕ Création fiche impliqué
@main_bp.route("/fiche/new", methods=["GET", "POST"])
@login_required
def fiche_new():
    user = get_current_user()

    if not user.evenement_id:
        flash("Aucun événement sélectionné.", "error")
        return redirect(url_for("main_bp.evenement_new"))

    # ✅ Calculer le numéro à afficher
    last_fiche = FicheImplique.query.order_by(FicheImplique.id.desc()).first()
    next_id = 1 if not last_fiche else last_fiche.id + 1
    numero_fiche = f"{next_id:04d}"

    if request.method == "POST":
        fiche = FicheImplique(
            numero_fiche=numero_fiche,
            humain=request.form.get("humain") == "on",
            nom=request.form.get("nom"),
            prenom=request.form.get("prenom"),
            date_naissance=request.form.get("date_naissance"),
            nationalite=request.form.get("nationalite"),
            adresse=request.form.get("adresse"),
            telephone=request.form.get("telephone"),
            personne_a_prevenir=request.form.get("personne_a_prevenir"),
            tel_personne_a_prevenir=request.form.get("tel_personne_a_prevenir"),
            recherche_personne=request.form.get("recherche_personne"),
            difficulte=request.form.get("difficulte"),
            competences=request.form.get("competences"),
            effets_perso=request.form.get("effets_perso"),
            nom_createur=user.nom,
            prenom_createur=user.prenom,
            date_sortie=request.form.get("date_sortie") or None,
            destination=request.form.get("destination"),
            moyen_transport=request.form.get("moyen_transport"),
            createur_id=user.id,
            evenement_id=user.evenement_id
        )
        db.session.add(fiche)
        db.session.commit()

        flash("Fiche impliqué créée avec succès.", "success")
        return redirect(url_for("main_bp.dashboard"))

    # 👉 Affiche le formulaire avec le champ prérempli
    return render_template("fiche_new.html", user=user, numero_fiche=numero_fiche)


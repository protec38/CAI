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
        nom_evt = request.form["nom_evt"]
        type_evt = request.form["type_evt"]
        adresse = request.form["adresse"]
        statut = request.form["statut"]

        # Générer automatiquement le numéro d’évènement
        last_evt = Evenement.query.order_by(Evenement.id.desc()).first()
        next_id = last_evt.id + 1 if last_evt else 1
        numero_evt = str(next_id).zfill(8)

        nouvel_evt = Evenement(
            numero=numero_evt,
            nom=nom_evt,
            type=type_evt,
            adresse=adresse,
            statut=statut,
            date_creation=datetime.utcnow(),
        )

        db.session.add(nouvel_evt)
        db.session.commit()

        # Lier l'utilisateur à l'évènement s'il est admin ou codep
        if user.is_admin or user.role == "codep":
            user.evenement_id = nouvel_evt.id
            db.session.commit()

        flash("Évènement créé avec succès !", "success")
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
    evenement = user.evenement if user else None

    # Récupérer les fiches liées à l’évènement sélectionné
    fiches = []
    if evenement:
        fiches = FicheImplique.query.filter_by(evenement_id=evenement.id).all()

    return render_template(
        "dashboard.html",
        user=user,
        evenement=evenement,
        fiches=fiches
    )


# ➕ Création fiche impliqué
@main_bp.route("/fiche/new", methods=["GET", "POST"])
@login_required
def fiche_new():
    user = get_current_user()
    evenement = Evenement.query.get(user.evenement_id)

    if request.method == "POST":
        numero_fiche = str(FicheImplique.query.count() + 1).zfill(8)
        fiche = FicheImplique(
            numero_fiche=numero_fiche,
            humain=True,
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
            date_sortie=datetime.strptime(request.form["date_sortie"], "%Y-%m-%d") if request.form["date_sortie"] else None,
            destination=request.form["destination"],
            moyen_transport=request.form["moyen_transport"],
            createur_id=user.id,
            evenement_id=evenement.id,
        )
        db.session.add(fiche)
        db.session.commit()
        flash("Fiche impliqué créée avec succès.", "success")
        return redirect(url_for("main_bp.dashboard"))

    return render_template("fiche_new.html", user=user, evenement=evenement)

@main_bp.route("/admin/utilisateurs")
@login_required
def admin_utilisateurs():
    user = get_current_user()

    # Seuls les responsables de centre ou CODEP peuvent voir cette page
    if not (user.is_admin or user.role in ["responsable", "codep"]):
        flash("Accès refusé : vous n'avez pas les droits pour gérer les utilisateurs.", "danger")
        return redirect(url_for("main_bp.dashboard"))

    # Récupérer les utilisateurs liés à l'évènement actuel
    utilisateurs = Utilisateur.query.filter_by(evenement_id=user.evenement_id).all()

    return render_template("admin_utilisateurs.html", user=user, utilisateurs=utilisateurs)

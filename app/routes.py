from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from .models import Utilisateur, Evenement, FicheImplique
from . import db
from werkzeug.security import check_password_hash
from functools import wraps
from datetime import datetime
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
from datetime import datetime

@main_bp.route("/fiche/new", methods=["GET", "POST"])
@login_required
def fiche_new():
    user = get_current_user()
    evenement = user.evenement_selectionne

    if not evenement:
        flash("Aucun événement sélectionné.", "danger")
        return redirect(url_for("main_bp.evenement_new"))

    if request.method == "POST":
        try:
            # Numéro de fiche auto-incrémenté
            dernier = FicheImplique.query.order_by(FicheImplique.id.desc()).first()
            numero_fiche = f"{(dernier.id + 1) if dernier else 1:04d}"

            # Champs
            humain = request.form.get("humain") == "True"
            nom = request.form.get("nom")
            prenom = request.form.get("prenom")
            date_naissance_str = request.form.get("date_naissance")
            date_naissance = datetime.strptime(date_naissance_str, "%Y-%m-%d") if date_naissance_str else None

            nationalite = request.form.get("nationalite")
            adresse = request.form.get("adresse")
            telephone = request.form.get("telephone")
            personne_a_prevenir = request.form.get("personne_a_prevenir")
            tel_personne_a_prevenir = request.form.get("tel_personne_a_prevenir")
            recherche_personne = request.form.get("recherche_personne")
            difficulte = request.form.get("difficulte")
            competences = request.form.get("competences")
            effets_perso = request.form.get("effets_perso")
            destination = request.form.get("destination")
            moyen_transport = request.form.get("moyen_transport")

            # Heure d’arrivée (datetime-local)
            date_entree_str = request.form.get("date_entree")
            date_entree = datetime.strptime(date_entree_str, "%Y-%m-%dT%H:%M") if date_entree_str else datetime.now()

            # Créateur
            nom_createur = user.nom
            prenom_createur = user.prenom

            fiche = FicheImplique(
                numero_fiche=numero_fiche,
                humain=humain,
                nom=nom,
                prenom=prenom,
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
                nom_createur=nom_createur,
                prenom_createur=prenom_createur,
                date_entree=date_entree,
                destination=destination,
                moyen_transport=moyen_transport,
                createur_id=user.id,
                evenement_id=evenement.id
            )

            db.session.add(fiche)
            db.session.commit()
            flash("Fiche impliqué créée avec succès.", "success")
            return redirect(url_for("main_bp.dashboard"))

        except Exception as e:
            db.session.rollback()
            flash(f"Erreur lors de la création de la fiche : {str(e)}", "danger")
            return redirect(url_for("main_bp.fiche_new"))

    # Numéro de fiche estimé (à afficher)
    dernier = FicheImplique.query.order_by(FicheImplique.id.desc()).first()
    numero_fiche = f"{(dernier.id + 1) if dernier else 1:04d}"
    current_time = datetime.now().strftime("%Y-%m-%dT%H:%M")

    return render_template(
        "fiche_new.html",
        user=user,
        numero_fiche=numero_fiche,
        current_time=current_time
    )




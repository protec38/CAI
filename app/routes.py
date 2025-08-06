from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from .models import db, Utilisateur, Evenement, FicheImplique
from flask import current_app
from werkzeug.security import check_password_hash
from datetime import datetime

main_bp = Blueprint("main_bp", __name__)

def current_user():
    user_id = session.get("user_id")
    if user_id:
        return Utilisateur.query.get(user_id)
    return None

@main_bp.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = Utilisateur.query.filter_by(nom_utilisateur=username).first()
        if user and user.check_password(password):
            session["user_id"] = user.id
            return redirect(url_for("main_bp.evenement_choix"))
        else:
            flash("Nom d'utilisateur ou mot de passe incorrect", "error")
    return render_template("login.html")

@main_bp.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect(url_for("main_bp.login"))

@main_bp.route("/evenement/choix", methods=["GET", "POST"])
def evenement_choix():
    user = current_user()
    if not user:
        return redirect(url_for("main_bp.login"))

    evenements = Evenement.query.all()

    if request.method == "POST":
        selected_id = request.form.get("evenement_id")
        if selected_id:
            evenement = Evenement.query.get(int(selected_id))
            user.evenement = evenement
            db.session.commit()
            return redirect(url_for("main_bp.dashboard"))

        # Création d'événement
        if user.role not in ["codep"] and not user.is_admin:
            flash("Vous n'avez pas les droits pour créer un événement", "error")
            return redirect(url_for("main_bp.evenement_choix"))

        nom = request.form.get("nom")
        type_evt = request.form.get("type", "CAI")

        # Générer numéro automatique
        dept = "038"
        now = datetime.utcnow()
        base = f"{dept}{now.strftime('%y%m%d')}"
        similar = Evenement.query.filter(Evenement.numero.like(f"{base}%")).count() + 1
        numero = f"{base}{str(similar).zfill(2)}"

        new_evt = Evenement(nom=nom, type=type_evt, numero=numero)
        db.session.add(new_evt)
        db.session.commit()

        user.evenement = new_evt
        db.session.commit()

        return redirect(url_for("main_bp.dashboard"))

    return render_template("evenement_new.html", evenements=evenements, user=user)

@main_bp.route("/dashboard")
def dashboard():
    user = current_user()
    if not user or not user.evenement:
        return redirect(url_for("main_bp.evenement_choix"))

    fiches = FicheImplique.query.filter_by(evenement_id=user.evenement.id).all()
    return render_template("dashboard.html", user=user, evenement=user.evenement, impliques=fiches)

@main_bp.route("/fiche/new", methods=["GET", "POST"])
def fiche_new():
    user = current_user()
    if not user or not user.evenement:
        return redirect(url_for("main_bp.login"))

    if request.method == "POST":
        fiche = FicheImplique(
            numero_fiche=request.form["numero_fiche"],
            nom=request.form["nom"],
            prenom=request.form["prenom"],
            date_naissance=datetime.strptime(request.form["date_naissance"], "%Y-%m-%d"),
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
            createur_id=user.id,
            evenement_id=user.evenement.id
        )
        db.session.add(fiche)
        db.session.commit()
        return redirect(url_for("main_bp.dashboard"))

    return render_template("fiche_new.html", user=user)

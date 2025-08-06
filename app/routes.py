from flask import Blueprint, render_template, request, redirect, url_for, session
from .models import db, Utilisateur, Evenement, FicheImplique
from functools import wraps
from datetime import datetime

main_bp = Blueprint("main_bp", __name__)

def get_current_user():
    user_id = session.get("user_id")
    if user_id:
        return Utilisateur.query.get(user_id)
    return None

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("main_bp.login"))
        return f(*args, **kwargs)
    return decorated_function

@main_bp.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = Utilisateur.query.filter_by(nom_utilisateur=username).first()
        if user and user.check_password(password):
            session["user_id"] = user.id
            if user.is_admin or user.role == "codep":
                return redirect(url_for("main_bp.evenement_new"))
            return redirect(url_for("main_bp.dashboard"))
    return render_template("login.html")

@main_bp.route("/logout")
@login_required
def logout():
    session.clear()
    return redirect(url_for("main_bp.login"))

@main_bp.route("/evenement/new", methods=["GET", "POST"])
@login_required
def evenement_new():
    user = get_current_user()

    if not user.is_admin and user.role != "codep":
        return redirect(url_for("main_bp.dashboard"))

    if request.method == "POST":
        action = request.form.get("action")

        if action == "creer":
            numero = request.form["numero"]
            nom = request.form["nom"]
            type_evt = request.form["type_evt"]

            evenement = Evenement(numero=numero, nom=nom, type=type_evt)
            db.session.add(evenement)
            db.session.commit()

            users_to_link = Utilisateur.query.filter(
                (Utilisateur.role == "codep") | (Utilisateur.is_admin == True)
            ).all()
            for u in users_to_link:
                u.evenement_id = evenement.id

            db.session.commit()
            return redirect(url_for("main_bp.dashboard"))

        elif action == "acceder":
            selected_id = request.form.get("selected_evenement_id")
            if selected_id:
                user.evenement_id = int(selected_id)
                db.session.commit()
                return redirect(url_for("main_bp.dashboard"))

    evenements = Evenement.query.all()
    return render_template("evenement_new.html", user=user, evenements=evenements)

@main_bp.route("/dashboard")
@login_required
def dashboard():
    user = get_current_user()
    if not user.evenement_id:
        return redirect(url_for("main_bp.evenement_new"))
    evenement = Evenement.query.get(user.evenement_id)
    fiches = FicheImplique.query.filter_by(evenement_id=evenement.id).all()
    return render_template("dashboard.html", user=user, evenement=evenement, impliques=fiches)

@main_bp.route("/fiche/new", methods=["GET", "POST"])
@login_required
def fiche_new():
    user = get_current_user()
    if request.method == "POST":
        fiche = FicheImplique(
            numero_fiche=request.form["numero_fiche"],
            humain=True,
            nom=request.form.get("nom"),
            prenom=request.form.get("prenom"),
            date_naissance=datetime.strptime(request.form.get("date_naissance"), "%Y-%m-%d") if request.form.get("date_naissance") else None,
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
            date_sortie=None,
            destination=request.form.get("destination"),
            moyen_transport=request.form.get("moyen_transport"),
            createur_id=user.id,
            evenement_id=user.evenement_id
        )
        db.session.add(fiche)
        db.session.commit()
        return redirect(url_for("main_bp.dashboard"))

    return render_template("fiche_new.html", user=user)

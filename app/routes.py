from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from . import db
from .models import Utilisateur, Evenement, FicheImplique
from werkzeug.security import check_password_hash
from functools import wraps
from datetime import datetime

main_bp = Blueprint("main_bp", __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('main_bp.login'))
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    user_id = session.get('user_id')
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
            return redirect(url_for("main_bp.evenement_new"))
        else:
            flash("Nom d'utilisateur ou mot de passe incorrect")

    return render_template("login.html")

@main_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("main_bp.login"))

@main_bp.route("/evenement/new", methods=["GET", "POST"])
@login_required
def evenement_new():
    user = get_current_user()
    evenements = Evenement.query.all()

    if request.method == "POST":
        nom_evt = request.form["nom_evt"]
        type_evt = request.form["type_evt"]

        last_evt = Evenement.query.order_by(Evenement.id.desc()).first()
        count = 1 if not last_evt else last_evt.id + 1
        numero = f"{count:03d}"

        evenement = Evenement(
            numero=numero,
            nom=nom_evt,
            type=type_evt
        )
        db.session.add(evenement)
        db.session.commit()

        # Associer automatiquement les admins et codeps à tous les événements
        admins = Utilisateur.query.filter((Utilisateur.is_admin == True) | (Utilisateur.role == 'codep')).all()
        for admin in admins:
            admin.evenement_id = evenement.id
        db.session.commit()

        return redirect(url_for("main_bp.dashboard"))

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
        nom = request.form["nom"]
        prenom = request.form["prenom"]
        date_naissance = datetime.strptime(request.form["date_naissance"], "%Y-%m-%d")

        last_fiche = FicheImplique.query.order_by(FicheImplique.id.desc()).first()
        count = 1 if not last_fiche else last_fiche.id + 1
        numero_fiche = f"{count:03d}"

        fiche = FicheImplique(
            numero_fiche=numero_fiche,
            nom=nom,
            prenom=prenom,
            date_naissance=date_naissance,
            createur_id=user.id,
            evenement_id=user.evenement_id
        )
        db.session.add(fiche)
        db.session.commit()

        return redirect(url_for("main_bp.dashboard"))

    return render_template("fiche_new.html", user=user)

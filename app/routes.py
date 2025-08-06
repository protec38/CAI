from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from .models import Utilisateur, Evenement, FicheImplique
from . import db, bcrypt
from datetime import datetime
from sqlalchemy.exc import IntegrityError

main_bp = Blueprint("main_bp", __name__)

# Fonction utilitaire
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
            session["role"] = user.role

            # Redirection : si admin ou codep => création d'événement
            if user.is_admin or user.role == "codep":
                return redirect(url_for("main_bp.evenement_new"))
            else:
                return redirect(url_for("main_bp.evenement_choix"))
        else:
            flash("Identifiants incorrects", "error")

    return render_template("login.html")

@main_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("main_bp.login"))

@main_bp.route("/evenement/new", methods=["GET", "POST"])
def evenement_new():
    user = current_user()
    if not user or not (user.is_admin or user.role == "codep"):
        flash("Accès refusé", "error")
        return redirect(url_for("main_bp.login"))

    if request.method == "POST":
        nom = request.form["nom"]
        type_evt = request.form["type_evt"]
        date_str = datetime.utcnow().strftime("%y%m%d")
        count = Evenement.query.count() + 1
        numero = f"038{date_str}{count:02d}"

        new_evt = Evenement(nom=nom, type=type_evt, numero=numero)
        db.session.add(new_evt)
        db.session.commit()

        # Associer automatiquement tous les CODEP et ADMIN
        utilisateurs = Utilisateur.query.all()
        for u in utilisateurs:
            if u.is_admin or u.role == "codep":
                u.evenements.append(new_evt)
        # Associer aussi l'utilisateur courant
        if user not in new_evt.utilisateurs:
            user.evenements.append(new_evt)

        db.session.commit()
        session["evenement_id"] = new_evt.id
        return redirect(url_for("main_bp.dashboard"))

    return render_template("evenement_new.html")

@main_bp.route("/evenement/choisir", methods=["GET", "POST"])
def evenement_choix():
    user = current_user()
    if not user:
        return redirect(url_for("main_bp.login"))

    if request.method == "POST":
        evt_id = request.form["evenement_id"]
        session["evenement_id"] = int(evt_id)
        return redirect(url_for("main_bp.dashboard"))

    evenements = user.evenements
    return render_template("evenement_choix.html", evenements=evenements)

@main_bp.route("/dashboard")
def dashboard():
    user = current_user()
    if not user or "evenement_id" not in session:
        return redirect(url_for("main_bp.login"))

    evt_id = session["evenement_id"]
    evenement = Evenement.query.get(evt_id)
    fiches = FicheImplique.query.filter_by(evenement_id=evt_id).all()

    return render_template("dashboard.html", user=user, evenement=evenement, impliques=fiches)

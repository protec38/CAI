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
    if "user_id" not in session:
        return redirect(url_for("main_bp.login"))

    user = Utilisateur.query.get(session["user_id"])

    if request.method == "POST":
        nom = request.form["nom"]
        type_evt = request.form["type_evt"]

        if not (user.is_admin or user.role == "codep"):
            flash("Vous n’avez pas l’autorisation de créer un événement.", "danger")
            return redirect(url_for("main_bp.evenement_new"))

        # Générer automatiquement un numéro unique basé sur la date
        from datetime import datetime
        base = "038" + datetime.utcnow().strftime("%y%m%d")
        chrono = 1
        while True:
            numero = f"{base}{chrono:02d}"
            if not Evenement.query.filter_by(numero=numero).first():
                break
            chrono += 1

        evt = Evenement(numero=numero, nom=nom, type=type_evt)
        db.session.add(evt)
        db.session.commit()

        # Associer l'utilisateur admin/codep à l'événement
        user.evenement_id = evt.id
        db.session.commit()

        return redirect(url_for("main_bp.dashboard"))

    evenements = Evenement.query.all()
    return render_template("evenement_new.html", user=user, evenements=evenements)



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

# Route pour sélectionner un événement existant
@main_bp.route("/evenement/select", methods=["POST"])
@login_required
def select_evenement():
    user = get_user()
    evenement_id = request.form.get("evenement_id")

    if evenement_id:
        from .models import Evenement
        evenement = Evenement.query.get(int(evenement_id))
        if evenement:
            # Lier l'utilisateur à cet événement si ce n'est pas déjà fait
            user.evenement = evenement
            db.session.commit()
            return redirect(url_for("main_bp.dashboard"))
    
    flash("Erreur lors de la sélection de l’évènement.", "danger")
    return redirect(url_for("main_bp.evenement_new"))


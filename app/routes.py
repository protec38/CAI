from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from . import db
from .models import Utilisateur, Evenement, FicheImplique
from datetime import datetime
from werkzeug.security import check_password_hash

main_bp = Blueprint('main_bp', __name__)


def generer_numero_evenement():
    now = datetime.now()
    prefix = "038"
    date_part = now.strftime("%y%m")
    base_code = f"{prefix}{date_part}"

    dernier = (
        Evenement.query
        .filter(Evenement.numero.like(f"{base_code}%"))
        .order_by(Evenement.numero.desc())
        .first()
    )

    if dernier and dernier.numero[-2:].isdigit():
        chrono = int(dernier.numero[-2:]) + 1
    else:
        chrono = 1

    return f"{base_code}{chrono:02}"


@main_bp.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = Utilisateur.query.filter_by(nom_utilisateur=username).first()
        if user and user.check_password(password):
            session["user_id"] = user.id
            session["evenement_id"] = user.evenement_id
            session["role"] = user.role

            # 🔁 Redirection selon rôle
            if user.is_admin or user.role == "codep":
                return redirect(url_for("main_bp.evenement_new"))
            else:
                return redirect(url_for("main_bp.dashboard"))

        flash("Nom d'utilisateur ou mot de passe incorrect.", "danger")
    return render_template("login.html")


@main_bp.route("/dashboard")
def dashboard():
    user = Utilisateur.query.get(session.get("user_id"))
    if not user:
        return redirect(url_for("main_bp.login"))

    evenement = Evenement.query.get(user.evenement_id)
    impliques = FicheImplique.query.filter_by(evenement_id=evenement.id).all()

    return render_template("dashboard.html", user=user, evenement=evenement, impliques=impliques)


@main_bp.route("/evenement/new", methods=["GET", "POST"])
def evenement_new():
    user = Utilisateur.query.get(session.get("user_id"))
    if not user or not (user.is_admin or user.role == "codep"):
        flash("Accès refusé. Seul un administrateur ou un CODEP peut créer un événement.", "danger")
        return redirect(url_for("main_bp.dashboard"))

    if request.method == "POST":
        nom = request.form["nom"]
        type_event = request.form.get("type", "CHU")
        numero = generer_numero_evenement()

        evenement = Evenement(nom=nom, numero=numero, type=type_event)
        db.session.add(evenement)
        db.session.commit()

        flash(f"Événement créé avec succès : {numero}", "success")
        return redirect(url_for("main_bp.dashboard"))

    return render_template("evenement_new.html")


@main_bp.route("/fiche/new", methods=["GET", "POST"])
def fiche_new():
    user = Utilisateur.query.get(session.get("user_id"))
    evenement = Evenement.query.get(user.evenement_id)
    if request.method == "POST":
        data = request.form
        try:
            date_naissance = datetime.strptime(data["date_naissance"], "%Y-%m-%d").date() if data["date_naissance"] else None
        except ValueError:
            date_naissance = None

        fiche = FicheImplique(
            numero_fiche=data["numero_fiche"],
            humain=data.get("humain") == "on",
            nom=data["nom"],
            prenom=data["prenom"],
            date_naissance=date_naissance,
            nationalite=data["nationalite"],
            adresse=data["adresse"],
            telephone=data["telephone"],
            personne_a_prevenir=data["personne_a_prevenir"],
            tel_personne_a_prevenir=data["tel_personne_a_prevenir"],
            recherche_personne=data["recherche_personne"],
            difficulte=data["difficulte"],
            competences=data["competences"],
            effets_perso=data["effets_perso"],
            nom_createur=user.nom,
            prenom_createur=user.prenom,
            createur_id=user.id,
            evenement_id=evenement.id
        )
        db.session.add(fiche)
        db.session.commit()
        flash("Fiche impliqué créée avec succès.", "success")
        return redirect(url_for("main_bp.dashboard"))

    return render_template("fiche_new.html", user=user)

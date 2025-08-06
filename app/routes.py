# app/routes.py

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from .models import db, Utilisateur, Evenement, FicheImplique
from datetime import datetime
from werkzeug.security import check_password_hash

main_bp = Blueprint("main", __name__)

# -----------------------
# Connexion
# -----------------------
@main_bp.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = Utilisateur.query.filter_by(nom_utilisateur=username).first()
        if user and user.check_password(password) and user.actif:
            session["user_id"] = user.id
            return redirect(url_for("main.select_event"))
        flash("Identifiants invalides ou utilisateur inactif.")
    return render_template("login.html")

@main_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("main.login"))

# -----------------------
# Sélection / Création d’événement
# -----------------------
@main_bp.route("/event/select", methods=["GET", "POST"])
def select_event():
    user = Utilisateur.query.get(session.get("user_id"))
    events = Evenement.query.all()

    if request.method == "POST":
        if "create_event" in request.form:
            nom = request.form["nom"]
            type_evt = request.form["type"]
            numero = generate_event_number()
            evt = Evenement(nom=nom, type=type_evt, numero=numero)
            db.session.add(evt)
            db.session.commit()
            return redirect(url_for("main.select_event"))
        elif "select" in request.form:
            session["event_id"] = int(request.form["select"])
            return redirect(url_for("main.dashboard"))

    return render_template("evenement_new.html", user=user, events=events)

def generate_event_number():
    now = datetime.now()
    return f"038{now.strftime('%y%m')}01"

# -----------------------
# Tableau de bord
# -----------------------
@main_bp.route("/dashboard")
def dashboard():
    event_id = session.get("event_id")
    if not event_id:
        return redirect(url_for("main.select_event"))

    event = Evenement.query.get(event_id)
    fiches = FicheImplique.query.filter_by(evenement_id=event_id).all()
    humains = [f for f in fiches if f.humain]
    animaux = [f for f in fiches if not f.humain]
    sortis = [f for f in fiches if f.date_sortie]
    present = [f for f in fiches if not f.date_sortie]

    return render_template("dashboard.html", event=event, fiches=fiches, humains=humains, animaux=animaux, sortis=sortis, present=present)

# -----------------------
# Créer une fiche impliqué
# -----------------------
@main_bp.route("/fiche/new", methods=["GET", "POST"])
def fiche_new():
    user = Utilisateur.query.get(session.get("user_id"))
    event_id = session.get("event_id")

    if request.method == "POST":
        fiche = FicheImplique(
            numero_fiche=request.form["numero_fiche"],
            humain=bool(int(request.form.get("humain", 1))),
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
            createur_id=user.id,
            evenement_id=event_id
        )
        db.session.add(fiche)
        db.session.commit()
        flash("Fiche enregistrée.")
        return redirect(url_for("main.dashboard"))

    return render_template("fiche_form.html")

# -----------------------
# Interface admin : utilisateurs
# -----------------------
@main_bp.route("/admin/users", methods=["GET", "POST"])
def admin_users():
    user = Utilisateur.query.get(session.get("user_id"))
    if not user or not user.is_admin:
        return redirect(url_for("main.dashboard"))

    users = Utilisateur.query.all()
    events = Evenement.query.all()

    if request.method == "POST":
        u = Utilisateur(
            nom_utilisateur=request.form["username"],
            type_utilisateur=request.form["type_utilisateur"],
            niveau=request.form["niveau"],
            role=request.form["role"],
            nom=request.form["nom"],
            prenom=request.form["prenom"],
            is_admin=bool(int(request.form.get("is_admin", 0))),
            actif=True,
            evenement_id=int(request.form["evenement_id"])
        )
        u.set_password(request.form["password"])
        db.session.add(u)
        db.session.commit()
        flash("Utilisateur créé.")

    return render_template("admin_utilisateurs.html", users=users, events=events)

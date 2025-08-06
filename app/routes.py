from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from .models import Utilisateur, Evenement, FicheImplique
from . import db
from datetime import datetime

main_bp = Blueprint("main", __name__)


@main_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = Utilisateur.query.filter_by(nom_utilisateur=username).first()
        if user and user.check_password(password):
            session["user_id"] = user.id
            flash("Connexion réussie.")
            return redirect(url_for("main.dashboard"))
        flash("Identifiants invalides.")
    return render_template("login.html")


@main_bp.route("/logout")
def logout():
    session.clear()
    flash("Déconnecté.")
    return redirect(url_for("main.login"))


@main_bp.route("/")
@main_bp.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("main.login"))

    user = Utilisateur.query.get(session["user_id"])
    impliques = FicheImplique.query.all()

    total = len(impliques)
    humains = sum(1 for i in impliques if i.type == "humain")
    animaux = sum(1 for i in impliques if i.type == "animal")
    sortis = sum(1 for i in impliques if i.date_sortie)

    return render_template(
        "dashboard.html",
        impliques=impliques,
        total=total,
        humains=humains,
        animaux=animaux,
        sortis=sortis,
        user=user
    )


@main_bp.route("/evenement/new", methods=["GET", "POST"])
def create_evenement():
    if "user_id" not in session:
        return redirect(url_for("main.login"))

    user = Utilisateur.query.get(session["user_id"])
    if user.role != "codep":
        flash("Accès réservé aux CODEP.")
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        nom = request.form.get("nom")
        description = request.form.get("description")
        now = datetime.now()
        departement = "038"
        code = f"{departement}{now.strftime('%y%m')}{str(Evenement.query.count() + 1).zfill(2)}"
        evt = Evenement(code=code, nom=nom, description=description)
        db.session.add(evt)
        db.session.commit()
        flash(f"Événement créé avec le code {code}")
        return redirect(url_for("main.dashboard"))

    return render_template("evenement_new.html")


@main_bp.route("/fiche/new", methods=["GET", "POST"])
def create_implique():
    if "user_id" not in session:
        return redirect(url_for("main.login"))

    user = Utilisateur.query.get(session["user_id"])
    evenement = Evenement.query.order_by(Evenement.created_at.desc()).first()
    if not evenement:
        flash("Aucun événement actif.")
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        num_fiche = f"{evenement.code}{str(FicheImplique.query.count() + 1).zfill(3)}"
        fiche = FicheImplique(
            numero_fiche=num_fiche,
            type=request.form.get("type"),
            nom=request.form.get("nom"),
            prenom=request.form.get("prenom"),
            date_naissance=request.form.get("date_naissance"),
            nationalite=request.form.get("nationalite"),
            adresse=request.form.get("adresse"),
            telephone=request.form.get("telephone"),
            personne_a_prevenir=request.form.get("personne_a_prevenir"),
            telephone_a_prevenir=request.form.get("telephone_a_prevenir"),
            recherche_personne=request.form.get("recherche_personne"),
            difficulte=request.form.get("difficulte"),
            competences=request.form.get("competences"),
            cree_par_nom=user.nom,
            cree_par_prenom=user.prenom,
            evenement_id=evenement.id
        )
        db.session.add(fiche)
        db.session.commit()
        flash("Fiche impliqué créée.")
        return redirect(url_for("main.dashboard"))

    return render_template("fiche_new.html")


@main_bp.route("/fiche/<int:fiche_id>/edit", methods=["GET", "POST"])
def edit_implique(fiche_id):
    if "user_id" not in session:
        return redirect(url_for("main.login"))

    fiche = FicheImplique.query.get_or_404(fiche_id)

    if request.method == "POST":
        for field in [
            "type", "nom", "prenom", "date_naissance", "nationalite", "adresse",
            "telephone", "personne_a_prevenir", "telephone_a_prevenir",
            "recherche_personne", "difficulte", "competences"
        ]:
            setattr(fiche, field, request.form.get(field))
        db.session.commit()
        flash("Fiche mise à jour.")
        return redirect(url_for("main.dashboard"))

    return render_template("fiche_edit.html", fiche=fiche)


@main_bp.route("/fiche/<int:fiche_id>/sortie", methods=["GET", "POST"])
def signaler_sortie(fiche_id):
    if "user_id" not in session:
        return redirect(url_for("main.login"))

    fiche = FicheImplique.query.get_or_404(fiche_id)

    if request.method == "POST":
        fiche.date_sortie = datetime.now()
        fiche.sortie_destination = request.form.get("destination")
        fiche.sortie_transport = request.form.get("transport")
        db.session.commit()
        flash("Sortie enregistrée.")
        return redirect(url_for("main.dashboard"))

    return render_template("fiche_sortie.html", fiche=fiche)

@main_bp.route("/select_role", methods=["GET", "POST"])
def select_role():
    if "user_id" not in session:
        return redirect(url_for("main.login"))

    user = Utilisateur.query.get(session["user_id"])
    evenements = Evenement.query.order_by(Evenement.date_creation.desc()).all()

    # Détermination des rôles disponibles selon le profil
    roles = []
    if user.type_utilisateur == "interne":
        if user.niveau == "technicien":
            roles = ["entree_sortie", "bagagerie", "secouriste"]
        elif user.niveau == "encadrant":
            roles = ["entree_sortie", "bagagerie", "secouriste", "responsable", "codep"]
    else:
        roles = ["autorite", "entree_sortie", "bagagerie"]

    if request.method == "POST":
        selected_role = request.form.get("role")
        selected_evt_id = request.form.get("evenement_id")
        evenement = Evenement.query.get(int(selected_evt_id))

        if not evenement:
            flash("Événement invalide.")
            return redirect(url_for("main.select_role"))

        user.role = selected_role
        user.evenement = evenement
        db.session.commit()

        flash(f"Rôle {selected_role} sélectionné pour l'événement {evenement.nom}.")
        return redirect(url_for("main.dashboard"))

    return render_template("select_role.html", user=user, evenements=evenements, roles=roles)

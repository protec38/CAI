from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from .models import db, Utilisateur, Evenement, FicheImplique
from datetime import datetime

main_bp = Blueprint("main", __name__)

# Authentification
@main_bp.route("/")
def index():
    if "user_id" not in session:
        return redirect(url_for("main.login"))
    return redirect(url_for("main.select_role"))

@main_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = Utilisateur.query.filter_by(nom_utilisateur=username).first()
        if user and user.check_password(password):
            session["user_id"] = user.id
            return redirect(url_for("main.select_role"))
        else:
            flash("Identifiants invalides")
    return render_template("login.html")

@main_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("main.login"))

# Sélection du rôle (page statique pour le moment)
@main_bp.route("/select-role", methods=["GET"])
def select_role():
    if "user_id" not in session:
        return redirect(url_for("main.login"))
    return render_template("select_role.html")

# Tableau de bord
@main_bp.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("main.login"))

    impliques = FicheImplique.query.order_by(FicheImplique.date_entree.desc()).all()
    total = len(impliques)
    humains = sum(1 for i in impliques if i.humain)
    animaux = total - humains
    sortis = sum(1 for i in impliques if i.date_sortie)

    return render_template("dashboard.html",
                           impliques=impliques,
                           total=total,
                           humains=humains,
                           animaux=animaux,
                           sortis=sortis)

# Création de fiche impliqué
@main_bp.route("/fiche/new", methods=["GET", "POST"])
def create_implique():
    if "user_id" not in session:
        return redirect(url_for("main.login"))

    if request.method == "POST":
        try:
            numero_fiche = f"038{datetime.now().strftime('%y%m%d')}{str(FicheImplique.query.count() + 1).zfill(3)}"

            # Conversion de la date de naissance (si présente)
            date_naissance_str = request.form.get("date_naissance")
            date_naissance = datetime.strptime(date_naissance_str, "%Y-%m-%d").date() if date_naissance_str else None

            fiche = FicheImplique(
                numero_fiche=numero_fiche,
                humain=bool(int(request.form.get("humain", 1))),
                nom=request.form.get("nom"),
                prenom=request.form.get("prenom"),
                date_naissance=date_naissance,
                nationalite=request.form.get("nationalite"),
                adresse=request.form.get("adresse"),
                telephone=request.form.get("telephone"),
                personne_a_prevenir=request.form.get("personne_a_prevenir"),
                tel_personne_a_prevenir=request.form.get("tel_personne_a_prevenir"),
                recherche_personne=request.form.get("recherche_personne"),
                difficulte=request.form.get("difficulte"),
                competences=request.form.get("competences"),
                effets_perso=request.form.get("effets_perso"),
                nom_createur="Auto",
                prenom_createur="System"
            )

            db.session.add(fiche)
            db.session.commit()

            flash("Fiche créée avec succès")
            return redirect(url_for("main.dashboard"))

        except Exception as e:
            print("❌ Erreur lors de la création de fiche :", e)
            flash("Erreur lors de la création de la fiche")
            return redirect(url_for("main.create_implique"))

    return render_template("formulaire_implique.html")


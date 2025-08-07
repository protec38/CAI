from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from .models import Utilisateur, Evenement, FicheImplique
from . import db
from werkzeug.security import check_password_hash
from functools import wraps
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

    # 🔒 Restriction stricte à admin ou codep
    if not user.is_admin and user.role != "codep":
        flash("⛔ Vous n’avez pas l’autorisation de créer un évènement.", "danger")
        evenements = user.evenements  # on peut quand même lui afficher ceux qu’il voit
        return render_template("evenement_new.html", user=user, evenements=evenements)

    if request.method == "POST":
        nom_evt = request.form["nom_evt"]
        type_evt = request.form["type_evt"]
        adresse = request.form["adresse"]
        statut = request.form["statut"]

        last_evt = Evenement.query.order_by(Evenement.id.desc()).first()
        next_id = last_evt.id + 1 if last_evt else 1
        numero_evt = str(next_id).zfill(8)

        nouvel_evt = Evenement(
            numero=numero_evt,
            nom=nom_evt,
            type_evt=type_evt,
            adresse=adresse,
            statut=statut,
            date_ouverture=datetime.utcnow()
        )

        db.session.add(nouvel_evt)
        db.session.commit()

        # Lier l'utilisateur à l'évènement créé
        if nouvel_evt not in user.evenements:
            user.evenements.append(nouvel_evt)
            db.session.commit()

        flash("✅ Évènement créé avec succès.", "success")
        return redirect(url_for("main_bp.dashboard"))

    # GET
    evenements = Evenement.query.all() if user.is_admin or user.role == "codep" else user.evenements
    return render_template("evenement_new.html", user=user, evenements=evenements)



@main_bp.route("/evenement/<int:evenement_id>/dashboard")
@login_required
def dashboard(evenement_id):
    session["evenement_id"] = evenement_id  # 🧠 Sauvegarde de l'évènement actif
    user = get_current_user()

    evenement = Evenement.query.get(evenement_id)
    if not evenement or evenement not in user.evenements:
        flash("⛔ Vous n’avez pas accès à cet évènement.", "danger")
        return redirect(url_for("main_bp.evenement_new"))

    fiches = FicheImplique.query.filter_by(evenement_id=evenement.id).all()
    return render_template("dashboard.html", user=user, evenement=evenement, fiches=fiches)




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
    evenement = user.evenements[0] if user and user.evenements else None


    # Récupérer les fiches liées à l’évènement sélectionné
    fiches = []
    if evenement:
        fiches = FicheImplique.query.filter_by(evenement_id=evenement.id).all()

    return render_template(
        "dashboard.html",
        user=user,
        evenement=evenement,
        fiches=fiches
    )


# ➕ Création fiche impliqué
@main_bp.route("/fiche/new", methods=["GET", "POST"])
@login_required
def fiche_new():
    user = get_current_user()

    evenement_id = session.get("evenement_id")
    if not evenement_id:
        flash("⛔ Aucun évènement actif. Veuillez d'abord accéder à un évènement.", "danger")
        return redirect(url_for("main_bp.evenement_new"))

    evenement = Evenement.query.get(evenement_id)
    if not evenement or evenement not in user.evenements:
        flash("⛔ Vous n’avez pas accès à cet évènement.", "danger")
        return redirect(url_for("main_bp.evenement_new"))

    if request.method == "POST":
        nom = request.form.get("nom")
        prenom = request.form.get("prenom")
        statut = request.form.get("statut")
        nationalite = request.form.get("nationalite")
        difficulte = request.form.get("difficulte")
        telephone = request.form.get("telephone")

        last_fiche = FicheImplique.query.order_by(FicheImplique.id.desc()).first()
        next_id = last_fiche.id + 1 if last_fiche else 1
        numero = str(next_id).zfill(6)

        fiche = FicheImplique(
            numero=numero,
            nom=nom,
            prenom=prenom,
            statut=statut,
            nationalite=nationalite,
            difficulte=difficulte,
            telephone=telephone,
            evenement_id=evenement.id,
            utilisateur_id=user.id
        )

        db.session.add(fiche)
        db.session.commit()

        flash("✅ Fiche impliqué créée pour l’évènement en cours.", "success")
        return redirect(url_for("main_bp.dashboard", evenement_id=evenement.id))

    return render_template("fiche_new.html", user=user)


########################################################

@main_bp.route("/admin/utilisateurs")
@login_required
def admin_utilisateurs():
    user = get_current_user()

    if not user.is_admin and user.role != "codep":
        flash("⛔ Accès refusé : vous n’avez pas les droits pour gérer les utilisateurs.", "danger")
        return redirect(url_for("main_bp.evenement_new"))

    utilisateurs = Utilisateur.query.all()
    return render_template("admin_utilisateurs.html", utilisateurs=utilisateurs, user=user)





################################################################


@main_bp.route("/admin/utilisateur/create", methods=["GET", "POST"])
@login_required
def utilisateur_create():
    user = get_current_user()
    if not (user.is_admin or user.role == "codep"):
        flash("Accès refusé", "danger")
        return redirect(url_for("main_bp.dashboard"))

    from app.models import Evenement
    all_evenements = Evenement.query.all()

    if request.method == "POST":
        nom = request.form["nom"]
        nom_utilisateur = request.form["nom_utilisateur"]
        role = request.form["role"]
        type_utilisateur = request.form["type_utilisateur"]
        password = request.form["password"]
        evenement_ids = request.form.getlist("evenements")

        existing = Utilisateur.query.filter_by(nom_utilisateur=nom_utilisateur).first()
        if existing:
            flash("Nom d'utilisateur déjà utilisé.", "danger")
            return redirect(url_for("main_bp.utilisateur_create"))

        new_user = Utilisateur(
            nom=nom,
            nom_utilisateur=nom_utilisateur,
            role=role,
            type_utilisateur=type_utilisateur,
        )
        new_user.set_password(password)

        for evt_id in evenement_ids:
            evt = Evenement.query.get(int(evt_id))
            if evt:
                new_user.evenements.append(evt)

        db.session.add(new_user)
        db.session.commit()
        flash("Utilisateur créé avec succès", "success")
        return redirect(url_for("main_bp.admin_utilisateurs"))

    return render_template("utilisateur_form.html", utilisateur=None, all_evenements=all_evenements, mode="create")


###########################################

    
@main_bp.route("/admin/utilisateur/edit/<int:id>", methods=["GET", "POST"])
@login_required
def utilisateur_edit(id):
    user = get_current_user()
    if not (user.is_admin or user.role == "codep"):
        flash("Accès refusé", "danger")
        return redirect(url_for("main_bp.dashboard"))

    utilisateur = Utilisateur.query.get_or_404(id)
    from app.models import Evenement
    all_evenements = Evenement.query.all()

    if request.method == "POST":
        utilisateur.nom = request.form["nom"]
        utilisateur.nom_utilisateur = request.form["nom_utilisateur"]
        utilisateur.role = request.form["role"]
        utilisateur.type_utilisateur = request.form["type_utilisateur"]
        password = request.form["password"]

        if password:
            utilisateur.set_password(password)

        utilisateur.evenements = []
        for evt_id in request.form.getlist("evenements"):
            evt = Evenement.query.get(int(evt_id))
            if evt:
                utilisateur.evenements.append(evt)

        db.session.commit()
        flash("Utilisateur mis à jour.", "success")
        return redirect(url_for("main_bp.admin_utilisateurs"))

    return render_template("utilisateur_form.html", utilisateur=utilisateur, all_evenements=all_evenements, mode="edit")




@main_bp.route("/admin/utilisateur/delete/<int:id>")
@login_required
def utilisateur_delete(id):
    user = get_current_user()
    if not (user.is_admin or user.role in ["responsable", "codep"]):
        flash("Accès refusé.", "danger")
        return redirect(url_for("main_bp.dashboard"))

    utilisateur = Utilisateur.query.get_or_404(id)
    db.session.delete(utilisateur)
    db.session.commit()
    flash("Utilisateur supprimé.", "info")
    return redirect(url_for("main_bp.admin_utilisateurs"))



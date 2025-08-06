from flask import Blueprint, render_template, request, redirect, url_for, session
from app.models import db, Utilisateur, Evenement, FicheImplique
from datetime import datetime, date

main_bp = Blueprint("main_bp", __name__)

def login_required(f):
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for("main_bp.login"))
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    return Utilisateur.query.get(session.get("user_id"))

@main_bp.route("/evenement/new", methods=["GET", "POST"])
@login_required
def evenement_new():
    user = get_current_user()
    evenements = Evenement.query.all()

    if request.method == "POST":
        nom_evt = request.form.get("nom_evt")
        type_evt = request.form.get("type_evt")

        if nom_evt and type_evt:
            nouvel_evt = Evenement(nom_evt=nom_evt, type_evt=type_evt)
            db.session.add(nouvel_evt)
            db.session.commit()

            user.evenement_selectionne = nouvel_evt
            db.session.commit()

            return redirect(url_for("main_bp.dashboard"))

    return render_template("evenement_new.html", user=user, evenements=evenements)

@main_bp.route("/evenement/select", methods=["POST"])
@login_required
def select_evenement():
    user = get_current_user()
    evenement_id = request.form.get("evenement_id")

    if evenement_id:
        evenement = Evenement.query.get(evenement_id)
        if evenement:
            user.evenement_selectionne = evenement
            db.session.commit()

    return redirect(url_for("main_bp.dashboard"))

@main_bp.route("/dashboard")
@login_required
def dashboard():
    user = get_current_user()
    evenement = user.evenement_selectionne

    fiches = FicheImplique.query.filter_by(evenement_id=evenement.id).all() if evenement else []

    return render_template("dashboard.html", user=user, evenement=evenement, impliques=fiches)

@main_bp.route("/fiche/new", methods=["GET", "POST"])
@login_required
def fiche_new():
    user = get_current_user()
    evenement = user.evenement_selectionne

    if not evenement:
        return redirect(url_for("main_bp.evenement_new"))

    if request.method == "POST":
        numero = "{:04}".format(FicheImplique.query.filter_by(evenement_id=evenement.id).count() + 1)

        fiche = FicheImplique(
            numero_fiche=numero,
            humain=(request.form.get("humain") == "True"),
            nom=request.form.get("nom"),
            prenom=request.form.get("prenom"),
            date_naissance=date.fromisoformat(request.form.get("date_naissance")) if request.form.get("date_naissance") else None,
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
            date_entree=datetime.fromisoformat(request.form.get("date_entree")) if request.form.get("date_entree") else datetime.utcnow(),
            destination=request.form.get("destination"),
            moyen_transport=request.form.get("moyen_transport"),
            createur_id=user.id,
            evenement_id=evenement.id,
        )

        db.session.add(fiche)
        db.session.commit()
        return redirect(url_for("main_bp.dashboard"))

    current_time = datetime.now().strftime("%Y-%m-%dT%H:%M")
    numero_fiche = "{:04}".format(FicheImplique.query.filter_by(evenement_id=evenement.id).count() + 1)

    return render_template("fiche_new.html", user=user, current_time=current_time, numero_fiche=numero_fiche)

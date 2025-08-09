from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from .models import Utilisateur, Evenement, FicheImplique
from . import db
from werkzeug.security import check_password_hash
from functools import wraps
from datetime import datetime
from flask import jsonify
from flask_login import current_user
from flask import make_response
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
import io
from flask import send_file
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.units import cm
import os
from io import BytesIO
import re
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

        # Génération du numéro d'évènement
        last_evt = Evenement.query.order_by(Evenement.id.desc()).first()
        next_id = last_evt.id + 1 if last_evt else 1
        numero_evt = str(next_id).zfill(8)

        # Création de l'évènement
        nouvel_evt = Evenement(
            numero=numero_evt,
            nom=nom_evt,
            type_evt=type_evt,
            adresse=adresse,
            statut=statut,
            createur_id=user.id,
            date_ouverture=datetime.utcnow()
        )

        db.session.add(nouvel_evt)
        db.session.commit()

        # Association du créateur à l'évènement
        if nouvel_evt not in user.evenements:
            user.evenements.append(nouvel_evt)
            db.session.commit()

        flash("✅ Évènement créé avec succès.", "success")
        return redirect(url_for("main_bp.dashboard", evenement_id=nouvel_evt.id))

    # 🔁 Méthode GET
    evenements = Evenement.query.all() if user.is_admin or user.role == "codep" else user.evenements
    return render_template("evenement_new.html", user=user, evenements=evenements)




@main_bp.route("/evenement/<int:evenement_id>/dashboard")
@login_required
def dashboard(evenement_id):
    session["evenement_id"] = evenement_id
    user = get_current_user()

    evenement = Evenement.query.get(evenement_id)
    if not evenement or evenement not in user.evenements:
        flash("⛔ Vous n’avez pas accès à cet évènement.", "danger")
        return redirect(url_for("main_bp.evenement_new"))

    fiches = FicheImplique.query.filter_by(evenement_id=evenement.id).all()
    nb_present = FicheImplique.query.filter_by(evenement_id=evenement.id, statut="présent").count()
    nb_total = len(fiches)

    peut_modifier_statut = (
        user.is_admin or
        user.role == "codep" or
        evenement.createur_id == user.id or
        (user.role == "responsable" and user in evenement.utilisateurs)
    )

    return render_template(
        "dashboard.html",
        user=user,
        evenement=evenement,
        fiches=fiches,
        nb_present=nb_present,
        nb_total=nb_total,
        peut_modifier_statut=peut_modifier_statut,
        competence_colors=COMPETENCE_COLORS
    )








# 🔁 Sélection d’un événement existant
@main_bp.route("/evenement/select", methods=["POST"])
@login_required
def select_evenement():
    user = get_current_user()
    evt_id = request.form.get("evenement_id")

    if evt_id:
        session["evenement_id"] = int(evt_id)  # 🧠 on stocke dans la session
        return redirect(url_for("main_bp.dashboard", evenement_id=int(evt_id)))
    else:
        flash("Veuillez sélectionner un événement.", "warning")
        return redirect(url_for("main_bp.evenement_new"))





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

    # ✅ Liste fixe des compétences
    COMPETENCES_CAI = [
        "Médecin", "Infirmier", "Sapeur-pompier", "SST", "Psychologue",
        "Bénévole", "Artisan", "Interprète", "Logisticien", "Conducteur",
        "Agent sécurité", "Autre"
    ]

    # ✅ Liste des pays (France en premier)
    import pycountry
    countries = ["France"] + sorted([c.name for c in pycountry.countries if c.name != "France"])

    if request.method == "POST":
        from datetime import datetime, timedelta

        heure_js_str = request.form.get("heure_arrivee_js")
        try:
            heure_arrivee = datetime.strptime(heure_js_str, "%Y-%m-%dT%H:%M:%S.%fZ") + timedelta(hours=2)
        except Exception:
            heure_arrivee = datetime.utcnow()

        date_naissance_str = request.form.get("date_naissance")
        if date_naissance_str:
            try:
                date_naissance = datetime.strptime(date_naissance_str, "%Y-%m-%d").date()
            except ValueError:
                date_naissance = None
        else:
            date_naissance = None

        nom = request.form.get("nom")
        prenom = request.form.get("prenom")
        nationalite = request.form.get("nationalite")
        adresse = request.form.get("adresse")
        telephone = request.form.get("telephone")
        personne_a_prevenir = request.form.get("personne_a_prevenir")
        tel_personne_a_prevenir = request.form.get("tel_personne_a_prevenir")
        recherche_personne = request.form.get("recherche_personne")
        difficulte = request.form.get("difficulte")

        # ✅ Compétences multiples
        competences = ",".join(request.form.getlist("competences"))

        effets_perso = request.form.get("effets_perso")
        destination = request.form.get("destination")
        moyen_transport = request.form.get("moyen_transport")
        est_animal = bool(request.form.get("est_animal"))
        humain = request.form.get("humain") == "True"
        numero_recherche = request.form.get("numero_recherche")

        # 🔢 Numérotation automatique
        last_fiche_evt = (
            FicheImplique.query
            .filter_by(evenement_id=evenement.id)
            .order_by(FicheImplique.id.desc())
            .first()
        )
        next_local = 1
        if last_fiche_evt and last_fiche_evt.numero:
            try:
                last_parts = last_fiche_evt.numero.split("-")
                if len(last_parts) == 2:
                    next_local = int(last_parts[1]) + 1
            except ValueError:
                pass
        numero = f"{str(evenement.id).zfill(3)}-{str(next_local).zfill(4)}"

        fiche = FicheImplique(
            numero=numero,
            nom=nom,
            prenom=prenom,
            nationalite=nationalite,
            adresse=adresse,
            telephone=telephone,
            personne_a_prevenir=personne_a_prevenir,
            tel_personne_a_prevenir=tel_personne_a_prevenir,
            recherche_personne=recherche_personne,
            difficultes=difficulte,
            competences=competences,
            effets_perso=effets_perso,
            destination=destination,
            moyen_transport=moyen_transport,
            est_animal=est_animal,
            humain=humain,
            numero_recherche=numero_recherche,
            statut="présent",
            heure_arrivee=heure_arrivee,
            date_naissance=date_naissance,
            utilisateur_id=user.id,
            evenement_id=evenement.id,
        )

        db.session.add(fiche)
        db.session.commit()

        flash(f"✅ Fiche n°{numero} créée pour l’évènement en cours.", "success")
        return redirect(url_for("main_bp.dashboard", evenement_id=evenement.id))

    # Prévisualisation du prochain numéro
    last_fiche_evt = (
        FicheImplique.query
        .filter_by(evenement_id=evenement.id)
        .order_by(FicheImplique.id.desc())
        .first()
    )
    next_local = 1
    if last_fiche_evt and last_fiche_evt.numero:
        try:
            last_parts = last_fiche_evt.numero.split("-")
            if len(last_parts) == 2:
                next_local = int(last_parts[1]) + 1
        except ValueError:
            pass

    numero_prevu = f"{str(evenement.id).zfill(3)}-{str(next_local).zfill(4)}"

    return render_template(
        "fiche_new.html",
        user=user,
        numero_prevu=numero_prevu,
        competences_list=COMPETENCES_CAI,
        countries=countries
    )



    




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

# 🔍 Détail d’une fiche impliqué
@main_bp.route("/fiche/<int:id>")
@login_required
def fiche_detail(id):
    user = get_current_user()
    fiche = FicheImplique.query.get_or_404(id)

    if fiche.evenement not in user.evenements and not user.is_admin and user.role != "codep":
        flash("⛔ Vous n'avez pas accès à cette fiche.", "danger")
        return redirect(url_for("main_bp.evenement_new"))

    return render_template("fiche_detail.html", fiche=fiche, user=user)


# ✏️ Modification d’une fiche impliqué
from datetime import datetime

@main_bp.route("/fiche/edit/<int:id>", methods=["GET", "POST"])
@login_required
def fiche_edit(id):
    user = get_current_user()
    fiche = FicheImplique.query.get_or_404(id)

    # Vérification d'accès à l'évènement
    if fiche.evenement not in user.evenements:
        flash("⛔ Vous n’avez pas accès à cet évènement.", "danger")
        return redirect(url_for("main_bp.evenement_new"))

    # Liste des compétences
    COMPETENCES_CAI = [
        "Médecin", "Infirmier", "Sapeur-pompier", "SST", "Psychologue",
        "Bénévole", "Artisan", "Interprète", "Logisticien", "Conducteur",
        "Agent sécurité", "Autre"
    ]

    if request.method == "POST":
        fiche.nom = request.form.get("nom")
        fiche.prenom = request.form.get("prenom")
        fiche.statut = request.form.get("statut")
        fiche.nationalite = request.form.get("nationalite")
        fiche.difficultes = request.form.get("difficulte")
        fiche.telephone = request.form.get("telephone")
        fiche.competences = ",".join(request.form.getlist("competences"))
        fiche.adresse = request.form.get("adresse")
        fiche.recherche_personne = request.form.get("recherche_personne")
        fiche.numero_recherche = request.form.get("numero_recherche") or None

        # ✅ Conversion de la date au bon format
        date_str = request.form.get("date_naissance")
        if date_str:
            try:
                fiche.date_naissance = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                flash("⚠️ Format de date invalide.", "danger")
                return redirect(request.url)
        else:
            fiche.date_naissance = None

        db.session.commit()
        flash("✅ Fiche mise à jour avec succès.", "success")
        return redirect(url_for("main_bp.dashboard", evenement_id=fiche.evenement.id))

    return render_template(
        "fiche_edit.html",
        fiche=fiche,
        user=user,
        competences_list=COMPETENCES_CAI
    )



########################################################################

@main_bp.route("/fiche/delete/<int:id>", methods=["POST"])
@login_required
def fiche_delete(id):
    user = get_current_user()
    fiche = FicheImplique.query.get_or_404(id)

    # Vérification que l'utilisateur a accès à l'évènement
    if fiche.evenement not in user.evenements:
        flash("⛔ Vous n’avez pas l’autorisation de supprimer cette fiche.", "danger")
        return redirect(url_for("main_bp.evenement_new"))

    db.session.delete(fiche)
    db.session.commit()
    flash("🗑️ Fiche supprimée avec succès.", "info")
    return redirect(url_for("main_bp.dashboard", evenement_id=fiche.evenement.id))



################################################################################



@main_bp.route("/fiche/<int:id>/sortie", methods=["GET", "POST"])
@login_required
def fiche_sortie(id):
    fiche = FicheImplique.query.get_or_404(id)

    user = get_current_user()
    if fiche.evenement not in user.evenements:
        flash("⛔ Vous n’avez pas accès à cette fiche.", "danger")
        return redirect(url_for("main_bp.dashboard", evenement_id=fiche.evenement_id))

    # Marquer la fiche comme "sortie"
    fiche.statut = "sorti"
    fiche.heure_sortie = datetime.utcnow()  # ⬅️ Ajout de l'heure de sortie
    db.session.commit()

    flash(f"🚪 La fiche de {fiche.nom} a été marquée comme sortie.", "info")
    return redirect(url_for("main_bp.dashboard", evenement_id=fiche.evenement_id))



###############################################################



@main_bp.route("/evenement/<int:evenement_id>/update_statut", methods=["POST"])
@login_required
def update_evenement_statut(evenement_id):
    user = get_current_user()
    evenement = Evenement.query.get_or_404(evenement_id)

    if evenement not in user.evenements and not user.is_admin:
        flash("⛔ Accès refusé.", "danger")
        return redirect(url_for("main_bp.evenement_new"))

    new_statut = request.form.get("statut_evt")
    if new_statut:
        evenement.statut = new_statut
        db.session.commit()
        flash("✅ Statut de l’évènement mis à jour.", "success")

    return redirect(url_for("main_bp.dashboard", evenement_id=evenement.id))

#############################################

@main_bp.route("/evenement/<int:evenement_id>/fiches_json")
@login_required
def fiches_json(evenement_id):
    fiches = FicheImplique.query.filter_by(evenement_id=evenement_id).all()

    fiches_data = []
    for fiche in fiches:
        heure_locale = fiche.heure_arrivee_locale  # ✅ ici on la définit
        heure_sortie_locale = fiche.heure_sortie_locale  # (si tu veux aussi l'ajouter)

        fiches_data.append({
            "id": fiche.id,
            "numero": fiche.numero,
            "nom": fiche.nom,
            "prenom": fiche.prenom,
            "statut": fiche.statut,
            "heure_arrivee": heure_locale.strftime('%d/%m/%Y %H:%M') if heure_locale else "-",
            "heure_sortie": heure_sortie_locale.strftime('%d/%m/%Y %H:%M') if heure_sortie_locale else "-",  # optionnel
            "destination": fiche.destination or "",
            "difficultes": fiche.difficultes or "",
            "competences": fiche.competences or ""
        })

    return jsonify({
        "fiches": fiches_data,
        "nb_present": sum(1 for f in fiches if f.statut == "présent"),
        "nb_total": len(fiches),
        "statut_evenement": fiches[0].evenement.statut if fiches else ""
    })

#####################################################################

COMPETENCE_COLORS = {
    "Médecin": "#e74c3c",
    "Infirmier": "#3498db",
    "Sapeur-pompier": "#e67e22",
    "SST": "#1abc9c",
    "Psychologue": "#9b59b6",
    "Bénévole": "#34495e",
    "Artisan": "#f39c12",
    "Interprète": "#2ecc71",
    "Logisticien": "#16a085",
    "Conducteur": "#d35400",
    "Agent sécurité": "#2c3e50",
    "Autre": "#7f8c8d"
}



#############################################"

@main_bp.route("/fiche/<int:id>/pdf")
@login_required
def export_pdf_fiche(id):
    fiche = FicheImplique.query.get_or_404(id)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=60, bottomMargin=40)

    story = []

    # === STYLES ===
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Titre', fontSize=22, alignment=1, textColor=colors.HexColor("#002f6c"), spaceAfter=20))
    styles.add(ParagraphStyle(name='SectionTitle', fontSize=14, textColor=colors.HexColor("#f58220"), spaceBefore=15, spaceAfter=8, underlineWidth=1))
    styles.add(ParagraphStyle(name='NormalBold', parent=styles['Normal'], fontName='Helvetica-Bold'))

    # === LOGO + TITRE ===
    logo_path = os.path.join("static", "img", "logo-protection-civile.jpg")
    if os.path.exists(logo_path):
        img = Image(logo_path, width=70, height=70)
        img.hAlign = 'CENTER'
        story.append(img)

    story.append(Paragraph("Fiche Impliqué", styles['Titre']))

    # === INFOS PERSO ===
    story.append(Paragraph("Informations personnelles", styles['SectionTitle']))
    data_perso = [
        ["Numéro", fiche.numero],
        ["Nom", fiche.nom],
        ["Prénom", fiche.prenom],
        ["Date de naissance", fiche.date_naissance.strftime('%d/%m/%Y') if fiche.date_naissance else "Non renseignée"],
        ["Nationalité", fiche.nationalite or "Non renseignée"],
        ["Adresse", fiche.adresse or "Non renseignée"],
        ["Téléphone", fiche.telephone or "Non renseigné"],
    ]
    story.append(_styled_table(data_perso))

    # === INFOS HORAIRES ===
    story.append(Paragraph("Heures", styles['SectionTitle']))
    data_horaires = [
        ["Heure d’arrivée", fiche.heure_arrivee_locale.strftime('%d/%m/%Y %H:%M') if fiche.heure_arrivee_locale else "Non renseignée"],
        ["Heure de sortie", fiche.heure_sortie_locale.strftime('%d/%m/%Y %H:%M') if fiche.heure_sortie_locale else "Non sortie"]
    ]
    story.append(_styled_table(data_horaires))

    # === INFOS SUP ===
    story.append(Paragraph("Informations supplémentaires", styles['SectionTitle']))
    data_supp = [
        ["Statut", fiche.statut],
        ["Difficultés", fiche.difficultes or "Non renseignée"],
        ["Compétences", fiche.competences or "Non renseignée"],
        ["Est un animal", "Oui" if fiche.est_animal else "Non"],
        ["Recherche une personne", fiche.recherche_personne or "Non"],
        ["N° recherche", fiche.numero_recherche or "Non renseigné"],
        ["Évènement", fiche.evenement.nom]
    ]
    story.append(_styled_table(data_supp))

    doc.build(story)

    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="fiche_protection_civile.pdf", mimetype='application/pdf')


# === TABLE STYLING UTILITY ===
from reportlab.lib.units import mm
def _styled_table(data):
    table = Table(data, colWidths=[60*mm, 100*mm])
    table.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 11),
        ('BACKGROUND', (0,0), (-1,-1), colors.whitesmoke),
        ('ROWBACKGROUNDS', (0,0), (-1,-1), [colors.whitesmoke, colors.lightgrey]),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.black),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('INNERGRID', (0,0), (-1,-1), 0.3, colors.grey),
        ('BOX', (0,0), (-1,-1), 0.5, colors.grey),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
    ]))
    return table



################################################

@main_bp.route("/admin/evenements")
@login_required
def admin_evenements():
    user = get_current_user()

    if not user.is_admin and user.role != "codep":
        flash("⛔ Accès interdit.", "danger")
        return redirect(url_for("main_bp.evenement_new"))

    evenements = Evenement.query.order_by(Evenement.id.desc()).all()
    return render_template("admin_evenements.html", evenements=evenements, user=user)


####################################

@main_bp.route('/evenement/<int:evenement_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_evenement(evenement_id):
    user = get_current_user()
    evenement = Evenement.query.get_or_404(evenement_id)

    if not user.is_admin and user.role != "codep" and evenement.createur_id != user.id:
        flash("⛔ Accès interdit.", "danger")
        return redirect(url_for("main_bp.admin_evenements"))

    if request.method == "POST":
        evenement.nom = request.form["nom"]
        evenement.adresse = request.form["adresse"]
        evenement.type_evt = request.form["type"]
        evenement.statut = request.form["statut"]
        db.session.commit()
        flash("✅ Évènement mis à jour.", "success")
        return redirect(url_for("main_bp.admin_evenements"))

    return render_template("edit_evenement.html", evenement=evenement, user=user)

#########################################


@main_bp.route("/evenements/<int:evenement_id>/supprimer", methods=["POST"])
@login_required
def delete_evenement(evenement_id):
    user = get_current_user()  # ✅ au lieu de current_user
    evt = Evenement.query.get_or_404(evenement_id)

    # 🔐 Vérifie si l'utilisateur est admin OU le créateur (codep)
    if not user.is_admin and evt.createur_id != user.id:
        abort(403)

    # 🧹 Supprime les fiches impliquées
    FicheImplique.query.filter_by(evenement_id=evt.id).delete()

    # 🧹 Supprime les tickets (si tu en as)
    from .models import Ticket
    Ticket.query.filter_by(evenement_id=evt.id).delete()

    # 🗑 Supprime l'évènement
    db.session.delete(evt)
    db.session.commit()

    flash("✅ L’évènement et ses fiches ont été supprimés.", "success")
    return redirect(url_for("main_bp.evenement_new"))



###################################################



@main_bp.route("/evenement/<int:evenement_id>/export/pdf")
@login_required
def export_evenement_fiches_pdf(evenement_id):
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    import io
    import pytz

    evenement = Evenement.query.get_or_404(evenement_id)
    fiches = FicheImplique.query.filter_by(evenement_id=evenement_id).all()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=18)
    elements = []

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='CenterTitle', alignment=1, fontSize=18, spaceAfter=20))
    styles.add(ParagraphStyle(name='SubHeader', textColor=colors.orange, fontSize=14, spaceAfter=10))

    elements.append(Paragraph("Fiches Impliqués – Évènement", styles['CenterTitle']))
    elements.append(Paragraph("Informations sur l’évènement", styles['SubHeader']))

    # Date locale
    def convertir_heure_locale(dt_utc):
        if not dt_utc:
            return "Non renseignée"
        paris = pytz.timezone("Europe/Paris")
        return dt_utc.astimezone(paris).strftime("%d/%m/%Y %H:%M")

    infos_evt = [
        ["Nom", evenement.nom],
        ["Numéro", evenement.numero],
        ["Adresse", evenement.adresse],
        ["Statut", evenement.statut],
        ["Type", evenement.type_evt],
        ["Date d'ouverture", convertir_heure_locale(evenement.date_ouverture)]
    ]
    table_evt = Table(infos_evt, hAlign='LEFT', colWidths=[4*cm, 12*cm])
    table_evt.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
    ]))
    elements.append(table_evt)
    elements.append(Spacer(1, 20))

    elements.append(Paragraph("Liste des fiches impliquées", styles['SubHeader']))

    header = [
        "Nom", "Prénom", "Naissance", "Nationalité", "Statut",
        "Téléphone", "Adresse", "Compétences", "Destination", "Effets perso"
    ]
    data = [header]

    for f in fiches:
        row = [
            f.nom or "-",
            f.prenom or "-",
            f.date_naissance.strftime("%d/%m/%Y") if f.date_naissance else "-",
            f.nationalite or "-",
            f.statut or "-",
            f.telephone or "-",
            f.adresse or "-",
            f.competences or "-",
            f.destination or "-",
            f.effets_perso or "-",
        ]
        data.append(row)

    table_fiches = Table(data, repeatRows=1, hAlign='LEFT')
    table_fiches.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -1), 0.25, colors.grey)
    ]))
    elements.append(table_fiches)

    doc.build(elements)
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name=f"evenement_{evenement.numero}_fiches.pdf", mimetype='application/pdf')



###########################################



# ➕ ROUTE : ajout d’un ou plusieurs bagages sur une fiche
@main_bp.route("/fiche/<int:fiche_id>/bagages/ajouter", methods=["POST"])
@login_required
def fiche_bagages_ajouter(fiche_id):
    user = get_current_user()
    fiche = FicheImplique.query.get_or_404(fiche_id)

    # ✅ accès à l’évènement
    if fiche.evenement not in user.evenements and not user.is_admin and user.role != "codep":
        flash("⛔ Vous n’avez pas accès à cet évènement.", "danger")
        return redirect(url_for("main_bp.evenement_new"))

    # ✅ autorisations de l’action "bagage"
    role = (user.role or "").lower()
    if not (user.is_admin or role in {"bagages", "bagagerie", "responsable", "codep"}):
        flash("⛔ Vous n’êtes pas autorisé à ajouter des bagages.", "danger")
        return redirect(url_for("main_bp.dashboard", evenement_id=fiche.evenement_id))

    # 📥 récupération et parsing
    raw = (request.form.get("numeros") or "").strip()
    if not raw:
        flash("Veuillez saisir au moins un numéro de bagage.", "warning")
        return redirect(url_for("main_bp.dashboard", evenement_id=fiche.evenement_id))

    # split sur espaces / virgules / points-virgules / retours ligne
    tokens = [t.strip() for t in re.split(r"[\s,;]+", raw) if t.strip()]
    # dédoublonner en conservant l’ordre
    uniques, vus = [], set()
    for t in tokens:
        if t not in vus:
            uniques.append(t)
            vus.add(t)

    if not uniques:
        flash("Aucun numéro de bagage valide détecté.", "warning")
        return redirect(url_for("main_bp.dashboard", evenement_id=fiche.evenement_id))

    # 🔎 existence dans le centre (unicité par évènement)
    existants = {
        b.numero: b
        for b in Bagage.query.filter(
            Bagage.evenement_id == fiche.evenement_id,
            Bagage.numero.in_(uniques)
        ).all()
    }

    ajoutes, deja_sur_cette_fiche, deja_sur_autre_fiche = [], [], []
    for num in uniques:
        b = existants.get(num)
        if b:
            if b.fiche_id == fiche.id:
                deja_sur_cette_fiche.append(num)
            else:
                deja_sur_autre_fiche.append(num)
            continue

        # ✅ création
        nouveau = Bagage(numero=num, fiche_id=fiche.id, evenement_id=fiche.evenement_id)
        db.session.add(nouveau)
        ajoutes.append(num)

    db.session.commit()

    # 🗣️ feedback
    messages = []
    if ajoutes:
        messages.append(f"Ajouté: {', '.join(ajoutes)}")
    if deja_sur_cette_fiche:
        messages.append(f"Déjà sur cette fiche: {', '.join(deja_sur_cette_fiche)}")
    if deja_sur_autre_fiche:
        messages.append(f"Déjà utilisés par une autre fiche: {', '.join(deja_sur_autre_fiche)}")

    flash(" | ".join(messages) if messages else "Aucun bagage ajouté.", "success" if ajoutes else "info")
    return redirect(url_for("main_bp.dashboard", evenement_id=fiche.evenement_id))




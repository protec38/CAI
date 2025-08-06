from datetime import datetime
from . import db
from werkzeug.security import generate_password_hash, check_password_hash


class Utilisateur(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom_utilisateur = db.Column(db.String(50), unique=True, nullable=False)
    mot_de_passe = db.Column(db.String(200), nullable=False)
    nom = db.Column(db.String(50), nullable=False)
    prenom = db.Column(db.String(50), nullable=False)
    type_utilisateur = db.Column(db.String(20))  # 'interne' ou 'externe'
    niveau = db.Column(db.String(20))            # 'technicien' ou 'encadrant'
    role = db.Column(db.String(30))              # 'codep', 'responsable', 'entree_sortie', etc.

    def set_password(self, password):
        self.mot_de_passe = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.mot_de_passe, password)


class Evenement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)  # ex: 038250801
    nom = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    fiches = db.relationship("FicheImplique", backref="evenement", lazy=True)


class FicheImplique(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    numero_fiche = db.Column(db.String(16), unique=True, nullable=False)
    type = db.Column(db.String(10), nullable=False)  # humain / animal
    nom = db.Column(db.String(50))
    prenom = db.Column(db.String(50))
    date_naissance = db.Column(db.String(10))
    nationalite = db.Column(db.String(50))
    adresse = db.Column(db.String(150))
    telephone = db.Column(db.String(30))
    personne_a_prevenir = db.Column(db.String(50))
    telephone_a_prevenir = db.Column(db.String(30))
    recherche_personne = db.Column(db.String(300))
    difficulte = db.Column(db.String(300))
    competences = db.Column(db.String(300))
    date_entree = db.Column(db.DateTime, default=datetime.utcnow)
    date_sortie = db.Column(db.DateTime, nullable=True)
    sortie_destination = db.Column(db.String(150))
    sortie_transport = db.Column(db.String(100))
    cree_par_nom = db.Column(db.String(50))
    cree_par_prenom = db.Column(db.String(50))

    evenement_id = db.Column(db.Integer, db.ForeignKey("evenement.id"), nullable=False)

# app/models.py

from . import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class Evenement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(20), unique=True, nullable=False)
    nom = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(10), default="CAI")  # CAI / CHU / PRV
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    utilisateurs = db.relationship("Utilisateur", back_populates="evenement", cascade="all, delete")
    impliques = db.relationship("FicheImplique", back_populates="evenement", cascade="all, delete")

class Utilisateur(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom_utilisateur = db.Column(db.String(50), unique=True, nullable=False)
    mot_de_passe_hash = db.Column(db.String(128), nullable=False)
    type_utilisateur = db.Column(db.String(20), nullable=False)  # interne / externe
    niveau = db.Column(db.String(20))  # encadrant / technicien
    role = db.Column(db.String(30))    # codep / responsable / bagagerie / autorité / etc.
    nom = db.Column(db.String(100))
    prenom = db.Column(db.String(100))
    is_admin = db.Column(db.Boolean, default=False)
    actif = db.Column(db.Boolean, default=True)
    evenement_id = db.Column(db.Integer, db.ForeignKey('evenement.id'))
    evenement = db.relationship("Evenement", back_populates="utilisateurs")

    def set_password(self, mot_de_passe):
        self.mot_de_passe_hash = generate_password_hash(mot_de_passe)

    def check_password(self, mot_de_passe):
        return check_password_hash(self.mot_de_passe_hash, mot_de_passe)

class FicheImplique(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    numero_fiche = db.Column(db.String(20), unique=True, nullable=False)
    humain = db.Column(db.Boolean, default=True)
    nom = db.Column(db.String(50))
    prenom = db.Column(db.String(50))
    date_naissance = db.Column(db.Date)
    nationalite = db.Column(db.String(50))
    adresse = db.Column(db.String(150))
    telephone = db.Column(db.String(20))
    personne_a_prevenir = db.Column(db.String(50))
    tel_personne_a_prevenir = db.Column(db.String(20))
    recherche_personne = db.Column(db.String(300))
    difficulte = db.Column(db.String(300))
    competences = db.Column(db.String(300))
    effets_perso = db.Column(db.String(150))
    nom_createur = db.Column(db.String(100))
    prenom_createur = db.Column(db.String(100))
    date_entree = db.Column(db.DateTime, default=datetime.utcnow)
    date_sortie = db.Column(db.DateTime, nullable=True)
    destination = db.Column(db.String(100))
    moyen_transport = db.Column(db.String(100))
    createur_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    evenement_id = db.Column(db.Integer, db.ForeignKey('evenement.id'))

    evenement = db.relationship("Evenement", back_populates="impliques")

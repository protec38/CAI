from . import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from datetime import datetime, date

class Evenement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(10), unique=True)  # généré automatiquement
    nom = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(10), default="CAI")
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    utilisateurs = db.relationship("Utilisateur", back_populates="evenement", lazy=True)
    impliques = db.relationship("FicheImplique", back_populates="evenement", lazy=True)

class Utilisateur(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom_utilisateur = db.Column(db.String(50), unique=True, nullable=False)
    mot_de_passe_hash = db.Column(db.String(128), nullable=False)
    type_utilisateur = db.Column(db.String(20), nullable=False)
    niveau = db.Column(db.String(20))
    role = db.Column(db.String(30))
    nom = db.Column(db.String(100))
    prenom = db.Column(db.String(100))
    evenement_id = db.Column(db.Integer, db.ForeignKey('evenement.id'))
    evenement = db.relationship("Evenement", back_populates="utilisateurs")
    is_admin = db.Column(db.Boolean, default=False)
    actif = db.Column(db.Boolean, default=True)

    def set_password(self, mot_de_passe):
        self.mot_de_passe_hash = generate_password_hash(mot_de_passe)

    def check_password(self, mot_de_passe):
        return check_password_hash(self.mot_de_passe_hash, mot_de_passe)

class FicheImplique(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    numero_fiche = db.Column(db.String(10), nullable=False, unique=True)
    humain = db.Column(db.Boolean, default=True)
    nom = db.Column(db.String(50), nullable=False)
    prenom = db.Column(db.String(50))
    date_naissance = db.Column(db.Date)
    nationalite = db.Column(db.String(100))
    adresse = db.Column(db.String(150))
    telephone = db.Column(db.String(20))
    personne_a_prevenir = db.Column(db.String(50))
    tel_personne_a_prevenir = db.Column(db.String(20))
    recherche_personne = db.Column(db.String(300))
    difficulte = db.Column(db.String(300))
    competences = db.Column(db.String(300))
    effets_perso = db.Column(db.String(300))
    nom_createur = db.Column(db.String(50))
    prenom_createur = db.Column(db.String(50))
    date_entree = db.Column(db.DateTime, default=datetime.utcnow)
    date_sortie = db.Column(db.DateTime, nullable=True)
    destination = db.Column(db.String(100), nullable=True)
    moyen_transport = db.Column(db.String(100), nullable=True)
    
    # Clés étrangères
    createur_id = db.Column(db.Integer, db.ForeignKey("utilisateur.id"))
    evenement_id = db.Column(db.Integer, db.ForeignKey("evenement.id"))

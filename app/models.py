from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date

db = SQLAlchemy()

class Utilisateur(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom_utilisateur = db.Column(db.String(150), unique=True, nullable=False)
    mot_de_passe = db.Column(db.String(200), nullable=False)
    nom = db.Column(db.String(100))
    prenom = db.Column(db.String(100))
    role = db.Column(db.String(50))
    evenement_selectionne_id = db.Column(db.Integer, db.ForeignKey('evenement.id'))

    evenement_selectionne = db.relationship('Evenement', foreign_keys=[evenement_selectionne_id], post_update=True)

    def __repr__(self):
        return f"<Utilisateur {self.nom_utilisateur}>"

class Evenement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom_evt = db.Column(db.String(150), nullable=False)
    type_evt = db.Column(db.String(50))
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)

    utilisateurs_associes = db.relationship('Utilisateur', backref='evenement', lazy=True, foreign_keys=[Utilisateur.evenement_selectionne_id])
    fiches = db.relationship('FicheImplique', backref='evenement', lazy=True)

    def __repr__(self):
        return f"<Evenement {self.nom_evt}>"

class FicheImplique(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    numero_fiche = db.Column(db.String(10), nullable=False)
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
    effets_perso = db.Column(db.String(300))
    nom_createur = db.Column(db.String(100))
    prenom_createur = db.Column(db.String(100))
    date_entree = db.Column(db.DateTime, default=datetime.utcnow)
    date_sortie = db.Column(db.DateTime, nullable=True)
    destination = db.Column(db.String(150))
    moyen_transport = db.Column(db.String(100))
    
    createur_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    evenement_id = db.Column(db.Integer, db.ForeignKey('evenement.id'))

    def __repr__(self):
        return f"<FicheImplique {self.numero_fiche}>"

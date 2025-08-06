from .. import db
from datetime import datetime

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

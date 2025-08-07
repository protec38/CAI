from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# Association utilisateur <-> evenement (many-to-many)
utilisateur_evenement = db.Table(
    'utilisateur_evenement',
    db.Column('utilisateur_id', db.Integer, db.ForeignKey('utilisateur.id'), primary_key=True),
    db.Column('evenement_id', db.Integer, db.ForeignKey('evenement.id'), primary_key=True)
)

# Utilisateur
class Utilisateur(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom_utilisateur = db.Column(db.String(64), unique=True, nullable=False)
    mot_de_passe_hash = db.Column(db.String(128), nullable=False)

    nom = db.Column(db.String(100), nullable=True)
    prenom = db.Column(db.String(100), nullable=True)

    role = db.Column(db.String(50), nullable=False)  # Ex: entree, bagages, secouriste...
    type_utilisateur = db.Column(db.String(20), nullable=False)  # permanent / provisoire
    niveau = db.Column(db.String(20), nullable=True)  # encadrant / technicien (optionnel)
    fiches = db.relationship('FicheImplique', backref='createur', lazy=True)
    is_admin = db.Column(db.Boolean, default=False)
    actif = db.Column(db.Boolean, default=True)

    evenements = db.relationship(
        'Evenement',
        secondary=utilisateur_evenement,
        backref=db.backref('utilisateurs', lazy='dynamic')
    )

    def set_password(self, password):
        self.mot_de_passe_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.mot_de_passe_hash, password)

    def __repr__(self):
        return f'<Utilisateur {self.nom_utilisateur}>'

# Évènement
class Evenement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(50), unique=True, nullable=False)
    nom = db.Column(db.String(100), nullable=False)
    adresse = db.Column(db.String(200), nullable=True)
    statut = db.Column(db.String(50), nullable=True)
    type_evt = db.Column(db.String(50), nullable=True)
    date_ouverture = db.Column(db.DateTime, default=datetime.utcnow)

    # 🆕 Champ pour identifier le créateur/responsable
    createur_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'), nullable=True)
    createur = db.relationship('Utilisateur', backref='evenements_crees', foreign_keys=[createur_id])

    impliques = db.relationship('FicheImplique', backref='evenement', lazy=True)
    tickets = db.relationship('Ticket', backref='evenement', lazy=True)

    def __repr__(self):
        return f'<Evenement {self.nom}>'

# Fiche Impliqué
class FicheImplique(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(20), unique=True, nullable=False)
    nom = db.Column(db.String(50), nullable=False)
    prenom = db.Column(db.String(50), nullable=True)
    date_naissance = db.Column(db.Date, nullable=True)
    nationalite = db.Column(db.String(50), nullable=True)
    adresse = db.Column(db.String(150), nullable=True)
    telephone = db.Column(db.String(20), nullable=True)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'), nullable=False)
    statut = db.Column(db.String(20), nullable=False, default="présent")  # présent / sorti / supprimé
    heure_arrivee = db.Column(db.DateTime, default=datetime.utcnow)
    difficulte = db.Column(db.String(200), nullable=True)
    competence = db.Column(db.String(200), nullable=True)

    est_animal = db.Column(db.Boolean, default=False)
    recherche_personne = db.Column(db.String(300), nullable=True)
    numero_recherche = db.Column(db.String(20), nullable=True)

    evenement_id = db.Column(db.Integer, db.ForeignKey('evenement.id'), nullable=False)

    def __repr__(self):
        return f"<FicheImplique {self.nom} {self.prenom}>"

# Ticket logistique
class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(20), unique=True, nullable=False)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    emetteur = db.Column(db.String(100), nullable=False)
    destinataire = db.Column(db.String(100), nullable=True)
    nature = db.Column(db.String(200), nullable=True)
    degre_urgence = db.Column(db.String(20), nullable=True)

    statut = db.Column(db.String(20), nullable=False, default='nouveau')  # nouveau / pris en compte / clôturé / supprimé

    commentaire_prise_en_compte = db.Column(db.Text, nullable=True)
    date_prise_en_compte = db.Column(db.DateTime, nullable=True)

    commentaire_cloture = db.Column(db.Text, nullable=True)
    date_cloture = db.Column(db.DateTime, nullable=True)

    evenement_id = db.Column(db.Integer, db.ForeignKey('evenement.id'), nullable=False)

    def __repr__(self):
        return f"<Ticket {self.numero}>"

# Animal (lié à une fiche impliqué si nécessaire)
class Animal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    espece = db.Column(db.String(50), nullable=True)
    nom = db.Column(db.String(50), nullable=True)
    fiche_id = db.Column(db.Integer, db.ForeignKey('fiche_implique.id'), nullable=True)

    def __repr__(self):
        return f"<Animal {self.nom}>"

from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import pytz  # ✅ Pour conversion UTC → heure locale France
from flask_login import UserMixin
# 🌍 Fonction utilitaire
def convertir_heure_locale(dt_utc):
    if not dt_utc:
        return None
    paris = pytz.timezone("Europe/Paris")
    return dt_utc.astimezone(paris)

# Association utilisateur <-> evenement (many-to-many)
utilisateur_evenement = db.Table(
    'utilisateur_evenement',
    db.Column('utilisateur_id', db.Integer, db.ForeignKey('utilisateur.id'), primary_key=True),
    db.Column('evenement_id', db.Integer, db.ForeignKey('evenement.id'), primary_key=True)
)

# Utilisateur
class Utilisateur(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    nom_utilisateur = db.Column(db.String(64), unique=True, nullable=False)
    mot_de_passe_hash = db.Column(db.String(128), nullable=False)

    nom = db.Column(db.String(100), nullable=True)
    prenom = db.Column(db.String(100), nullable=True)

    role = db.Column(db.String(50), nullable=False)
    type_utilisateur = db.Column(db.String(20), nullable=False)
    niveau = db.Column(db.String(20), nullable=True)
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

    createur_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'), nullable=True)
    createur = db.relationship('Utilisateur', backref='evenements_crees', foreign_keys=[createur_id])

    impliques = db.relationship(
        'FicheImplique',
        backref='evenement',
        lazy=True,
        cascade="all, delete-orphan"
        )

    tickets = db.relationship(
        'Ticket',
        backref='evenement',
        lazy=True,
        cascade="all, delete-orphan"
    )


    def __repr__(self):
        return f'<Evenement {self.nom}>'


# Fiche Impliqué
class FicheImplique(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(20), unique=True, nullable=False)

    nom = db.Column(db.String(100))
    prenom = db.Column(db.String(100))
    date_naissance = db.Column(db.Date, nullable=True)
    nationalite = db.Column(db.String(50), nullable=True)
    adresse = db.Column(db.String(200), nullable=True)
    telephone = db.Column(db.String(20), nullable=True)

    personne_a_prevenir = db.Column(db.String(255))
    tel_personne_a_prevenir = db.Column(db.String(50))
    recherche_personne = db.Column(db.Text)

    difficultes = db.Column(db.Text)
    competences = db.Column(db.Text)

    effets_perso = db.Column(db.String(255))
    destination = db.Column(db.String(255))
    moyen_transport = db.Column(db.String(255))

    est_animal = db.Column(db.Boolean, default=False)
    humain = db.Column(db.Boolean, default=True)
    heure_sortie = db.Column(db.DateTime, nullable=True)
    numero_recherche = db.Column(db.String(20), nullable=True)

    statut = db.Column(db.String(20), nullable=False, default="présent")
    heure_arrivee = db.Column(db.DateTime, default=datetime.utcnow)

    evenement_id = db.Column(db.Integer, db.ForeignKey('evenement.id'), nullable=False)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'), nullable=False)

    # ✅ Propriétés heure locale
    @property
    def heure_arrivee_locale(self):
        return convertir_heure_locale(self.heure_arrivee)

    @property
    def heure_sortie_locale(self):
        return convertir_heure_locale(self.heure_sortie)

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

    statut = db.Column(db.String(20), nullable=False, default='nouveau')

    commentaire_prise_en_compte = db.Column(db.Text, nullable=True)
    date_prise_en_compte = db.Column(db.DateTime, nullable=True)

    commentaire_cloture = db.Column(db.Text, nullable=True)
    date_cloture = db.Column(db.DateTime, nullable=True)

    evenement_id = db.Column(db.Integer, db.ForeignKey('evenement.id'), nullable=False)

    def __repr__(self):
        return f"<Ticket {self.numero}>"


# Animal
class Animal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    espece = db.Column(db.String(50), nullable=True)
    nom = db.Column(db.String(50), nullable=True)
    fiche_id = db.Column(db.Integer, db.ForeignKey('fiche_implique.id'), nullable=True)

    def __repr__(self):
        return f"<Animal {self.nom}>"

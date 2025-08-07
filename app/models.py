from datetime import datetime
from app import db
from werkzeug.security import generate_password_hash, check_password_hash

# ✅ Table d'association Utilisateur <-> Evenement (many-to-many)
utilisateur_evenement = db.Table(
    'utilisateur_evenement',
    db.Column('utilisateur_id', db.Integer, db.ForeignKey('utilisateur.id'), primary_key=True),
    db.Column('evenement_id', db.Integer, db.ForeignKey('evenement.id'), primary_key=True)
)

# ✅ Modèle Utilisateur
class Utilisateur(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom_utilisateur = db.Column(db.String(64), unique=True, nullable=False)
    mot_de_passe_hash = db.Column(db.String(128), nullable=False)

    nom = db.Column(db.String(100), nullable=True)
    prenom = db.Column(db.String(100), nullable=True)

    role = db.Column(db.String(20), nullable=False)
    type_utilisateur = db.Column(db.String(20), nullable=False)  # ex: 'provisoire', 'permanent'
    niveau = db.Column(db.String(20), nullable=True)

    is_admin = db.Column(db.Boolean, default=False)
    actif = db.Column(db.Boolean, default=True)

    # ✅ Relation vers les évènements
    evenements = db.relationship(
        'Evenement',
        secondary=utilisateur_evenement,
        backref=db.backref('utilisateurs', lazy='dynamic')
    )

    def set_password(self, mot_de_passe):
        self.mot_de_passe_hash = generate_password_hash(mot_de_passe)

    def check_password(self, mot_de_passe):
        return check_password_hash(self.mot_de_passe_hash, mot_de_passe)

    def __repr__(self):
        return f"<Utilisateur {self.nom_utilisateur}>"

# ✅ Modèle Evenement (exemple minimal)
class Evenement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(50), unique=True, nullable=False)
    nom = db.Column(db.String(100), nullable=False)
    adresse = db.Column(db.String(200), nullable=True)
    statut = db.Column(db.String(50), nullable=True)
    type_evt = db.Column(db.String(50), nullable=True)

    def __repr__(self):
        return f"<Evenement {self.nom} ({self.numero})>"


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

from .. import db
from werkzeug.security import generate_password_hash, check_password_hash

class Utilisateur(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom_utilisateur = db.Column(db.String(50), unique=True, nullable=False)
    mot_de_passe_hash = db.Column(db.String(128), nullable=False)
    type_utilisateur = db.Column(db.String(20), nullable=False)  # 'interne' ou 'externe'
    niveau = db.Column(db.String(20))  # 'technicien' ou 'encadrant' (pour internes)
    role = db.Column(db.String(30), nullable=True)  # entrée/sortie, responsable, etc.
    nom = db.Column(db.String(100))
    prenom = db.Column(db.String(100))
    evenement_id = db.Column(db.Integer, db.ForeignKey('evenement.id'))
    evenement = db.relationship("Evenement", back_populates="utilisateurs")

    def set_password(self, mot_de_passe):
        self.mot_de_passe_hash = generate_password_hash(mot_de_passe)

    def check_password(self, mot_de_passe):
        return check_password_hash(self.mot_de_passe_hash, mot_de_passe)

    def is_admin(self):
        return self.role in ['responsable', 'codep']

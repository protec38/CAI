from .. import db
from datetime import datetime

class Evenement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(20), unique=True, nullable=False)
    nom = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(10), default="CAI")  # CAI ou PRV
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    utilisateurs = db.relationship("Utilisateur", back_populates="evenement")
    impliques = db.relationship("FicheImplique", back_populates="evenement")

    def generer_numero(self):
        now = datetime.utcnow()
        chrono = str(self.id).zfill(2)
        return f"038{now.strftime('%y%m')}{chrono}"

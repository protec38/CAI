from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from .models import db, Utilisateur  # on importe db depuis models.py
from .routes import main_bp

bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = "main_bp.login"

@login_manager.user_loader
def load_user(user_id):
    return Utilisateur.query.get(int(user_id))

def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "votre_cle_secrete"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///site.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)        # IMPORTANT : initialiser SQLAlchemy avec l’app
    bcrypt.init_app(app)
    login_manager.init_app(app)

    app.register_blueprint(main_bp)

    with app.app_context():
        db.create_all()     # Crée les tables si elles n'existent pas
        create_default_admin()  # Crée un utilisateur admin si nécessaire

    return app

def create_default_admin():
    if not Utilisateur.query.filter_by(nom_utilisateur="admin").first():
        admin = Utilisateur(
            nom="Administrateur",
            prenom="Général",
            nom_utilisateur="admin"
        )
        admin.set_mot_de_passe("admin")
        db.session.add(admin)
        db.session.commit()

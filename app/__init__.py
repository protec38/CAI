# app/__init__.py

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()

# Initialisation de l'extension
db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")

    # Initialiser les extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Importer les modèles et routes après l'init de db (évite les imports circulaires)
    from . import models
    from .routes import main_bp
    app.register_blueprint(main_bp)

    # Création de la base et admin par défaut
    with app.app_context():
        db.create_all()
        create_default_admin()

    return app

def create_default_admin():
    from .models import Utilisateur

    if not Utilisateur.query.filter_by(nom_utilisateur="admin").first():
        admin = Utilisateur(
            nom_utilisateur="admin",
            type_utilisateur="interne",
            niveau="encadrant",
            role="codep",  # ou "admin" selon ta logique
            nom="Administrateur",
            prenom="Général",
            is_admin=True
        )
        admin.set_password("admin")
        db.session.add(admin)
        db.session.commit()

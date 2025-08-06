from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from .models import Utilisateur
from werkzeug.security import generate_password_hash

# Initialisation extensions
db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")

    db.init_app(app)
    Migrate(app, db)

    from .routes import main_bp
    app.register_blueprint(main_bp)

    with app.app_context():
        db.create_all()
        create_default_admin()

    return app

def create_default_admin():
    if not Utilisateur.query.filter_by(nom_utilisateur="admin").first():
        admin = Utilisateur(
            nom_utilisateur="admin",
            type_utilisateur="interne",
            niveau="encadrant",
            role="admin",
            nom="Administrateur",
            prenom="Général",
            is_admin=True
        )
        admin.set_password("admin")
        db.session.add(admin)
        db.session.commit()

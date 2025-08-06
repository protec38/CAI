from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
migrate = Migrate()
bcrypt = Bcrypt()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'changeme'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.sqlite'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)

    from .routes import main_bp
    app.register_blueprint(main_bp)

    create_default_users(app)

    return app


def create_default_users(app):
    from .models import Utilisateur
    with app.app_context():
        db.create_all()  # 👉 Crée les tables si elles n'existent pas

        default_users = [
            ("codep", "codep", "encadrant", "codep"),
            ("responsable", "responsable", "encadrant", "responsable"),
            ("entree", "entree", "technicien", "entree_sortie"),
            ("sortie", "sortie", "technicien", "entree_sortie"),
            ("bagagiste", "bagagiste", "technicien", "bagagerie"),
            ("secouriste", "secouriste", "technicien", "secouriste"),
            ("autorite", "autorite", "technicien", "autorite")
        ]

        for username, nom, niveau, role in default_users:
            existing = Utilisateur.query.filter_by(nom_utilisateur=username).first()
            if not existing:
                user = Utilisateur(
                    nom_utilisateur=username,
                    nom=nom.capitalize(),
                    prenom="Test",
                    type_utilisateur="interne",
                    niveau=niveau,
                    role=role
                )
                user.set_password("azerty")
                db.session.add(user)
                print(f"✅ Utilisateur '{username}' créé avec mot de passe : azerty")
        db.session.commit()


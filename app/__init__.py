from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
bcrypt = Bcrypt()

def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")

    db.init_app(app)
    bcrypt.init_app(app)

    from .routes import main_bp
    app.register_blueprint(main_bp)

    # Créer les tables AVANT d'appeler create_default_admin
    with app.app_context():
        db.create_all()

        # Importer ici pour éviter les erreurs circulaires
        from .models import Utilisateur

        # Créer l'admin par défaut si pas encore présent
        if not Utilisateur.query.filter_by(nom_utilisateur="admin").first():
            from .models import Utilisateur
            admin = Utilisateur(
                nom_utilisateur="admin",
                nom="Administrateur",
                prenom="Général",
                role="admin",
                mot_de_passe=bcrypt.generate_password_hash("admin").decode("utf-8")
            )
            db.session.add(admin)
            db.session.commit()

    return app

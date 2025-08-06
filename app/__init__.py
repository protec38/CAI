from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")

    db.init_app(app)
    Migrate(app, db)

    from .routes import main_bp
    app.register_blueprint(main_bp)

    # On importe ici pour éviter les circular imports
    with app.app_context():
        from .models import Utilisateur
        db.create_all()
        if Utilisateur.query.first() is None:
            user = Utilisateur(
                nom_utilisateur="admin",
                type_utilisateur="interne",
                niveau="encadrant",
                role="responsable",
                nom="Durand",
                prenom="Jean"
            )
            user.set_password("admin123")
            db.session.add(user)
            db.session.commit()
            print("✅ Utilisateur par défaut créé : admin / admin123")

    return app

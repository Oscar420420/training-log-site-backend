"""
Training Log Backend (Flask)
----------------------------
What this gives you vs the static version:
- Real accounts (coach + lifter)
- Comments saved to a database (shared across devices)
- High-quality media uploads from phone (stored on server disk)
- Add/remove periods/blocks/weeks/days/exercises from the web UI

Deployment note:
- GitHub Pages cannot host backends.
- Use Render/Fly.io/Railway/etc. (guide in README).
"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"

def create_app():
    app = Flask(__name__, instance_relative_config=True)

    # --- Config --------------------------------------------------------------
    app.config["SECRET_KEY"] = app.config.get("SECRET_KEY") or "dev-change-me"

    # Database: default to sqlite in instance folder for local dev
    app.config["SQLALCHEMY_DATABASE_URI"] = app.config.get("SQLALCHEMY_DATABASE_URI") or "sqlite:///traininglog.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Uploads
    import os
    max_mb = int(os.environ.get("MAX_UPLOAD_MB", "500"))
    app.config["MAX_CONTENT_LENGTH"] = max_mb * 1024 * 1024
    app.config["UPLOAD_FOLDER"] = os.path.join(app.instance_path, "uploads")
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # Init extensions
    db.init_app(app)
    login_manager.init_app(app)

    # Register blueprints
    from .routes import main_bp
    from .auth import auth_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)

    # Create tables + optionally bootstrap users
    with app.app_context():
        from . import models
        db.create_all()
        models.bootstrap_users_if_configured()

    return app

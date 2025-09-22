import os
from flask import Flask
from focusflow.extensions import db, migrate, mail, login_manager, csrf, scheduler, start_scheduler
from focusflow.routes import main
import firebase_admin
from firebase_admin import credentials

def create_app(config_class=None):
    app = Flask(__name__)

    if config_class is None:
        from focusflow.config import Config
        config_class = Config
    app.config.from_object(config_class)

    os.makedirs(app.instance_path, exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)

    login_manager.init_app(app)
    login_manager.login_view = 'main.login'  # redirect non-auth users here
    login_manager.login_message_category = 'info'

    csrf.init_app(app)
    scheduler.init_app(app)

    # Register blueprint
    app.register_blueprint(main)

    # Initialize Firebase Admin SDK if configured
    firebase_cred_file = os.getenv('FIREBASE_SERVICE_ACCOUNT_FILE')
    if firebase_cred_file and not firebase_admin._apps:
        cred = credentials.Certificate(firebase_cred_file)
        firebase_admin.initialize_app(cred)

    # Start scheduler
    start_scheduler(app)

    return app

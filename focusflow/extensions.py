from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail
from flask_login import LoginManager
from flask_wtf import CSRFProtect
from flask_apscheduler import APScheduler
import atexit
import logging
from sqlalchemy import MetaData


# Naming convention dictionary for constraints
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

# Create metaData with naming convention
metadata = MetaData(naming_convention=convention)

# Pass the metadata with naming convention to SQLAlchemy
db = SQLAlchemy(metadata=metadata)
migrate = Migrate()
mail = Mail()
login_manager = LoginManager()
csrf = CSRFProtect()
scheduler = APScheduler()
logger = logging.getLogger(__name__)

def start_scheduler(app):
    try:
        if not scheduler.running:
            scheduler.init_app(app)
            scheduler.start()
            logger.info("Scheduler started")
            atexit.register(shutdown_scheduler)
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}")

def shutdown_scheduler():
    try:
        if scheduler.running:
            scheduler.shutdown()
            logger.info("Scheduler shut down")
    except Exception as e:
        logger.error(f"Error shutting down scheduler: {e}")

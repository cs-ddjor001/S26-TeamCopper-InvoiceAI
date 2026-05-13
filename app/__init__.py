import os
from datetime import date, datetime

from flask import Flask

from .config import Config
from .extensions import db


def create_app(config_class=Config):
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    app = Flask(
        __name__,
        template_folder=os.path.join(project_root, "templates"),
        static_folder=os.path.join(project_root, "static"),
    )
    app.config.from_object(config_class)

    db.init_app(app)

    def format_datetime(value, fmt="%m/%d/%Y"):
        if value is None:
            return ""
        if isinstance(value, datetime):
            return value.strftime(fmt)
        if isinstance(value, date):
            return datetime.combine(value, datetime.min.time()).strftime(fmt)
        if isinstance(value, str):
            for parse_fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
                try:
                    return datetime.strptime(value, parse_fmt).strftime(fmt)
                except ValueError:
                    continue
        return str(value)

    app.jinja_env.filters["format_datetime"] = format_datetime

    from .routes.auth import auth_bp
    from .routes.ap import ap_bp
    from .routes.dashboard import dashboard_bp
    from .routes.model_trainer import model_trainer_bp
    from .routes.invoice import invoice_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(ap_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(model_trainer_bp)
    app.register_blueprint(invoice_bp)

    return app

import os

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Config:
    PROJECT_ROOT = _project_root
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(_project_root, 'app.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = "invoiceai-dev-key"

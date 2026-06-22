import os


BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "ganti-secret-key-di-production")
    DB_PATH = os.environ.get(
        "DB_PATH", os.path.join(BASE_DIR, "database", "database.db")
    )
    UPLOAD_FOLDER = os.environ.get(
        "UPLOAD_FOLDER", os.path.join(BASE_DIR, "static", "uploads")
    )
    LOGO_FOLDER = os.environ.get(
        "LOGO_FOLDER", os.path.join(BASE_DIR, "static", "logo")
    )
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB

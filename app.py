import os
from flask import Flask, redirect, url_for
from flask_login import LoginManager, current_user

# Pastikan file config.py ada
from config import Config
from utils.db import close_db, init_db, query_one, execute
from utils.security import hash_password
from utils.user import AppUser

def ensure_database(app):
    db_path = app.config["DB_PATH"]
    # Memastikan folder database ada
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)

    if not os.path.exists(db_path):
        with app.app_context():
            init_db()

    # Seed admin default
    with app.app_context():
        row = query_one("SELECT id FROM admins LIMIT 1")
        if not row:
            execute(
                "INSERT INTO admins (nama, username, password) VALUES (?, ?, ?)",
                ("Admin Madrasah", "admin", hash_password("admin123")),
            )

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Pastikan folder upload ada
    os.makedirs(app.config.get("UPLOAD_FOLDER", "uploads"), exist_ok=True)
    os.makedirs(app.config.get("LOGO_FOLDER", "static/logo"), exist_ok=True)

    ensure_database(app)
    app.teardown_appcontext(close_db)

    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id: str):
        return AppUser.from_login_id(user_id)

    @app.context_processor
    def inject_profile():
        prof = query_one("SELECT * FROM profil_madrasah WHERE id = 1")
        return {"profil_madrasah": prof}

    @app.route("/")
    def index():
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))
        if getattr(current_user, "role", None) == "admin":
            return redirect(url_for("admin.dashboard"))
        return redirect(url_for("guru.dashboard"))

    # Blueprints
    from blueprints.auth.routes import bp as auth_bp
    from blueprints.admin.routes import bp as admin_bp
    from blueprints.guru.routes import bp as guru_bp
    from blueprints.laporan.routes import bp as laporan_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(guru_bp, url_prefix="/guru")
    app.register_blueprint(laporan_bp, url_prefix="/laporan")

    return app

# Variabel 'app' inilah yang akan dibaca oleh file api/index.py
app = create_app()

if __name__ == "__main__":
    # Hanya jalan saat di laptop/lokal
    app.run(debug=True)
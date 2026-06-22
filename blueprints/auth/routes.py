from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user

from utils.db import query_one
from utils.security import verify_password
from utils.user import AppUser


bp = Blueprint("auth", __name__, template_folder="../../templates")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        if getattr(current_user, "role", None) == "admin":
            return redirect(url_for("admin.dashboard"))
        return redirect(url_for("guru.dashboard"))

    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""

        if not username or not password:
            flash("Username dan password wajib diisi.", "danger")
            return render_template("auth/login.html")

        admin = query_one("SELECT * FROM admins WHERE username = ?", (username,))
        if admin and verify_password(admin["password"], password):
            login_user(
                AppUser(
                    user_id=admin["id"],
                    role="admin",
                    nama=admin["nama"],
                    username=admin["username"],
                )
            )
            return redirect(url_for("admin.dashboard"))

        guru = query_one("SELECT * FROM guru WHERE username = ?", (username,))
        if guru and verify_password(guru["password"], password):
            login_user(
                AppUser(
                    user_id=guru["id"],
                    role="guru",
                    nama=guru["nama"],
                    username=guru["username"],
                )
            )
            return redirect(url_for("guru.dashboard"))

        flash("Login gagal. Periksa kembali username/password.", "danger")

    return render_template("auth/login.html")


@bp.route("/logout")
def logout():
    logout_user()
    flash("Anda telah logout.", "info")
    return redirect(url_for("auth.login"))

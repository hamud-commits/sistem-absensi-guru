import os
from datetime import date, datetime

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user

from utils.decorators import role_required
from utils.db import query_one, query_all, execute
from utils.helpers import today_str, minutes_late, allowed_image, unique_filename
from utils.security import hash_password


bp = Blueprint("guru", __name__, template_folder="../../templates")

STATUS_OPTIONS = ["Hadir", "Izin", "Sakit", "Alpha", "Dinas Luar"]


def _save_upload(file_storage, subfolder="uploads"):
    if not file_storage or not file_storage.filename:
        return None
    if not allowed_image(file_storage.filename):
        return None
    filename = unique_filename(file_storage.filename)
    dest_dir = os.path.join(current_app.static_folder, subfolder)
    os.makedirs(dest_dir, exist_ok=True)
    file_storage.save(os.path.join(dest_dir, filename))
    return f"{subfolder}/{filename}"


@bp.route("/dashboard")
@login_required
@role_required("guru")
def dashboard():
    guru_id = current_user.user_id
    ym = date.today().strftime("%Y-%m")
    stats = query_one(
        """
        SELECT
          SUM(CASE WHEN status='Hadir' THEN 1 ELSE 0 END) AS hadir,
          SUM(CASE WHEN status='Izin' THEN 1 ELSE 0 END) AS izin,
          SUM(CASE WHEN status='Sakit' THEN 1 ELSE 0 END) AS sakit,
          SUM(CASE WHEN status='Alpha' THEN 1 ELSE 0 END) AS alpha,
          SUM(CASE WHEN status='Dinas Luar' THEN 1 ELSE 0 END) AS dinas_luar,
          COUNT(*) AS total
        FROM absensi
        WHERE guru_id = ? AND substr(tanggal,1,7) = ?
        """,
        (guru_id, ym),
    )
    hadir = int(stats["hadir"] or 0)
    total = int(stats["total"] or 0)
    persen = (hadir / total * 100) if total else 0
    return render_template(
        "guru/dashboard.html",
        ym=ym,
        hadir=hadir,
        izin=int(stats["izin"] or 0),
        sakit=int(stats["sakit"] or 0),
        alpha=int(stats["alpha"] or 0),
        dinas_luar=int(stats["dinas_luar"] or 0),
        persen=round(persen, 2),
        total=total,
    )


@bp.route("/absensi", methods=["GET", "POST"])
@login_required
@role_required("guru")
def absensi_saya():
    guru_id = current_user.user_id
    today = today_str()
    row = query_one(
        "SELECT * FROM absensi WHERE guru_id=? AND tanggal=?",
        (guru_id, today),
    )

    if request.method == "POST":
        action = request.form.get("action")
        now = datetime.now().strftime("%H:%M")

        if action == "checkin":
            if row:
                flash("Anda sudah melakukan absensi hari ini.", "warning")
                return redirect(url_for("guru.absensi_saya"))

            status = request.form.get("status") or "Hadir"
            keterangan = request.form.get("keterangan") or None

            jam_masuk = now if status == "Hadir" else None
            terlambat = minutes_late(jam_masuk, "07:00") if status == "Hadir" else 0
            execute(
                """
                INSERT INTO absensi (guru_id, tanggal, jam_masuk, status, terlambat, keterangan, validated)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (guru_id, today, jam_masuk, status, terlambat, keterangan, 0),
            )
            flash("Check-in berhasil.", "success")
            return redirect(url_for("guru.absensi_saya"))

        if action == "checkout":
            if not row:
                flash("Silakan check-in terlebih dahulu.", "warning")
                return redirect(url_for("guru.absensi_saya"))
            if row["jam_pulang"]:
                flash("Anda sudah check-out.", "info")
                return redirect(url_for("guru.absensi_saya"))
            execute(
                "UPDATE absensi SET jam_pulang=? WHERE id=?",
                (now, row["id"]),
            )
            flash("Check-out berhasil.", "success")
            return redirect(url_for("guru.absensi_saya"))

    row = query_one(
        "SELECT * FROM absensi WHERE guru_id=? AND tanggal=?",
        (guru_id, today),
    )
    return render_template(
        "guru/absensi_saya.html",
        row=row,
        today=today,
        status_options=STATUS_OPTIONS,
    )


@bp.route("/riwayat")
@login_required
@role_required("guru")
def riwayat():
    guru_id = current_user.user_id
    start = request.args.get("start") or ""
    end = request.args.get("end") or ""
    where = ["guru_id=?"]
    params = [guru_id]
    if start:
        where.append("tanggal >= ?")
        params.append(start)
    if end:
        where.append("tanggal <= ?")
        params.append(end)
    rows = query_all(
        f"SELECT * FROM absensi WHERE {' AND '.join(where)} ORDER BY tanggal DESC",
        tuple(params),
    )
    return render_template("guru/riwayat.html", rows=rows, start=start, end=end)


@bp.route("/profil", methods=["GET", "POST"])
@login_required
@role_required("guru")
def profil():
    guru_id = current_user.user_id
    row = query_one("SELECT * FROM guru WHERE id=?", (guru_id,))
    if request.method == "POST":
        no_hp = request.form.get("no_hp") or row["no_hp"]
        email = request.form.get("email") or row["email"]
        password = request.form.get("password") or ""
        foto_path = row["foto"]

        new_foto = _save_upload(request.files.get("foto"), "uploads")
        if new_foto:
            foto_path = new_foto

        pwd_hash = row["password"]
        if password.strip():
            pwd_hash = hash_password(password)

        try:
            execute(
                "UPDATE guru SET no_hp=?, email=?, foto=?, password=? WHERE id=?",
                (no_hp, email, foto_path, pwd_hash, guru_id),
            )
            flash("Profil berhasil diperbarui.", "success")
            return redirect(url_for("guru.profil"))
        except Exception as e:
            flash(f"Gagal memperbarui profil: {e}", "danger")

    return render_template("guru/profil.html", row=row)

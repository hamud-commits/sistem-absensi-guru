import os
from datetime import date, datetime, timedelta

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app,
    send_file,
    jsonify,
)
from flask_login import login_required, current_user

from utils.decorators import role_required
from utils.db import query_one, query_all, execute
from utils.helpers import allowed_image, unique_filename, today_str
from utils.security import hash_password


bp = Blueprint("admin", __name__, template_folder="../../templates")


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
@role_required("admin")
def dashboard():
    today = today_str()
    total_guru = query_one("SELECT COUNT(*) AS c FROM guru")["c"]
    stats_today = query_one(
        """
        SELECT
          SUM(CASE WHEN status='Hadir' THEN 1 ELSE 0 END) AS hadir,
          SUM(CASE WHEN status='Izin' THEN 1 ELSE 0 END) AS izin,
          SUM(CASE WHEN status='Sakit' THEN 1 ELSE 0 END) AS sakit,
          SUM(CASE WHEN status='Alpha' THEN 1 ELSE 0 END) AS alpha,
          SUM(CASE WHEN status='Dinas Luar' THEN 1 ELSE 0 END) AS dinas_luar
        FROM absensi
        WHERE tanggal = ?
        """,
        (today,),
    )
    hadir = int(stats_today["hadir"] or 0)
    persen = (hadir / total_guru * 100) if total_guru else 0

    return render_template(
        "admin/dashboard.html",
        total_guru=total_guru,
        today=today,
        hadir=hadir,
        izin=int(stats_today["izin"] or 0),
        sakit=int(stats_today["sakit"] or 0),
        alpha=int(stats_today["alpha"] or 0),
        dinas_luar=int(stats_today["dinas_luar"] or 0),
        persen=round(persen, 2),
    )


@bp.route("/api/chart/bulanan")
@login_required
@role_required("admin")
def api_chart_bulanan():
    year = request.args.get("year") or str(date.today().year)
    rows = query_all(
        """
        SELECT substr(tanggal,1,7) AS ym,
               SUM(CASE WHEN status='Hadir' THEN 1 ELSE 0 END) AS hadir
        FROM absensi
        WHERE substr(tanggal,1,4) = ?
        GROUP BY ym
        ORDER BY ym
        """,
        (year,),
    )
    labels = [r["ym"] for r in rows]
    data = [int(r["hadir"] or 0) for r in rows]
    return jsonify({"labels": labels, "data": data})


@bp.route("/api/chart/status-hari-ini")
@login_required
@role_required("admin")
def api_chart_status_hari_ini():
    today = today_str()
    rows = query_all(
        """
        SELECT status, COUNT(*) AS c
        FROM absensi
        WHERE tanggal = ?
        GROUP BY status
        """,
        (today,),
    )
    labels = [r["status"] for r in rows]
    data = [int(r["c"] or 0) for r in rows]
    return jsonify({"labels": labels, "data": data})


@bp.route("/api/chart/tahunan")
@login_required
@role_required("admin")
def api_chart_tahunan():
    rows = query_all(
        """
        SELECT substr(tanggal,1,4) AS y,
               COUNT(*) AS total,
               SUM(CASE WHEN status='Hadir' THEN 1 ELSE 0 END) AS hadir
        FROM absensi
        GROUP BY y
        ORDER BY y
        """
    )
    labels = [r["y"] for r in rows]
    data = [int(r["hadir"] or 0) for r in rows]
    return jsonify({"labels": labels, "data": data})


# -----------------------------
# CRUD GURU
# -----------------------------


@bp.route("/guru")
@login_required
@role_required("admin")
def guru_list():
    rows = query_all("SELECT * FROM guru ORDER BY nama ASC")
    return render_template("admin/guru_list.html", rows=rows)


@bp.route("/guru/tambah", methods=["GET", "POST"])
@login_required
@role_required("admin")
def guru_add():
    if request.method == "POST":
        form = request.form
        foto_path = _save_upload(request.files.get("foto"), "uploads")
        password = form.get("password") or "guru123"

        try:
            execute(
                """
                INSERT INTO guru (
                  nip, nama, jenis_kelamin, tempat_lahir, tanggal_lahir, pendidikan,
                  jabatan, mata_pelajaran, no_hp, email, alamat, status_kepegawaian,
                  foto, username, password
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    form.get("nip"),
                    form.get("nama"),
                    form.get("jenis_kelamin"),
                    form.get("tempat_lahir"),
                    form.get("tanggal_lahir"),
                    form.get("pendidikan"),
                    form.get("jabatan"),
                    form.get("mata_pelajaran"),
                    form.get("no_hp"),
                    form.get("email"),
                    form.get("alamat"),
                    form.get("status_kepegawaian"),
                    foto_path,
                    form.get("username"),
                    hash_password(password),
                ),
            )
        except Exception as e:
            flash(f"Gagal menambah guru: {e}", "danger")
            return render_template("admin/guru_form.html", mode="add")

        flash("Data guru berhasil ditambahkan.", "success")
        return redirect(url_for("admin.guru_list"))

    return render_template("admin/guru_form.html", mode="add")


@bp.route("/guru/<int:guru_id>")
@login_required
@role_required("admin")
def guru_detail(guru_id: int):
    row = query_one("SELECT * FROM guru WHERE id = ?", (guru_id,))
    if not row:
        flash("Guru tidak ditemukan.", "warning")
        return redirect(url_for("admin.guru_list"))
    return render_template("admin/guru_detail.html", row=row)


@bp.route("/guru/<int:guru_id>/edit", methods=["GET", "POST"])
@login_required
@role_required("admin")
def guru_edit(guru_id: int):
    row = query_one("SELECT * FROM guru WHERE id = ?", (guru_id,))
    if not row:
        flash("Guru tidak ditemukan.", "warning")
        return redirect(url_for("admin.guru_list"))

    if request.method == "POST":
        form = request.form
        foto_path = row["foto"]
        new_foto = _save_upload(request.files.get("foto"), "uploads")
        if new_foto:
            foto_path = new_foto

        pwd = form.get("password") or ""
        if pwd.strip():
            pwd_hash = hash_password(pwd)
        else:
            pwd_hash = row["password"]

        try:
            execute(
                """
                UPDATE guru SET
                  nip=?, nama=?, jenis_kelamin=?, tempat_lahir=?, tanggal_lahir=?, pendidikan=?,
                  jabatan=?, mata_pelajaran=?, no_hp=?, email=?, alamat=?, status_kepegawaian=?,
                  foto=?, username=?, password=?
                WHERE id=?
                """,
                (
                    form.get("nip"),
                    form.get("nama"),
                    form.get("jenis_kelamin"),
                    form.get("tempat_lahir"),
                    form.get("tanggal_lahir"),
                    form.get("pendidikan"),
                    form.get("jabatan"),
                    form.get("mata_pelajaran"),
                    form.get("no_hp"),
                    form.get("email"),
                    form.get("alamat"),
                    form.get("status_kepegawaian"),
                    foto_path,
                    form.get("username"),
                    pwd_hash,
                    guru_id,
                ),
            )
        except Exception as e:
            flash(f"Gagal mengedit guru: {e}", "danger")
            return render_template("admin/guru_form.html", mode="edit", row=row)

        flash("Data guru berhasil diperbarui.", "success")
        return redirect(url_for("admin.guru_detail", guru_id=guru_id))

    return render_template("admin/guru_form.html", mode="edit", row=row)


@bp.route("/guru/<int:guru_id>/hapus", methods=["POST"])
@login_required
@role_required("admin")
def guru_delete(guru_id: int):
    execute("DELETE FROM guru WHERE id = ?", (guru_id,))
    flash("Data guru berhasil dihapus.", "success")
    return redirect(url_for("admin.guru_list"))


# -----------------------------
# MANAJEMEN ABSENSI
# -----------------------------


@bp.route("/absensi")
@login_required
@role_required("admin")
def absensi_list():
    start = request.args.get("start") or ""
    end = request.args.get("end") or ""
    where = []
    params = []
    if start:
        where.append("a.tanggal >= ?")
        params.append(start)
    if end:
        where.append("a.tanggal <= ?")
        params.append(end)
    wh = ("WHERE " + " AND ".join(where)) if where else ""
    rows = query_all(
        f"""
        SELECT a.*, g.nama, g.nip
        FROM absensi a
        JOIN guru g ON g.id = a.guru_id
        {wh}
        ORDER BY a.tanggal DESC, g.nama ASC
        """,
        tuple(params),
    )
    return render_template("admin/absensi_list.html", rows=rows, start=start, end=end)


@bp.route("/absensi/tambah", methods=["GET", "POST"])
@login_required
@role_required("admin")
def absensi_add():
    gurus = query_all("SELECT id, nama, nip FROM guru ORDER BY nama ASC")
    if request.method == "POST":
        form = request.form
        guru_id = int(form.get("guru_id"))
        tanggal = form.get("tanggal") or today_str()
        jam_masuk = form.get("jam_masuk") or None
        jam_pulang = form.get("jam_pulang") or None
        status = form.get("status") or "Hadir"
        keterangan = form.get("keterangan") or None

        terlambat = 0
        if status == "Hadir" and jam_masuk:
            masuk_dt = datetime.strptime(jam_masuk, "%H:%M").time()
            normal = datetime.strptime("07:00", "%H:%M").time()
            delta = (
                datetime.combine(date.today(), masuk_dt)
                - datetime.combine(date.today(), normal)
            )
            terlambat = max(int(delta.total_seconds() // 60), 0)

        try:
            execute(
                """
                INSERT INTO absensi (guru_id, tanggal, jam_masuk, jam_pulang, status, terlambat, keterangan, validated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    guru_id,
                    tanggal,
                    jam_masuk,
                    jam_pulang,
                    status,
                    terlambat,
                    keterangan,
                    1,
                ),
            )
        except Exception as e:
            flash(f"Gagal menambah absensi: {e}", "danger")
            return render_template("admin/absensi_form.html", mode="add", gurus=gurus)

        flash("Absensi berhasil ditambahkan.", "success")
        return redirect(url_for("admin.absensi_list"))

    return render_template("admin/absensi_form.html", mode="add", gurus=gurus)


@bp.route("/absensi/<int:absensi_id>/edit", methods=["GET", "POST"])
@login_required
@role_required("admin")
def absensi_edit(absensi_id: int):
    row = query_one(
        """
        SELECT a.*, g.nama, g.nip
        FROM absensi a JOIN guru g ON g.id=a.guru_id
        WHERE a.id=?
        """,
        (absensi_id,),
    )
    if not row:
        flash("Data absensi tidak ditemukan.", "warning")
        return redirect(url_for("admin.absensi_list"))

    if request.method == "POST":
        form = request.form
        jam_masuk = form.get("jam_masuk") or None
        status = form.get("status") or row["status"]
        terlambat = row["terlambat"] or 0
        if status == "Hadir" and jam_masuk:
            masuk_dt = datetime.strptime(jam_masuk, "%H:%M").time()
            normal = datetime.strptime("07:00", "%H:%M").time()
            delta = (
                datetime.combine(date.today(), masuk_dt)
                - datetime.combine(date.today(), normal)
            )
            terlambat = max(int(delta.total_seconds() // 60), 0)
        else:
            terlambat = 0

        execute(
            """
            UPDATE absensi SET tanggal=?, jam_masuk=?, jam_pulang=?, status=?, terlambat=?, keterangan=?, validated=?
            WHERE id=?
            """,
            (
                form.get("tanggal"),
                jam_masuk,
                form.get("jam_pulang") or None,
                status,
                terlambat,
                form.get("keterangan") or None,
                1 if form.get("validated") == "1" else 0,
                absensi_id,
            ),
        )
        flash("Absensi berhasil diperbarui.", "success")
        return redirect(url_for("admin.absensi_list"))

    return render_template("admin/absensi_form.html", mode="edit", row=row)


@bp.route("/absensi/<int:absensi_id>/hapus", methods=["POST"])
@login_required
@role_required("admin")
def absensi_delete(absensi_id: int):
    execute("DELETE FROM absensi WHERE id = ?", (absensi_id,))
    flash("Absensi berhasil dihapus.", "success")
    return redirect(url_for("admin.absensi_list"))


@bp.route("/absensi/<int:absensi_id>/validasi", methods=["POST"])
@login_required
@role_required("admin")
def absensi_validasi(absensi_id: int):
    execute("UPDATE absensi SET validated = 1 WHERE id = ?", (absensi_id,))
    flash("Absensi berhasil divalidasi.", "success")
    return redirect(url_for("admin.absensi_list"))


# -----------------------------
# REKAPITULASI (berbasis rentang)
# -----------------------------


@bp.route("/rekap")
@login_required
@role_required("admin")
def rekap():
    mode = request.args.get("mode") or "harian"
    today = date.today()

    # default range
    start = request.args.get("start")
    end = request.args.get("end")
    if not start or not end:
        if mode == "harian":
            start = end = today.isoformat()
        elif mode == "mingguan":
            start_dt = today - timedelta(days=today.weekday())
            end_dt = start_dt + timedelta(days=6)
            start, end = start_dt.isoformat(), end_dt.isoformat()
        elif mode == "bulanan":
            start = today.replace(day=1).isoformat()
            end = today.isoformat()
        elif mode == "tahunan":
            start = today.replace(month=1, day=1).isoformat()
            end = today.isoformat()
        else:  # semester
            start = today.replace(month=1, day=1).isoformat()
            end = today.isoformat()

    rows = query_all(
        """
        SELECT a.*, g.nama, g.nip
        FROM absensi a JOIN guru g ON g.id=a.guru_id
        WHERE a.tanggal BETWEEN ? AND ?
        ORDER BY a.tanggal DESC, g.nama ASC
        """,
        (start, end),
    )
    return render_template(
        "admin/rekap.html",
        rows=rows,
        mode=mode,
        start=start,
        end=end,
    )


# -----------------------------
# PENGATURAN
# -----------------------------


@bp.route("/pengaturan", methods=["GET", "POST"])
@login_required
@role_required("admin")
def pengaturan():
    prof = query_one("SELECT * FROM profil_madrasah WHERE id=1")
    if request.method == "POST":
        form = request.form
        logo_madrasah = prof["logo_madrasah"]
        logo_kemenag = prof["logo_kemenag"]
        ttd_kepala = prof["ttd_kepala"]

        new_logo1 = _save_upload(request.files.get("logo_madrasah"), "logo")
        new_logo2 = _save_upload(request.files.get("logo_kemenag"), "logo")
        new_ttd = _save_upload(request.files.get("ttd_kepala"), "logo")
        if new_logo1:
            logo_madrasah = new_logo1
        if new_logo2:
            logo_kemenag = new_logo2
        if new_ttd:
            ttd_kepala = new_ttd

        execute(
            """
            UPDATE profil_madrasah SET
              nama_madrasah=?, nsm=?, npsn=?, alamat=?, telepon=?, email=?,
              kepala_madrasah=?, logo_madrasah=?, logo_kemenag=?, ttd_kepala=?,
              tahun_ajaran=?, semester_aktif=?, updated_at=datetime('now')
            WHERE id=1
            """,
            (
                form.get("nama_madrasah"),
                form.get("nsm"),
                form.get("npsn"),
                form.get("alamat"),
                form.get("telepon"),
                form.get("email"),
                form.get("kepala_madrasah"),
                logo_madrasah,
                logo_kemenag,
                ttd_kepala,
                form.get("tahun_ajaran"),
                form.get("semester_aktif"),
            ),
        )
        flash("Pengaturan berhasil disimpan.", "success")
        return redirect(url_for("admin.pengaturan"))

    return render_template("admin/pengaturan.html", prof=prof)


@bp.route("/admin", methods=["GET", "POST"])
@login_required
@role_required("admin")
def admin_profile():
    row = query_one("SELECT * FROM admins WHERE id = ?", (current_user.user_id,))
    if request.method == "POST":
        nama = request.form.get("nama") or row["nama"]
        username = request.form.get("username") or row["username"]
        password = request.form.get("password") or ""
        pwd_hash = row["password"]
        if password.strip():
            pwd_hash = hash_password(password)
        try:
            execute(
                "UPDATE admins SET nama=?, username=?, password=? WHERE id=?",
                (nama, username, pwd_hash, row["id"]),
            )
            flash("Profil admin berhasil diperbarui.", "success")
            return redirect(url_for("admin.admin_profile"))
        except Exception as e:
            flash(f"Gagal menyimpan profil admin: {e}", "danger")
    return render_template("admin/admin_profile.html", row=row)

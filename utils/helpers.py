import os
import uuid
from datetime import datetime, date, time


def allowed_image(filename: str) -> bool:
    ext = os.path.splitext(filename.lower())[1]
    return ext in {".png", ".jpg", ".jpeg", ".webp", ".gif"}


def unique_filename(original: str) -> str:
    ext = os.path.splitext(original)[1].lower()
    return f"{uuid.uuid4().hex}{ext}"


def today_str() -> str:
    return date.today().isoformat()


def parse_time_hhmm(value: str) -> time | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%H:%M").time()
    except Exception:
        return None


def minutes_late(jam_masuk: str | None, jam_normal: str = "07:00") -> int:
    if not jam_masuk:
        return 0
    try:
        masuk = datetime.strptime(jam_masuk, "%H:%M").time()
        normal = datetime.strptime(jam_normal, "%H:%M").time()
        masuk_dt = datetime.combine(date.today(), masuk)
        normal_dt = datetime.combine(date.today(), normal)
        delta = int((masuk_dt - normal_dt).total_seconds() // 60)
        return max(delta, 0)
    except Exception:
        return 0


def month_label(dt: date) -> str:
    return dt.strftime("%Y-%m")


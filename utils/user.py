from dataclasses import dataclass
from flask_login import UserMixin

from utils.db import query_one


@dataclass
class AppUser(UserMixin):
    user_id: int
    role: str  # "admin" | "guru"
    nama: str
    username: str

    @property
    def id(self) -> str:  # Flask-Login uses this
        return f"{self.role}:{self.user_id}"

    @staticmethod
    def from_login_id(login_id: str):
        """
        login_id format: '<role>:<id>'
        """
        if not login_id or ":" not in login_id:
            return None
        role, raw_id = login_id.split(":", 1)
        try:
            user_id = int(raw_id)
        except Exception:
            return None

        if role == "admin":
            row = query_one(
                "SELECT id, nama, username FROM admins WHERE id = ?",
                (user_id,),
            )
            if not row:
                return None
            return AppUser(
                user_id=row["id"],
                role="admin",
                nama=row["nama"],
                username=row["username"],
            )

        if role == "guru":
            row = query_one(
                "SELECT id, nama, username FROM guru WHERE id = ?",
                (user_id,),
            )
            if not row:
                return None
            return AppUser(
                user_id=row["id"],
                role="guru",
                nama=row["nama"],
                username=row["username"],
            )

        return None


from functools import wraps
from flask import abort
from flask_login import current_user


def role_required(*roles: str):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if getattr(current_user, "role", None) not in roles:
                abort(403)
            return fn(*args, **kwargs)

        return wrapper

    return decorator


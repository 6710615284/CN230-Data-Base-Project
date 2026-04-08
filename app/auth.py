from functools import wraps

from flask import redirect, session, url_for


def role_required(*allowed_roles):
    """Require the current session role to be one of the allowed roles."""

    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if session.get("role") not in allowed_roles:
                return redirect(url_for("auth.login"))
            return view(*args, **kwargs)

        return wrapped

    return decorator

import hashlib
import hmac
from datetime import timedelta
from functools import wraps

from flask import abort, current_app, request
from flask_login import current_user, login_required
from sqlalchemy import delete, func, select

from app.models import LoginAttempt, db, utcnow


def role_required(role):
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapped(*args, **kwargs):
            if current_user.role != role:
                abort(403)
            return view(*args, **kwargs)

        return wrapped

    return decorator


def attempt_keys(identifier):
    secret = current_app.secret_key.encode()

    def digest(value):
        return hmac.new(secret, value.encode(), hashlib.sha256).hexdigest()

    return digest("account:" + identifier), digest(
        "ip:" + (request.remote_addr or "unknown")
    )


def login_limited(identifier):
    account_key, ip_key = attempt_keys(identifier)
    since = utcnow() - timedelta(minutes=15)
    db.session.execute(delete(LoginAttempt).where(LoginAttempt.created_at < since))
    account_count = db.session.scalar(
        select(func.count())
        .select_from(LoginAttempt)
        .where(LoginAttempt.account_key == account_key)
    )
    ip_count = db.session.scalar(
        select(func.count())
        .select_from(LoginAttempt)
        .where(LoginAttempt.ip_key == ip_key)
    )
    db.session.commit()
    return (
        account_count >= current_app.config["LOGIN_ACCOUNT_LIMIT"]
        or ip_count >= current_app.config["LOGIN_IP_LIMIT"]
    )


def record_failure(identifier):
    account_key, ip_key = attempt_keys(identifier)
    db.session.add(LoginAttempt(account_key=account_key, ip_key=ip_key))
    db.session.commit()

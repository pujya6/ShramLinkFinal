import re
import uuid

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash

from app import validation
from app.models import User, UserRole, db
from app.security import login_limited, record_failure

auth_bp = Blueprint("auth", __name__)


def sign_in(user):
    session.clear()
    login_user(user, remember=False, fresh=True)
    session.permanent = True


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))
    errors = {}
    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip().lower()[:120]
        password = request.form.get("password", "")
        if login_limited(identifier):
            abort(429)
        user = User.query.filter(
            or_(User.phone == identifier, User.email == identifier)
        ).first()
        candidate = (
            user.password_hash
            if user and user.password_hash
            else current_app.config["DUMMY_PASSWORD_HASH"]
        )
        valid_password = check_password_hash(candidate, password[:128])
        if (
            not user
            or not valid_password
            or len(password) > 128
            or not user.is_active
            or user.credential_version < 2
        ):
            record_failure(identifier)
            errors["login"] = (
                "मोबाइल / ईमेल या पासवर्ड सही नहीं है / Incorrect login details."
            )
        else:
            sign_in(user)
            return redirect(url_for("dashboard.index"))
    return render_template("login.html", errors=errors, values=request.form), (
        400 if errors else 200
    )


@auth_bp.route("/register/laborer", methods=["GET", "POST"])
def register_laborer():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))
    errors = {}
    if request.method == "POST":
        phone = validation.phone_number(request.form, errors)
        password = validation.password(request.form, errors)
        if not errors:
            if login_limited("register:" + phone):
                abort(429)
            record_failure(
                "register:" + phone
            )  # Bound account creation per IP as well.
            user = User(
                phone=phone,
                email=uuid.uuid4().hex + "@accounts.invalid",
                role=UserRole.LABORER,
                name="नया श्रमिक",
                is_verified=False,
                profile_complete=False,
                credential_version=2,
            )
            user.set_password(password)
            db.session.add(user)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                errors["phone"] = (
                    "इस नंबर से खाता नहीं बन सका। पहले खाता बनाया हो तो लॉग इन करें / Try logging in if already registered."
                )
            else:
                sign_in(user)
                return redirect(url_for("dashboard.onboarding"))
    return render_template(
        "register_laborer.html", errors=errors, values=request.form
    ), (400 if errors else 200)


@auth_bp.route("/register/manager", methods=["GET", "POST"])
def register_manager():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))
    errors = {}
    if request.method == "POST":
        email = validation.text(request.form, "email", 120, errors).lower()
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email) or email.endswith(
            "@accounts.invalid"
        ):
            errors["email"] = "Enter a valid work email address."
        password = validation.password(request.form, errors)
        name = validation.text(request.form, "name", 100, errors, minimum=2)
        factory_name = validation.text(
            request.form, "factory_name", 200, errors, minimum=2
        )
        address = validation.text(
            request.form, "factory_address", 200, errors, minimum=5
        )
        if not errors:
            if login_limited("register:" + email):
                abort(429)
            record_failure("register:" + email)
            user = User(
                email=email,
                name=name,
                role=UserRole.MANAGER,
                factory_name=factory_name,
                factory_address=address,
                is_verified=False,
                credential_version=2,
            )
            user.set_password(password)
            db.session.add(user)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                errors["email"] = (
                    "Could not register this email. Log in if you already have an account."
                )
            else:
                sign_in(user)
                flash(
                    "Factory account created. Details are self-reported; you can now post a vacancy.",
                    "success",
                )
                return redirect(url_for("dashboard.manager_dashboard"))
    return render_template(
        "register_manager.html", errors=errors, values=request.form
    ), (400 if errors else 200)


@auth_bp.route("/admin-login")
def admin_login():
    return redirect(url_for("auth.login"))


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    session.clear()
    return redirect(url_for("main.index"))

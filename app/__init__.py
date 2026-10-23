import os
import secrets
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, render_template, request, url_for
from flask_wtf.csrf import CSRFError, CSRFProtect
from werkzeug.exceptions import HTTPException
from werkzeug.security import generate_password_hash
from sqlalchemy.exc import SQLAlchemyError

from app.catalog import (
    DOMAINS,
    LOCATIONS,
    SKILLS,
    STATUS_LABELS,
    EMPLOYMENT_CATEGORIES,
    CATEGORY_LABELS,
    WAGE_UNITS,
)
from app.experience import experience_label
from app.models import db, login_manager
from app.timeutils import india_date, localdate

BASE_DIR = Path(__file__).resolve().parent.parent
csrf = CSRFProtect()


def create_app(test_config=None):
    load_dotenv(BASE_DIR / ".env", override=False)
    app = Flask(
        __name__,
        template_folder=str(BASE_DIR / "templates"),
        static_folder=str(BASE_DIR / "static"),
        instance_path=str(BASE_DIR / "instance"),
    )
    production = os.getenv("SHRAMLINK_ENV") == "production"
    app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY") or None,
        SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL")
        or "sqlite:///" + str(BASE_DIR / "instance" / "shramlink.sqlite3"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SQLALCHEMY_ENGINE_OPTIONS={"hide_parameters": True},
        SESSION_COOKIE_NAME="shramlink_session_v2",
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SECURE=production,
        SESSION_COOKIE_SAMESITE="Lax",
        PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
        MAX_CONTENT_LENGTH=64 * 1024,
        WTF_CSRF_TIME_LIMIT=8 * 60 * 60,
        LOGIN_ACCOUNT_LIMIT=8,
        LOGIN_IP_LIMIT=30,
    )
    from app.settings import defaults, configure

    app.config.update(defaults())
    if test_config:
        app.config.update(test_config)
    configure(app)
    if production and (
        not app.config["SECRET_KEY"] or len(app.config["SECRET_KEY"]) < 32
    ):
        raise RuntimeError(
            "Production requires a fresh SECRET_KEY of at least 32 characters."
        )
    if (
        production
        and not os.getenv("DATABASE_URL")
        and not (test_config and "SQLALCHEMY_DATABASE_URI" in test_config)
    ):
        raise RuntimeError(
            "Production requires an explicit DATABASE_URL on persistent storage."
        )
    if production and os.getenv("DATABASE_URL") in ("sqlite://", "sqlite:///:memory:"):
        raise RuntimeError("Production cannot use an in-memory database.")
    Path(app.instance_path).mkdir(mode=0o700, parents=True, exist_ok=True)
    if not app.config["SECRET_KEY"]:
        key_file = Path(app.instance_path) / ".session-key"
        try:
            fd = os.open(key_file, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, "w") as stream:
                stream.write(secrets.token_hex(32))
        except FileExistsError:
            pass
        app.config["SECRET_KEY"] = key_file.read_text().strip()
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    app.jinja_env.filters["india_date"] = india_date
    app.jinja_env.filters["experience"] = experience_label
    app.config["DUMMY_PASSWORD_HASH"] = generate_password_hash(
        secrets.token_urlsafe(32)
    )

    from app.commands import register_commands
    from app.routes.admin import admin_bp
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.main import main_bp

    for blueprint in (main_bp, auth_bp, dashboard_bp, admin_bp):
        app.register_blueprint(blueprint)
    register_commands(app)

    @app.context_processor
    def context():
        return dict(
            skills=SKILLS,
            domains=DOMAINS,
            locations=LOCATIONS,
            status_labels=STATUS_LABELS,
            employment_categories=EMPLOYMENT_CATEGORIES,
            category_labels=CATEGORY_LABELS,
            wage_units=WAGE_UNITS,
            today=localdate().isoformat(),
        )

    @login_manager.unauthorized_handler
    def unauthorized():
        if request.path.startswith("/api/"):
            return jsonify(
                error="कृपया फिर लॉग इन करें / Please log in.", success=False
            ), 401
        return redirect(url_for("auth.login"))

    @app.errorhandler(CSRFError)
    def csrf_error(error):
        message = "सत्र की सुरक्षा जाँच असफल। पेज फिर खोलकर कोशिश करें / Session expired. Reload the page and try again."
        if request.path.startswith("/api/"):
            return jsonify(error=message, success=False), 400
        return render_template("error.html", code=400, message=message), 400

    @app.errorhandler(HTTPException)
    def http_error(error):
        messages = {
            400: "अनुरोध सही नहीं है / Invalid request.",
            403: "इस कार्य की अनुमति नहीं है / You cannot access this action.",
            404: "यह पेज या रिकॉर्ड नहीं मिला / Page or record not found.",
            405: "इस तरह अनुरोध नहीं भेज सकते / Method not allowed.",
            413: "जानकारी बहुत बड़ी है / Request is too large.",
            429: "कुछ देर बाद फिर कोशिश करें / Too many attempts. Try again in 15 minutes.",
        }
        message = messages.get(
            error.code, "अनुरोध पूरा नहीं हुआ / Request could not be completed."
        )
        if request.path.startswith("/api/"):
            return jsonify(error=message, success=False), error.code
        return render_template(
            "error.html", code=error.code, message=message
        ), error.code

    @app.errorhandler(500)
    def server_error(error):
        db.session.rollback()
        message = "अभी सेव नहीं हो पाया। फिर कोशिश करें / Could not complete the request. Please try again."
        if request.path.startswith("/api/"):
            return jsonify(error=message, success=False), 500
        return render_template("error.html", code=500, message=message), 500

    @app.errorhandler(SQLAlchemyError)
    def database_error(error):
        db.session.rollback()
        # Do not include SQL, bind parameters, profiles or connection URLs in logs.
        app.logger.error("Database unavailable; request was not completed.")
        message = "सेवा अभी उपलब्ध नहीं है। फिर कोशिश करें / Service temporarily unavailable. Please retry."
        if request.path.startswith("/api/"):
            return jsonify(error=message, success=False), 503
        # Standalone template avoids another user/session lookup into the failed DB.
        return render_template("service_unavailable.html", message=message), 503

    @app.after_request
    def headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["Permissions-Policy"] = (
            "microphone=(self), camera=(), geolocation=()"
        )
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'"
        )
        if request.endpoint != "static":
            response.headers["Cache-Control"] = "no-store"
        if production:
            response.headers["Strict-Transport-Security"] = "max-age=31536000"
        return response

    return app

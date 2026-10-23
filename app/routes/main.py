from flask import Blueprint, jsonify, redirect, render_template, url_for
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from app.models import db

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    return render_template("index.html")


@main_bp.route("/inside")
def inside():
    from app.showcase import (
        BASE_SHA,
        BRANCH,
        RELEASE_EVIDENCE,
        REPOSITORY,
        synthetic_matches,
    )

    return render_template(
        "inside.html",
        repository=REPOSITORY,
        source_root=f"{REPOSITORY}/blob/{BRANCH}",
        base_sha=BASE_SHA,
        evidence=RELEASE_EVIDENCE,
        examples=synthetic_matches(),
    )


@main_bp.route("/about")
def about():
    return redirect(url_for("main.index", _anchor="how"))


@main_bp.route("/laborer")
def laborer_standalone():
    # Keep the old entry URL, but require the real account/dashboard flow.
    return redirect(url_for("dashboard.laborer_dashboard"))


@main_bp.route("/healthz")
def health():
    try:
        # Also checks that explicit migration/setup has been run.
        db.session.execute(text("SELECT id FROM users LIMIT 1"))
        return jsonify(status="ok", application="ShramLink")
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify(status="unavailable"), 503

"""Read-only operational overview. Verification and payment actions are deferred."""

from flask import Blueprint, current_app, jsonify, render_template

from app.models import Job, JobApplication, User, UserRole, ServiceMetric
from app.security import role_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/")
@role_required(UserRole.ADMIN)
def index():
    return render_template(
        "admin/index.html",
        users=User.query.count(),
        jobs=Job.query.count(),
        applications=JobApplication.query.count(),
    )


@admin_bp.route("/service-status")
@role_required(UserRole.ADMIN)
def service_status():
    c = current_app.config
    counters = {r.key: r.count for r in ServiceMetric.query.all()}
    estimate = None
    if c["XAI_INPUT_USD_PER_MILLION"] and c["XAI_OUTPUT_USD_PER_MILLION"]:
        estimate = (
            counters.get("voice_input_tokens", 0) * c["XAI_INPUT_USD_PER_MILLION"]
            + counters.get("voice_output_tokens", 0) * c["XAI_OUTPUT_USD_PER_MILLION"]
        ) / 1_000_000
    return jsonify(
        configuration=c["CONFIGURATION_LABEL"],
        requested_configuration=c["REQUESTED_CONFIGURATION_LABEL"],
        counters=counters,
        estimated_usd=estimate,
        estimate_note="Only reported token usage at configured prices; not a billing guarantee. Failed/time-out requests may still cost money.",
    )

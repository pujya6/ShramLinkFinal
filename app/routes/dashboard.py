from flask import (
    Blueprint,
    abort,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required

from app import recruitment, validation, external_jobs
from app.catalog import LOCATIONS, SKILLS
from app.models import (
    ApplicationStatus,
    Job,
    JobApplication,
    UserRole,
    DemoPreparation,
    db,
)
from app.security import role_required

dashboard_bp = Blueprint("dashboard", __name__)
worker_only = role_required(UserRole.LABORER)
manager_only = role_required(UserRole.MANAGER)


def json_data():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        abort(400)
    return data


def positive_id(data, key):
    errors = {}
    value = validation.integer(data, key, 1, 2147483647, errors)
    if errors:
        abort(400)
    return value


@dashboard_bp.errorhandler(recruitment.RecruitmentError)
def recruitment_error(error):
    if request.path.startswith("/api/"):
        return jsonify(success=False, error=error.message), error.status
    return render_template(
        "error.html", code=error.status, message=error.message
    ), error.status


@dashboard_bp.route("/dashboard")
@login_required
def index():
    if current_user.role == UserRole.LABORER:
        endpoint = (
            "dashboard.laborer_dashboard"
            if current_user.profile_complete
            else "dashboard.onboarding"
        )
    elif current_user.role == UserRole.MANAGER:
        endpoint = "dashboard.manager_dashboard"
    else:
        endpoint = "admin.index"
    return redirect(url_for(endpoint))


def profile_values():
    return dict(
        name=current_user.name if current_user.profile_complete else "",
        age=current_user.age or "",
        skills=current_user.get_skills_list(),
        preferred_domain=current_user.preferred_domain or "",
        location=current_user.location or "",
        experience_years=current_user.experience_years
        if current_user.experience_years is not None
        else "",
        experience_months=current_user.total_experience_months
        if current_user.total_experience_months is not None
        else "",
        eshram_number=current_user.eshram_number or "",
    )


def save_profile(data):
    clean, errors = validation.profile(data)
    if not errors:
        current_user.set_skills_list(clean.pop("skills"))
        for field, value in clean.items():
            setattr(current_user, field, value)
        current_user.profile_complete = True
        # No credential is verified by entry, speech recognition or matching.
        current_user.is_verified = False
        current_user.kyc_status = "pending"
        db.session.commit()
    return errors


@dashboard_bp.route("/onboarding", methods=["GET", "POST"])
@worker_only
def onboarding():
    errors = {}
    values = profile_values()
    if request.method == "POST":
        errors = save_profile(request.form)
        if not errors:
            flash("प्रोफ़ाइल सेव हो गई / Profile saved. अब काम खोजें।", "success")
            return redirect(url_for("dashboard.laborer_dashboard"))
        values = request.form.to_dict()
        values["skills"] = request.form.getlist("skills")
    return render_template("onboarding.html", errors=errors, values=values), (
        400 if errors else 200
    )


@dashboard_bp.route("/api/laborer/profile", methods=["GET", "POST"])
@worker_only
def api_profile():
    if request.method == "POST":
        errors = save_profile(json_data())
        if errors:
            return jsonify(
                success=False, errors=errors, error="जानकारी जाँचें / Review the fields."
            ), 400
    return jsonify(
        success=True,
        profile=profile_values(),
        complete=current_user.profile_complete,
        information_source="self_reported",
        verified_credentials=[],
    )


def filters():
    skill = request.args.get("skill", "")
    location = request.args.get("location", "")
    if skill and skill not in SKILLS or location and location not in LOCATIONS:
        abort(400)
    return skill, location


@dashboard_bp.route("/dashboard/laborer")
@worker_only
def laborer_dashboard():
    if not current_user.profile_complete:
        return redirect(url_for("dashboard.onboarding"))
    skill, location = filters()
    rows = recruitment.discover(current_user, skill, location)
    applications = (
        JobApplication.query.filter_by(laborer_id=current_user.id)
        .order_by(JobApplication.applied_at.desc())
        .all()
    )
    return render_template(
        "dashboard/laborer.html",
        rows=rows,
        applications=applications,
        preparations=DemoPreparation.query.filter_by(laborer_id=current_user.id)
        .order_by(DemoPreparation.prepared_at.desc())
        .all(),
        preparation_status=external_jobs.PREPARED_STATUS,
        filter_skill=skill,
        filter_location=location,
    )


@dashboard_bp.route("/api/laborer/jobs")
@worker_only
def api_laborer_jobs():
    skill, location = filters()
    return jsonify(
        jobs=[
            dict(**recruitment.job_dict(job), match=match, applied=applied)
            for job, match, applied in recruitment.discover(
                current_user, skill, location
            )
        ]
    )


@dashboard_bp.route("/discover")
@worker_only
def discovery():
    if not current_user.profile_complete:
        return redirect(url_for("dashboard.onboarding"))
    skill, location = filters()
    from app.discovery_state import state

    all_rows = recruitment.discover(current_user)
    all_external, feed_message = external_jobs.available_cards(
        current_user, include_prepared=True
    )
    selected_rows = [
        r
        for r in all_rows
        if (not skill or r[0].skill.value == skill)
        and (not location or r[0].location == location)
    ]
    selected_external = [
        r
        for r in all_external
        if (not skill or r.get("skill") == skill)
        and (not location or r.get("location") == location)
    ]
    discovery_state = state(
        selected_rows,
        selected_external,
        all_rows,
        all_external,
        bool(skill or location),
    )
    rows = [r for r in selected_rows if not r[2]]
    external_cards = [r for r in selected_external if not r["prepared"]]
    return render_template(
        "discovery.html",
        rows=rows,
        jobs=[dict(**recruitment.job_dict(job), match=match) for job, match, _ in rows]
        + external_cards,
        external_cards=external_cards,
        feed_message=feed_message,
        discovery_state=discovery_state,
        filter_skill=skill,
        filter_location=location,
    )


@dashboard_bp.route("/jobs/<int:job_id>/apply", methods=["POST"])
@worker_only
def apply_job(job_id):
    recruitment.apply(current_user, job_id)
    flash("आवेदन भेज दिया / Application submitted.", "success")
    return redirect(url_for("dashboard.laborer_dashboard", _anchor="applications"))


@dashboard_bp.route("/api/laborer/apply", methods=["POST"])
@worker_only
def api_laborer_apply():
    application = recruitment.apply(current_user, positive_id(json_data(), "job_id"))
    return jsonify(
        success=True, application_id=application.id, status=application.status.value
    )


@dashboard_bp.route("/api/laborer/my-jobs")
@worker_only
def api_laborer_my_jobs():
    return jsonify(
        applications=[
            dict(id=a.id, status=a.status.value, job=recruitment.job_dict(a.job))
            for a in JobApplication.query.filter_by(
                laborer_id=current_user.id
            ).order_by(JobApplication.applied_at.desc())
        ]
    )


@dashboard_bp.route("/dashboard/manager")
@manager_only
def manager_dashboard():
    jobs = (
        Job.query.filter_by(manager_id=current_user.id)
        .order_by(Job.created_at.desc())
        .all()
    )
    return render_template(
        "dashboard/manager.html",
        jobs=jobs,
        application_count=sum(j.applications.count() for j in jobs),
    )


@dashboard_bp.route("/jobs/new", methods=["GET", "POST"])
@manager_only
def new_job():
    errors = {}
    if request.method == "POST":
        job, errors = recruitment.create_vacancy(current_user, request.form)
        if not errors:
            flash("Vacancy published. Workers can now apply.", "success")
            return redirect(url_for("dashboard.applicants", job_id=job.id))
    return render_template("job_form.html", errors=errors, values=request.form), (
        400 if errors else 200
    )


@dashboard_bp.route("/api/manager/post-job", methods=["POST"])
@manager_only
def api_manager_post_job():
    job, errors = recruitment.create_vacancy(current_user, json_data())
    if errors:
        return jsonify(
            success=False, errors=errors, error="Please review the vacancy fields."
        ), 400
    return jsonify(success=True, job=recruitment.job_dict(job)), 201


def owned_job(job_id):
    job = Job.query.filter_by(id=job_id, manager_id=current_user.id).first()
    if not job:
        abort(404)
    return job


def filtered_applicants(job):
    status = request.args.get("status", "")
    if status and status not in [s.value for s in ApplicationStatus]:
        abort(400)
    query = job.applications
    if status:
        query = query.filter(JobApplication.status == ApplicationStatus(status))
    return query.order_by(JobApplication.applied_at.asc()).all(), status


@dashboard_bp.route("/jobs/<int:job_id>/applicants")
@manager_only
def applicants(job_id):
    job = owned_job(job_id)
    rows, status = filtered_applicants(job)
    return render_template(
        "applicants.html", job=job, applications=rows, filter_status=status
    )


@dashboard_bp.route("/applications/<int:application_id>/decision", methods=["POST"])
@manager_only
def decision(application_id):
    application = recruitment.decide(
        current_user, application_id, request.form.get("action")
    )
    flash(
        "Decision saved. The worker can see the updated status in their account.",
        "success",
    )
    return redirect(url_for("dashboard.applicants", job_id=application.job_id))


@dashboard_bp.route("/api/manager/hire", methods=["POST"])
@manager_only
def api_manager_hire():
    data = json_data()
    application_id = positive_id(data, "application_id")
    application = recruitment.decide(current_user, application_id, data.get("action"))
    return jsonify(
        success=True, application_id=application.id, status=application.status.value
    )


@dashboard_bp.route("/api/manager/workers")
@manager_only
def api_manager_workers():
    job = owned_job(positive_id(request.args, "job_id"))
    rows, status = filtered_applicants(job)
    return jsonify(
        job=recruitment.job_dict(job),
        applicants=[
            dict(
                id=a.id,
                name=a.laborer.name,
                age=a.laborer.age,
                skills=a.laborer.get_skills_list(),
                location=a.laborer.location,
                preferred_domain=a.laborer.preferred_domain,
                experience_years=a.laborer.experience_years,
                experience_months=a.laborer.total_experience_months,
                eshram_provided=bool(a.laborer.eshram_number),
                information_source="self_reported",
                status=a.status.value,
                demo=a.laborer.demo_account,
            )
            for a in rows
        ],
    )


@dashboard_bp.route("/api/manager/dashboard")
@manager_only
def api_manager_dashboard():
    return jsonify(
        jobs=[
            recruitment.job_dict(j)
            for j in Job.query.filter_by(manager_id=current_user.id).order_by(
                Job.created_at.desc()
            )
        ]
    )


@dashboard_bp.route("/external/<int:vacancy_id>/preview", methods=["GET", "POST"])
@worker_only
def external_preview(vacancy_id):
    vacancy = external_jobs.vacancy_for_preview(current_user, vacancy_id)
    if request.method == "POST":
        external_jobs.prepare(current_user, vacancy_id, request.form)
        flash(external_jobs.PREPARED_STATUS + ". " + external_jobs.NOTICE_HI, "success")
        return redirect(url_for("dashboard.laborer_dashboard", _anchor="preparations"))
    return render_template(
        "external_preview.html", preview=external_jobs.preview(current_user, vacancy)
    )


@dashboard_bp.route("/api/laborer/external/<int:vacancy_id>/preview")
@worker_only
def api_external_preview(vacancy_id):
    vacancy = external_jobs.vacancy_for_preview(current_user, vacancy_id)
    return jsonify(external_jobs.preview(current_user, vacancy))


@dashboard_bp.route("/api/laborer/external/<int:vacancy_id>/prepare", methods=["POST"])
@worker_only
def api_external_prepare(vacancy_id):
    record = external_jobs.prepare(current_user, vacancy_id, json_data())
    return jsonify(
        success=True,
        preparation_id=record.id,
        status="demo_prepared",
        status_label=external_jobs.PREPARED_STATUS,
    )


@dashboard_bp.route("/api/laborer/interpret", methods=["POST"])
@worker_only
def api_interpret():
    from app.interpretation import interpret

    return jsonify(interpret(current_user, json_data()))

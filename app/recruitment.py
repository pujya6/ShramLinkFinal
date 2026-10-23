"""Shared recruitment operations for HTML forms and the retained API routes."""

from uuid import uuid4

from sqlalchemy import case, literal, update
from sqlalchemy.exc import IntegrityError

from app import validation
from app.experience import experience_label
from app.catalog import CATEGORY_LABELS
from app.job_speech import job_summary
from app.models import (
    ApplicationStatus,
    Job,
    JobApplication,
    JobStatus,
    SkillType,
    User,
    db,
    utcnow,
)
from app.timeutils import localdate


class RecruitmentError(Exception):
    def __init__(self, message, status=400):
        self.message, self.status = message, status


def create_vacancy(manager, data):
    clean, errors = validation.vacancy(data)
    if errors:
        return None, errors
    job = Job(
        **clean,
        job_code="JB-" + uuid4().hex[:12].upper(),
        manager_id=manager.id,
        status=JobStatus.ACTIVE,
        workers_hired=0,
        verified_only=False,
    )
    job.skill = SkillType(clean["skill"])
    db.session.add(job)
    db.session.commit()
    return job, {}


def matching(job, worker):
    reasons, unmet, score = [], [], 0
    if job.skill.value in worker.get_skills_list():
        reasons.append("कौशल मिलता है / Skill matches (+50)")
        score += 50
    else:
        unmet.append("यह कौशल प्रोफ़ाइल में नहीं है / Required skill missing")
    if job.location == worker.location:
        reasons.append("पसंद का शहर / Preferred city (+30)")
        score += 30
    if job.domain and job.domain == worker.preferred_domain:
        reasons.append("पसंद का क्षेत्र / Preferred domain (+15)")
        score += 15
    if (
        worker.total_experience_months is not None
        and worker.total_experience_months >= job.required_experience_months
    ):
        reasons.append("अनुभव की शर्त पूरी / Experience meets requirement (+5)")
        score += 5
    else:
        unmet.append("अनुभव की शर्त पूरी नहीं / More experience required")
    return dict(
        score=score,
        reasons=reasons,
        unmet=unmet,
        eligible=worker.profile_complete and not unmet,
    )


def discover(worker, skill=None, location=None):
    query = Job.query.join(User, Job.manager_id == User.id).filter(
        Job.status == JobStatus.ACTIVE,
        Job.workers_hired < Job.workers_needed,
        Job.start_date >= localdate(),
        User.is_active.is_(True),
    )
    if skill:
        query = query.filter(Job.skill == SkillType(skill))
    if location:
        query = query.filter(Job.location == location)
    applied = {
        row.job_id for row in JobApplication.query.filter_by(laborer_id=worker.id)
    }
    rows = [(job, matching(job, worker), job.id in applied) for job in query.all()]
    return sorted(
        rows, key=lambda row: (-row[1]["score"], row[0].start_date, row[0].id)
    )


def apply(worker, job_id):
    if not worker.profile_complete:
        raise RecruitmentError("पहले प्रोफ़ाइल पूरी करें / Complete your profile first.", 409)
    job = db.session.get(Job, job_id)
    if not job:
        raise RecruitmentError("काम नहीं मिला / Vacancy not found.", 404)
    existing = JobApplication.query.filter_by(
        laborer_id=worker.id, job_id=job.id
    ).first()
    if existing:
        return existing  # Retrying a submission cannot create a duplicate.
    if (
        job.status != JobStatus.ACTIVE
        or job.workers_hired >= job.workers_needed
        or job.start_date < localdate()
        or not job.manager.is_active
    ):
        raise RecruitmentError(
            "यह काम अब आवेदन नहीं ले रहा / Vacancy is not accepting applications.", 409
        )
    if not matching(job, worker)["eligible"]:
        raise RecruitmentError(
            "कौशल और अनुभव की शर्तें जाँचें / Required skill or experience is missing.", 409
        )
    application = JobApplication(
        laborer_id=worker.id, job_id=job.id, status=ApplicationStatus.APPLIED
    )
    db.session.add(application)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        application = JobApplication.query.filter_by(
            laborer_id=worker.id, job_id=job.id
        ).first()
        if not application:
            raise
    return application


def decide(manager, application_id, action):
    if action not in ("select", "reject", "shortlist"):
        raise RecruitmentError("Choose select, reject or shortlist.")
    application = (
        JobApplication.query.join(Job)
        .filter(JobApplication.id == application_id, Job.manager_id == manager.id)
        .first()
    )
    if not application:
        raise RecruitmentError("Application not found.", 404)
    target = {
        "select": ApplicationStatus.SELECTED,
        "reject": ApplicationStatus.REJECTED,
        "shortlist": ApplicationStatus.SHORTLISTED,
    }[action]
    if application.status == target:
        return application
    allowed = [ApplicationStatus.APPLIED, ApplicationStatus.SHORTLISTED]
    if application.status not in allowed:
        raise RecruitmentError(
            "This decision is final; the application cannot be changed.", 409
        )
    job = application.job
    if action == "select":
        if (
            not application.laborer.is_active
            or not matching(job, application.laborer)["eligible"]
        ):
            raise RecruitmentError(
                "Applicant no longer meets the vacancy requirements.", 409
            )
        # Atomic capacity reservation prevents double hires / exceeding vacancies.
        result = db.session.execute(
            update(Job)
            .where(
                Job.id == job.id,
                Job.manager_id == manager.id,
                Job.status == JobStatus.ACTIVE,
                Job.workers_hired < Job.workers_needed,
                Job.start_date >= localdate(),
            )
            .values(
                workers_hired=Job.workers_hired + 1,
                status=case(
                    (
                        Job.workers_hired + 1 >= Job.workers_needed,
                        literal(JobStatus.FILLED, type_=Job.status.type),
                    ),
                    else_=literal(JobStatus.ACTIVE, type_=Job.status.type),
                ),
            )
            .execution_options(synchronize_session=False)
        )
        if result.rowcount != 1:
            db.session.rollback()
            raise RecruitmentError("No open position remains for this vacancy.", 409)
    result = db.session.execute(
        update(JobApplication)
        .where(JobApplication.id == application.id, JobApplication.status.in_(allowed))
        .values(
            status=target,
            reviewed_at=utcnow(),
            selected_at=utcnow() if action == "select" else None,
        )
        .execution_options(synchronize_session=False)
    )
    if result.rowcount != 1:
        db.session.rollback()
        raise RecruitmentError("Application changed. Refresh before trying again.", 409)
    db.session.commit()
    return db.session.get(JobApplication, application_id)


def job_dict(job):
    return dict(
        id=job.id,
        job_code=job.job_code,
        title=job.title,
        factory=job.manager.factory_name,
        location=job.location,
        worksite_address=job.worksite_address,
        wage=job.pay_amount,
        wage_unit=job.pay_unit,
        employment_category=job.category,
        category_label=CATEGORY_LABELS.get(
            job.category, CATEGORY_LABELS["direct_unspecified"]
        ),
        category_claim="नियोक्ता ने प्रकार बताया है; सत्यापन नहीं हुआ।"
        if job.employment_category
        else "पुराने रिकॉर्ड में प्रकार नहीं बताया गया।",
        source="ShramLink",
        external=False,
        skill=job.skill.value,
        domain=job.domain,
        shift=job.shift_timing,
        start_date=job.start_date.isoformat(),
        requirements=job.description,
        min_experience=job.min_experience,
        min_experience_months=job.required_experience_months,
        experience_label=experience_label(job.required_experience_months),
        spoken_summary=job_summary(job),
        spoken_requirements=f"काम की जगह। {job.worksite_address or job.location}। नियोक्ता की शर्तें। {job.description or 'अलग शर्तें नहीं दी गई हैं'}",
        needed=job.workers_needed,
        hired=job.workers_hired,
        status=job.status.value,
        information_source="self_reported",
        demo=bool(job.manager.demo_account),
    )

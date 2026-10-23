import json
from enum import Enum

from flask_login import LoginManager, UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from werkzeug.security import check_password_hash, generate_password_hash

from app.timeutils import localdate, utcnow

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "info"


class UserRole(str, Enum):
    LABORER = "laborer"
    MANAGER = "manager"
    ADMIN = "admin"


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), unique=True, nullable=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum(UserRole), nullable=False, default=UserRole.LABORER)
    name = db.Column(db.String(100), nullable=False)
    is_verified = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    # Laborer specific fields
    age = db.Column(db.Integer, nullable=True)
    skills = db.Column(db.Text, nullable=True)  # JSON array
    upi_id = db.Column(db.String(100), nullable=True)
    eshram_number = db.Column(db.String(50), nullable=True)
    kyc_status = db.Column(
        db.String(20), default="pending"
    )  # pending, approved, rejected
    kyc_method = db.Column(db.String(20), nullable=True)
    # MVP profile fields. Legacy verification flags are retained, not trusted.
    preferred_domain = db.Column(db.String(40), nullable=True)
    experience_years = db.Column(db.Integer, nullable=True)
    experience_months = db.Column(db.Integer, nullable=True)
    location = db.Column(db.String(100), nullable=True)
    profile_complete = db.Column(db.Boolean, nullable=False, default=False)
    credential_version = db.Column(db.Integer, nullable=False, default=2)
    demo_account = db.Column(db.Boolean, nullable=False, default=False)

    # Manager specific fields
    factory_name = db.Column(db.String(200), nullable=True)
    factory_address = db.Column(db.Text, nullable=True)
    gstin = db.Column(db.String(30), nullable=True)
    gst_certificate = db.Column(db.String(200), nullable=True)
    pan_number = db.Column(db.String(20), nullable=True)

    # Relationships
    laborer_jobs = db.relationship(
        "JobApplication",
        backref="laborer",
        lazy="dynamic",
        foreign_keys="JobApplication.laborer_id",
    )
    manager_jobs = db.relationship(
        "Job", backref="manager", lazy="dynamic", foreign_keys="Job.manager_id"
    )
    ratings_given = db.relationship(
        "WorkerRating",
        backref="rater",
        lazy="dynamic",
        foreign_keys="WorkerRating.rater_id",
    )
    ratings_received = db.relationship(
        "WorkerRating",
        backref="worker",
        lazy="dynamic",
        foreign_keys="WorkerRating.worker_id",
    )

    @property
    def total_experience_months(self):
        from app.experience import months_or_legacy

        return months_or_legacy(self.experience_months, self.experience_years)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def get_id(self):
        return f"{self.id}:{self.credential_version}"

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_skills_list(self):
        if self.skills:
            try:
                value = json.loads(self.skills)
                return value if isinstance(value, list) else []
            except (ValueError, TypeError):
                return []
        return []

    def set_skills_list(self, skills_list):
        self.skills = json.dumps(skills_list)

    @property
    def avg_rating(self):
        avg = (
            db.session.query(func.avg(WorkerRating.rating))
            .filter(WorkerRating.worker_id == self.id)
            .scalar()
        )
        return round(avg, 1) if avg else None

    @property
    def selected_jobs_count(self):
        return JobApplication.query.filter(
            JobApplication.laborer_id == self.id,
            JobApplication.status == ApplicationStatus.SELECTED,
        ).count()

    def __repr__(self):
        return f"<User {self.name} ({self.role.value})>"


class SkillType(str, Enum):
    WELDER = "welder"
    CONSTRUCTION = "construction"
    LOADER = "loader"
    ELECTRICIAN = "electrician"
    PAINTER = "painter"
    HELPER = "helper"


class JobStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    FILLED = "filled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Job(db.Model):
    __tablename__ = "jobs"

    id = db.Column(db.Integer, primary_key=True)
    job_code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    title = db.Column(db.String(100), nullable=False)
    title_hi = db.Column(db.String(100), nullable=True)
    description = db.Column(db.Text, nullable=True)
    skill = db.Column(db.Enum(SkillType), nullable=False)
    wage_per_day = db.Column(db.Integer, nullable=False)
    # Additive V3 fields. NULL category on historical records means unspecified.
    employment_category = db.Column(db.String(30), nullable=True)
    wage_amount = db.Column(db.Integer, nullable=True)
    wage_unit = db.Column(db.String(10), nullable=True)
    fixture_key = db.Column(db.String(80), nullable=True)
    workers_needed = db.Column(db.Integer, default=1)
    workers_hired = db.Column(db.Integer, default=0)
    shift_timing = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    domain = db.Column(db.String(40), nullable=True)
    min_experience = db.Column(db.Integer, nullable=False, default=0)
    min_experience_months = db.Column(db.Integer, nullable=True)
    worksite_address = db.Column(db.String(200), nullable=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.Enum(JobStatus), default=JobStatus.ACTIVE, index=True)
    verified_only = db.Column(
        db.Boolean, default=False
    )  # Historical field, not an MVP gate.
    mass_hire_enabled = db.Column(db.Boolean, default=False)
    mass_hire_fee = db.Column(db.Integer, default=0)
    platform_fee = db.Column(db.Integer, default=0)
    total_escrow = db.Column(db.Integer, default=0)
    escrow_paid = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    manager_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    # Relationships
    applications = db.relationship("JobApplication", backref="job", lazy="dynamic")
    escrow_records = db.relationship("EscrowRecord", backref="job", lazy="dynamic")
    mass_hire_requests = db.relationship(
        "MassHireRequest", backref="job", lazy="dynamic"
    )

    @property
    def pay_amount(self):
        return self.wage_amount if self.wage_amount is not None else self.wage_per_day

    @property
    def pay_unit(self):
        return self.wage_unit or "day"

    @property
    def category(self):
        return self.employment_category or "direct_unspecified"

    @property
    def required_experience_months(self):
        from app.experience import months_or_legacy

        return months_or_legacy(self.min_experience_months, self.min_experience) or 0

    def __repr__(self):
        return f"<Job {self.job_code}: {self.title}>"


class ApplicationStatus(str, Enum):
    APPLIED = "applied"
    SHORTLISTED = "shortlisted"
    SELECTED = "selected"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class JobApplication(db.Model):
    __tablename__ = "job_applications"

    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(
        db.Enum(ApplicationStatus), default=ApplicationStatus.APPLIED, index=True
    )
    applied_at = db.Column(db.DateTime, default=utcnow)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    selected_at = db.Column(db.DateTime, nullable=True)
    manager_notes = db.Column(db.Text, nullable=True)

    laborer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey("jobs.id"), nullable=False)

    # For tracking daily application limit
    application_date = db.Column(db.Date, default=localdate, index=True)

    __table_args__ = (
        db.UniqueConstraint(
            "laborer_id", "job_id", name="unique_laborer_job_application"
        ),
        db.Index("idx_laborer_date", "laborer_id", "application_date"),
    )

    def __repr__(self):
        return f"<JobApplication {self.laborer_id} -> {self.job_id}>"


class EscrowStatus(str, Enum):
    # Legacy storage only. No payment routes or new records in the recruitment MVP.
    HELD = "held"
    WORK_DONE = "work_done"
    PAID_UPI = "paid_upi"
    CASH_ZONE = "cash_zone"
    REFUNDED = "refunded"


class EscrowRecord(db.Model):
    __tablename__ = "escrow_records"

    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Integer, nullable=False)
    workers_count = db.Column(db.Integer, default=1)
    status = db.Column(db.Enum(EscrowStatus), default=EscrowStatus.HELD, index=True)
    released_at = db.Column(db.DateTime, nullable=True)
    payment_method = db.Column(db.String(20), nullable=True)  # upi, cash
    transaction_id = db.Column(db.String(100), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    job_id = db.Column(db.Integer, db.ForeignKey("jobs.id"), nullable=False)
    manager_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    def __repr__(self):
        return f"<EscrowRecord {self.id}: {self.amount} ({self.status.value})>"


class MassHireRequest(db.Model):
    __tablename__ = "mass_hire_requests"

    id = db.Column(db.Integer, primary_key=True)
    request_code = db.Column(db.String(20), unique=True, nullable=False)
    workers_needed = db.Column(db.Integer, nullable=False)
    workers_assigned = db.Column(db.Integer, default=0)
    status = db.Column(
        db.String(20), default="pending"
    )  # pending, in_progress, completed, cancelled
    request_date = db.Column(db.Date, default=localdate)
    target_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    job_id = db.Column(db.Integer, db.ForeignKey("jobs.id"), nullable=False)
    manager_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    # Relationships
    assignments = db.relationship(
        "MassHireAssignment", backref="request", lazy="dynamic"
    )

    def __repr__(self):
        return f"<MassHireRequest {self.request_code}: {self.workers_assigned}/{self.workers_needed}>"


class MassHireAssignment(db.Model):
    __tablename__ = "mass_hire_assignments"

    id = db.Column(db.Integer, primary_key=True)
    assigned_at = db.Column(db.DateTime, default=utcnow)
    status = db.Column(
        db.String(20), default="assigned"
    )  # assigned, confirmed, completed, cancelled

    request_id = db.Column(
        db.Integer, db.ForeignKey("mass_hire_requests.id"), nullable=False
    )
    laborer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    def __repr__(self):
        return f"<MassHireAssignment {self.id}: laborer {self.laborer_id}>"


class WorkerRating(db.Model):
    __tablename__ = "worker_ratings"

    id = db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.Integer, nullable=False)  # 1-5
    feedback_tags = db.Column(db.Text, nullable=True)  # JSON array
    comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow)

    rater_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    worker_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey("jobs.id"), nullable=True)

    def get_tags_list(self):
        if self.feedback_tags:
            try:
                return json.loads(self.feedback_tags)
            except (ValueError, TypeError):
                return []
        return []

    def set_tags_list(self, tags_list):
        self.feedback_tags = json.dumps(tags_list)

    def __repr__(self):
        return f"<WorkerRating {self.rating}/5: {self.rater_id} -> {self.worker_id}>"


class VerificationRequest(db.Model):
    __tablename__ = "verification_requests"

    id = db.Column(db.Integer, primary_key=True)
    entity_type = db.Column(db.String(20), nullable=False)  # factory, laborer
    entity_name = db.Column(db.String(200), nullable=False)
    owner_name = db.Column(db.String(100), nullable=False)
    gstin = db.Column(db.String(30), nullable=True)
    eshram_number = db.Column(db.String(50), nullable=True)
    kyc_method = db.Column(db.String(20), nullable=True)
    skill = db.Column(db.String(50), nullable=True)
    age = db.Column(db.Integer, nullable=True)
    city = db.Column(db.String(100), nullable=True)
    documents = db.Column(db.Text, nullable=True)  # JSON array of document paths
    status = db.Column(
        db.String(20), default="pending", index=True
    )  # pending, approved, rejected
    reviewed_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    review_notes = db.Column(db.Text, nullable=True)
    submitted_at = db.Column(db.DateTime, default=utcnow)

    def __repr__(self):
        return f"<VerificationRequest {self.entity_type}: {self.entity_name} ({self.status})>"


@login_manager.user_loader
def load_user(user_id):
    try:
        identifier, version = user_id.split(":", 1)
        user = db.session.get(User, int(identifier))
    except (ValueError, TypeError):
        return None
    if (
        not user
        or not user.is_active
        or user.credential_version < 2
        or str(user.credential_version) != version
    ):
        return None
    return user


class LoginAttempt(db.Model):
    """Short-lived, HMAC-keyed abuse counters; no submitted identifiers stored."""

    __tablename__ = "login_attempts"
    id = db.Column(db.Integer, primary_key=True)
    account_key = db.Column(db.String(64), nullable=False, index=True)
    ip_key = db.Column(db.String(64), nullable=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow, index=True)


class ExternalVacancy(db.Model):
    """Read-only provider/fictional vacancy snapshot. Never a direct hiring job."""

    __tablename__ = "external_vacancies"
    id = db.Column(db.Integer, primary_key=True)
    source_key = db.Column(db.String(180), nullable=False, unique=True)
    source = db.Column(db.String(40), nullable=False)
    payload = db.Column(db.JSON, nullable=False)
    is_demo = db.Column(db.Boolean, nullable=False, default=False)
    active = db.Column(db.Boolean, nullable=False, default=True)
    retrieved_at = db.Column(db.DateTime, nullable=False, default=utcnow)


class DemoPreparation(db.Model):
    """Local preview only. This model has no hiring/submission status or sender."""

    __tablename__ = "demo_preparations"
    id = db.Column(db.Integer, primary_key=True)
    laborer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    vacancy_id = db.Column(
        db.Integer, db.ForeignKey("external_vacancies.id"), nullable=False
    )
    snapshot = db.Column(db.JSON, nullable=False)
    prepared_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    vacancy = db.relationship("ExternalVacancy")
    __table_args__ = (
        db.UniqueConstraint("laborer_id", "vacancy_id", name="unique_demo_preparation"),
    )


class ServiceBudget(db.Model):
    """Atomic service limits across app processes; contains no transcripts."""

    __tablename__ = "service_budgets"
    key = db.Column(db.String(160), primary_key=True)
    count = db.Column(db.Integer, nullable=False, default=0)


class ServiceMetric(db.Model):
    __tablename__ = "service_metrics"
    key = db.Column(db.String(100), primary_key=True)
    count = db.Column(db.Integer, nullable=False, default=0)

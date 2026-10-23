"""V2 persistence, exact eligibility and safe additive upgrade contracts."""

import pytest
from sqlalchemy import text
from conftest import PROFILE, post, vacancy

from app.commands import init_database
from app.experience import experience_label
from app.models import Job, User, db


@pytest.mark.parametrize(
    "months,label",
    [
        (6, "6 months"),
        (12, "12 months"),
        (15, "15 months"),
        (17, "17 months"),
        (18, "18 months"),
        (23, "23 months"),
        (24, "2 years"),
        (32, "2 years"),
        (42, "3 years"),
    ],
)
def test_exact_months_persist_and_display(journey, months, label):
    worker, _ = journey
    profile = {k: v for k, v in PROFILE.items() if k != "experience_years"}
    result = post(
        worker, "/api/laborer/profile", json=dict(profile, experience_months=months)
    )
    assert result.status_code == 200
    saved = worker.get("/api/laborer/profile").json["profile"]
    assert saved["experience_months"] == months
    assert saved["experience_years"] == months // 12
    assert experience_label(months, "en") == label


@pytest.mark.parametrize("months", [-1, 1.5, "2 saal", True, None, 745, 97])
def test_invalid_or_age_inconsistent_months_rejected(journey, months):
    worker, _ = journey
    profile = {k: v for k, v in PROFILE.items() if k != "experience_years"}
    response = post(
        worker, "/api/laborer/profile", json=dict(profile, experience_months=months)
    )
    assert response.status_code == 400
    assert worker.get("/api/laborer/profile").json["profile"]["experience_months"] == 36


def test_exact_requirement_is_not_rounded_down(journey):
    worker, manager = journey
    job_data = {k: v for k, v in vacancy().items() if k != "min_experience"}
    job = post(
        manager, "/api/manager/post-job", json=dict(job_data, min_experience_months=37)
    ).json["job"]
    assert job["experience_label"] == "3 वर्ष" and job["min_experience_months"] == 37
    result = post(worker, "/api/laborer/apply", json={"job_id": job["id"]})
    assert result.status_code == 409
    profile = {k: v for k, v in PROFILE.items() if k != "experience_years"}
    assert (
        post(
            worker, "/api/laborer/profile", json=dict(profile, experience_months=37)
        ).status_code
        == 200
    )
    assert (
        post(worker, "/api/laborer/apply", json={"job_id": job["id"]}).status_code
        == 200
    )
    assert b'id="job-data">[]</script>' in worker.get("/discover").data


def test_conflicting_units_and_missing_confirmation_rejected(journey):
    worker, manager = journey
    assert (
        post(
            worker, "/api/laborer/profile", json=dict(PROFILE, experience_months=17)
        ).status_code
        == 400
    )
    assert (
        post(
            worker, "/api/laborer/profile", json=dict(PROFILE, confirmed="no")
        ).status_code
        == 400
    )
    assert (
        post(
            manager,
            "/api/manager/post-job",
            json=vacancy(min_experience_months=17, min_experience=2),
        ).status_code
        == 400
    )


def test_v1_month_upgrade_adds_columns_preserves_years_and_is_repeatable(app, journey):
    worker, manager = journey
    job_id = post(manager, "/api/manager/post-job", json=vacancy()).json["job"]["id"]
    with app.app_context():
        user = User.query.filter_by(email="worker@example.invalid").one()
        user_id = user.id
        original = (user.name, user.password_hash, user.experience_years)
        db.session.remove()
        with db.engine.begin() as connection:
            connection.execute(text("ALTER TABLE users DROP COLUMN experience_months"))
            connection.execute(
                text("ALTER TABLE jobs DROP COLUMN min_experience_months")
            )
        init_database()
        init_database()
        user = db.session.get(User, user_id)
        job = db.session.get(Job, job_id)
        assert user.experience_months == 36 and job.min_experience_months == 12
        assert (user.name, user.password_hash, user.experience_years) == original
        user.experience_months = 37
        job.min_experience_months = 15
        db.session.commit()
        init_database()
        db.session.expire_all()
        assert user.experience_months == 37 and job.min_experience_months == 15


def test_job_speech_uses_stored_wage_city_shift_and_exact_requirement(journey):
    _, manager = journey
    job = post(
        manager,
        "/api/manager/post-job",
        json=vacancy(min_experience=2, min_experience_months=32),
    ).json["job"]
    speech = job["spoken_summary"]
    assert "आठ सौ पचास रुपये" in speech and "दिल्ली" in speech
    assert "सुबह नौ बजे से शाम पाँच बजे तक" in speech
    assert "दो साल आठ महीने" in speech
    assert job["title"] in speech and job["factory"] in speech
    assert job["requirements"] in job["spoken_requirements"]


def test_discovery_requires_worker_role_and_completed_profile(app, journey):
    worker, manager = journey
    assert app.test_client().get("/discover").status_code == 302
    assert manager.get("/discover").status_code == 403
    assert worker.get("/discover").status_code == 200

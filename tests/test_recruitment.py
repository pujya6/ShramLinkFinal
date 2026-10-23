from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta

import pytest
from conftest import PROFILE, TEST_PASSWORD, account, login, post, vacancy

from app.models import (
    ApplicationStatus,
    EscrowRecord,
    Job,
    JobApplication,
    JobStatus,
    User,
    UserRole,
    db,
)
from app.recruitment import RecruitmentError, decide


def test_full_registration_profile_and_recruitment_persist_after_login(app):
    worker = app.test_client()
    manager = app.test_client()
    # Synthetic number used only inside a temporary test database.
    result = post(
        worker,
        "/register/laborer",
        {
            "phone": "6999999901",
            "password": TEST_PASSWORD,
            "confirm_password": TEST_PASSWORD,
            "role": "admin",
            "is_verified": "true",
        },
    )
    assert result.status_code == 302 and result.location.endswith("/onboarding")
    assert worker.get("/onboarding").status_code == 200
    assert post(worker, "/onboarding", PROFILE).status_code == 302
    assert post(worker, "/logout").status_code == 302
    assert login(worker, "6999999901").status_code == 302
    saved = worker.get("/api/laborer/profile").json
    assert saved["complete"] and saved["profile"]["name"] == PROFILE["name"]
    assert (
        saved["information_source"] == "self_reported"
        and saved["verified_credentials"] == []
    )
    result = post(
        manager,
        "/register/manager",
        dict(
            email="factory@example.invalid",
            name="Test Manager",
            factory_name="Test Factory",
            factory_address="Test industrial area",
            password=TEST_PASSWORD,
            confirm_password=TEST_PASSWORD,
            role="admin",
        ),
    )
    assert result.status_code == 302
    response = post(manager, "/api/manager/post-job", json=vacancy())
    assert response.status_code == 201
    job = response.json["job"]
    job_id = job["id"]
    assert worker.get("/api/laborer/jobs").json["jobs"][0]["match"]["score"] == 100
    assert post(worker, f"/jobs/{job_id}/apply").status_code == 302
    applications = manager.get(
        "/api/manager/workers", query_string={"job_id": job_id}
    ).json["applicants"]
    assert applications[0]["name"] == PROFILE["name"]
    assert "eshram_number" not in applications[0]
    application_id = applications[0]["id"]
    assert (
        post(
            manager, f"/applications/{application_id}/decision", {"action": "select"}
        ).status_code
        == 302
    )
    assert post(manager, "/logout").status_code == 302
    assert login(manager, "factory@example.invalid").status_code == 302
    assert (
        manager.get("/api/manager/workers", query_string={"job_id": job_id}).json[
            "applicants"
        ][0]["status"]
        == "selected"
    )
    assert (
        worker.get("/api/laborer/my-jobs").json["applications"][0]["status"]
        == "selected"
    )
    assert worker.get("/dashboard/laborer").status_code == 200
    assert manager.get(f"/jobs/{job_id}/applicants").status_code == 200
    with app.app_context():
        job = db.session.get(Job, job_id)
        assert job.status == JobStatus.FILLED and job.workers_hired == 1
        assert EscrowRecord.query.count() == 0 and not job.escrow_paid
        assert User.query.filter_by(phone="6999999901").one().role == UserRole.LABORER
        assert (
            User.query.filter_by(email="factory@example.invalid").one().role
            == UserRole.MANAGER
        )


def test_duplicate_applications_and_decisions_are_idempotent(app, journey):
    worker, manager = journey
    job_id = post(manager, "/api/manager/post-job", json=vacancy()).json["job"]["id"]
    a = post(worker, "/api/laborer/apply", json={"job_id": job_id}).json[
        "application_id"
    ]
    assert (
        post(worker, "/api/laborer/apply", json={"job_id": job_id}).json[
            "application_id"
        ]
        == a
    )
    assert (
        post(
            manager, "/api/manager/hire", json={"application_id": a, "action": "select"}
        ).status_code
        == 200
    )
    assert (
        post(
            manager, "/api/manager/hire", json={"application_id": a, "action": "select"}
        ).status_code
        == 200
    )
    assert (
        post(
            manager, "/api/manager/hire", json={"application_id": a, "action": "reject"}
        ).status_code
        == 409
    )
    with app.app_context():
        assert JobApplication.query.count() == 1
        assert db.session.get(Job, job_id).workers_hired == 1


def test_shortlist_and_reject_persist(journey):
    worker, manager = journey
    job = post(manager, "/api/manager/post-job", json=vacancy()).json["job"]
    a = post(worker, "/api/laborer/apply", json={"job_id": job["id"]}).json[
        "application_id"
    ]
    for action, status in [("shortlist", "shortlisted"), ("reject", "rejected")]:
        assert (
            post(
                manager,
                "/api/manager/hire",
                json={"application_id": a, "action": action},
            ).json["status"]
            == status
        )
        assert (
            worker.get("/api/laborer/my-jobs").json["applications"][0]["status"]
            == status
        )
    assert (
        post(
            manager, "/api/manager/hire", json={"application_id": a, "action": "select"}
        ).status_code
        == 409
    )


def test_last_position_is_not_overfilled(app, journey):
    worker, manager = journey
    account(app, UserRole.LABORER, "worker2@example.invalid")
    worker2 = app.test_client()
    login(worker2, "worker2@example.invalid")
    post(worker2, "/api/laborer/profile", json=PROFILE)
    job_id = post(manager, "/api/manager/post-job", json=vacancy()).json["job"]["id"]
    ids = [
        post(w, "/api/laborer/apply", json={"job_id": job_id}).json["application_id"]
        for w in [worker, worker2]
    ]
    with app.app_context():
        manager_id = User.query.filter_by(email="employer@example.invalid").one().id

    def select_one(application_id):
        with app.app_context():
            try:
                decide(db.session.get(User, manager_id), application_id, "select")
                return "selected"
            except RecruitmentError as exc:
                return exc.status

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(select_one, ids))
    assert sorted(str(v) for v in results) == ["409", "selected"]
    with app.app_context():
        assert db.session.get(Job, job_id).workers_hired == 1
        assert (
            JobApplication.query.filter_by(status=ApplicationStatus.SELECTED).count()
            == 1
        )


@pytest.mark.parametrize(
    "change",
    [
        {"wage": 0},
        {"wage": True},
        {"wage": 1.5},
        {"wage": "not a number"},
        {"workers": -1},
        {"workers": 99999999},
        {"skill": "unlisted"},
        {"location": "Mars"},
        {"domain": []},
        {"requirements": ""},
        {"title": ["wrong type"]},
        {"start_date": "2020-01-01"},
        {"start_date": "bad"},
        {"min_experience": -1},
        {"wage": "9" * 5000},
    ],
)
def test_invalid_vacancy_returns_validation_errors(journey, change):
    worker, manager = journey
    response = post(manager, "/api/manager/post-job", json=vacancy(**change))
    assert response.status_code == 400 and response.json["errors"]
    assert manager.get("/api/manager/dashboard").json["jobs"] == []


@pytest.mark.parametrize(
    "change",
    [
        {"age": 17},
        {"age": 81},
        {"age": "25.5"},
        {"age": True},
        {"name": "A"},
        {"skills": []},
        {"skills": "welder"},
        {"skills": ["invented"]},
        {"skills": [{}]},
        {"preferred_domain": "invalid"},
        {"location": "invalid"},
        {"experience_years": 9},
        {"experience_years": None},
        {"eshram_number": "abc"},
        {"eshram_number": "123"},
        {"confirmed": "no"},
    ],
)
def test_invalid_profile_never_overwrites_saved_profile(journey, change):
    worker, _ = journey
    before = worker.get("/api/laborer/profile").json["profile"]
    assert (
        post(worker, "/api/laborer/profile", json=dict(PROFILE, **change)).status_code
        == 400
    )
    assert worker.get("/api/laborer/profile").json["profile"] == before


def test_matching_filters_and_required_experience(journey):
    worker, manager = journey
    post(manager, "/api/manager/post-job", json=vacancy(title="Delhi match"))
    far = post(
        manager,
        "/api/manager/post-job",
        json=vacancy(title="Noida experienced", location="Noida", min_experience=5),
    ).json["job"]["id"]
    jobs = worker.get("/api/laborer/jobs").json["jobs"]
    assert jobs[0]["title"] == "Delhi match" and jobs[0]["match"]["score"] == 100
    assert jobs[1]["match"]["score"] == 65 and not jobs[1]["match"]["eligible"]
    assert post(worker, "/api/laborer/apply", json={"job_id": far}).status_code == 409
    assert len(worker.get("/api/laborer/jobs?location=Noida").json["jobs"]) == 1
    assert worker.get("/api/laborer/jobs?skill=not-valid").status_code == 400


def test_closed_and_past_vacancies_reject_application(app, journey):
    worker, manager = journey
    job_id = post(manager, "/api/manager/post-job", json=vacancy()).json["job"]["id"]
    with app.app_context():
        job = db.session.get(Job, job_id)
        job.start_date = date.today() - timedelta(days=1)
        db.session.commit()
    assert (
        post(worker, "/api/laborer/apply", json={"job_id": job_id}).status_code == 409
    )
    assert worker.get("/api/laborer/jobs").json["jobs"] == []


def test_profile_edit_and_eshram_stays_self_reported(journey):
    worker, manager = journey
    profile = dict(PROFILE, name="बदला हुआ नाम", eshram_number="123456789012")
    assert post(worker, "/api/laborer/profile", json=profile).status_code == 200
    saved = worker.get("/api/laborer/profile").json
    assert (
        saved["profile"]["name"] == profile["name"]
        and saved["verified_credentials"] == []
    )

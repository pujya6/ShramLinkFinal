"""Release bootstrap/diagnostics and public read-only evidence. Synthetic data only."""

import json
import re
import sqlite3
from datetime import timedelta

import pytest
from conftest import PROFILE, TEST_PASSWORD, account, login, post, vacancy
from sqlalchemy.exc import OperationalError

from app import create_app, recruitment
from app.commands import init_database
from app.demo_setup import bootstrap
from app.models import (
    DemoPreparation,
    ExternalVacancy,
    Job,
    JobApplication,
    JobStatus,
    User,
    UserRole,
    db,
)
from app.settings import configure
from app.showcase import synthetic_matches
from app.timeutils import localdate


def cards(response):
    return json.loads(
        re.search(
            rb'<script type="application/json" id="job-data">(.*?)</script>',
            response.data,
            re.S,
        ).group(1)
    )


def boot(app, refresh=False):
    with app.app_context():
        return bootstrap(TEST_PASSWORD, refresh)


def test_bootstrap_from_uninitialized_file_and_idempotence(tmp_path):
    path = tmp_path / "nested" / "demo.sqlite3"
    app = create_app(
        dict(
            TESTING=True,
            SECRET_KEY="synthetic-test-secret",
            SQLALCHEMY_DATABASE_URI="sqlite:///" + str(path),
            SHRAMLINK_DEMO=True,
            VOICE_PROVIDER="deterministic",
            JOB_SOURCE="demo",
        )
    )
    for _ in range(2):
        result = app.test_cli_runner().invoke(
            args=["bootstrap-demo"], input=TEST_PASSWORD + "\n" + TEST_PASSWORD + "\n"
        )
        assert result.exit_code == 0, result.output
        assert (
            "eligible direct: 3" in result.output
            and "total visible cards: 8" in result.output
        )
        assert TEST_PASSWORD not in result.output
    with app.app_context():
        assert (
            User.query.count(),
            Job.query.count(),
            ExternalVacancy.query.count(),
        ) == (5, 6, 2)
        assert JobApplication.query.count() == DemoPreparation.query.count() == 0
        assert all(
            j.start_date == localdate() + timedelta(days=7) for j in Job.query.all()
        )
        assert (
            User.query.filter_by(email="worker.v3@example.invalid")
            .one()
            .check_password(TEST_PASSWORD)
        )
        db.session.remove()
        db.engine.dispose()


def test_bootstrap_refuses_legacy_before_schema_changes(tmp_path):
    path = tmp_path / "legacy.sqlite3"
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)")
        connection.execute("INSERT INTO users VALUES (1, 'Synthetic legacy')")
    app = create_app(
        dict(
            TESTING=True,
            SECRET_KEY="test-secret",
            SHRAMLINK_DEMO=True,
            SQLALCHEMY_DATABASE_URI="sqlite:///" + str(path),
        )
    )
    result = app.test_cli_runner().invoke(
        args=["bootstrap-demo", "--password", TEST_PASSWORD]
    )
    assert result.exit_code != 0 and "before migration" in result.output
    with sqlite3.connect(path) as connection:
        assert connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall() == [("users",)]
        assert connection.execute("SELECT * FROM users").fetchall() == [
            (1, "Synthetic legacy")
        ]
    with app.app_context():
        db.engine.dispose()


def test_bootstrap_refuses_non_demo_and_disabled_mode(app):
    account(app, UserRole.LABORER, "synthetic-realish@example.invalid")
    result = app.test_cli_runner().invoke(
        args=["bootstrap-demo", "--password", TEST_PASSWORD]
    )
    assert result.exit_code != 0 and "No records changed" in result.output
    with app.app_context():
        assert Job.query.count() == ExternalVacancy.query.count() == 0
    app.config["SHRAMLINK_DEMO"] = False
    result = app.test_cli_runner().invoke(
        args=["bootstrap-demo", "--password", TEST_PASSWORD]
    )
    assert result.exit_code != 0 and "isolated demonstration" in result.output


def test_bootstrap_preserves_passwords_outcomes_and_only_explicitly_refreshes_unused(
    app,
):
    boot(app)
    with app.app_context():
        worker = User.query.filter_by(email="worker.v3@example.invalid").one()
        jobs = Job.query.order_by(Job.id).all()
        application = recruitment.apply(worker, jobs[0].id)
        used, closed, unused = jobs[0].id, jobs[1].id, jobs[2].id
        jobs[1].status = JobStatus.CANCELLED
        for j in jobs:
            j.start_date = localdate() - timedelta(days=2)
        db.session.commit()
        digest = worker.password_hash
        assert bootstrap("a-different-synthetic-password")["dates_refreshed"] == 0
        assert worker.password_hash == digest
        result = bootstrap(TEST_PASSWORD, True)
        assert result["dates_refreshed"] == 4
        assert db.session.get(Job, used).start_date < localdate()
        assert db.session.get(Job, closed).status == JobStatus.CANCELLED
        assert db.session.get(Job, unused).start_date >= localdate()
        assert (
            JobApplication.query.count() == 1 and application.status.value == "applied"
        )
        assert bootstrap(TEST_PASSWORD, True)["dates_refreshed"] == 0


def test_seeded_and_new_registered_worker_have_matching_cards_and_internal_flow(app):
    boot(app)
    worker, employer, fresh = app.test_client(), app.test_client(), app.test_client()
    login(worker, "worker.v3@example.invalid")
    visible = cards(worker.get("/discover"))
    assert (
        len(visible) == 8
        and sum(not j["external"] and j["match"]["eligible"] for j in visible) == 3
    )
    eligible = next(j for j in visible if not j["external"] and j["match"]["eligible"])
    application = post(
        worker, "/api/laborer/apply", json={"job_id": eligible["id"]}
    ).json
    login(employer, "employer1.v3@example.invalid")
    assert (
        post(
            employer,
            "/api/manager/hire",
            json={"application_id": application["application_id"], "action": "select"},
        ).json["status"]
        == "selected"
    )
    assert eligible["id"] not in [j["id"] for j in cards(worker.get("/discover"))]
    assert (
        post(
            fresh,
            "/register/laborer",
            data={
                "phone": "6999999981",
                "password": TEST_PASSWORD,
                "confirm_password": TEST_PASSWORD,
            },
        ).status_code
        == 302
    )
    assert (
        post(
            fresh,
            "/api/laborer/profile",
            json=dict(PROFILE, name="जीत झा", experience_months=32, experience_years=2),
        ).status_code
        == 200
    )
    assert len(cards(fresh.get("/discover"))) == 8
    assert next(j for j in cards(fresh.get("/discover")) if j["id"] == eligible["id"])[
        "match"
    ]["eligible"]


@pytest.mark.parametrize(
    "demo,reason", [(True, "uninitialized"), (False, "no_vacancies")]
)
def test_empty_unseeded_vs_no_vacancies(app, journey, demo, reason):
    app.config["SHRAMLINK_DEMO"] = demo
    response = journey[0].get("/discover")
    assert f'data-reason="{reason}"'.encode() in response.data
    assert (
        b"bootstrap-demo" not in response.data and b"DATABASE_URL" not in response.data
    )


def test_filters_eligibility_and_expired_status_are_distinguished(app):
    boot(app)
    worker = app.test_client()
    login(worker, "worker.v3@example.invalid")
    assert (
        b'data-reason="filters"'
        in worker.get("/discover?skill=welder&location=Gurugram").data
    )
    with app.app_context():
        w = User.query.filter_by(email="worker.v3@example.invalid").one()
        w.set_skills_list(["construction"])
        w.experience_months = 0
        db.session.commit()
    response = worker.get("/discover")
    assert b'data-reason="no_eligible"' in response.data and len(cards(response)) == 8
    with app.app_context():
        for j in Job.query.all():
            j.start_date = localdate() - timedelta(days=1)
        for v in ExternalVacancy.query.all():
            v.active = False
        db.session.commit()
    assert b'data-reason="unavailable"' in worker.get("/discover").data


def test_already_applied_exclusion_has_history_recovery(app, journey):
    worker, manager = journey
    job = post(manager, "/api/manager/post-job", json=vacancy()).json["job"]
    post(worker, "/api/laborer/apply", json={"job_id": job["id"]})
    response = worker.get("/discover")
    assert cards(response) == [] and b'data-reason="reviewed"' in response.data
    assert b"/dashboard/laborer#applications" in response.data


@pytest.mark.parametrize(
    "voice,jobs,requested,effective",
    [
        ("api", "demo", "V3a", "V3b"),
        ("deterministic", "demo", "V3b", "V3b"),
        ("deterministic", "integrated", "V3c", "V3b"),
        ("api", "integrated", "V3d", "V3b"),
    ],
)
def test_public_showcase_is_safe_and_shows_requested_effective(
    app, client, monkeypatch, voice, jobs, requested, effective
):
    app.config.update(
        VOICE_PROVIDER=voice, JOB_SOURCE=jobs, XAI_API_KEY="", GREENHOUSE_BOARD=""
    )
    configure(app)
    monkeypatch.setattr(
        "app.network.request_json",
        lambda *a, **k: pytest.fail("Showcase cannot call providers"),
    )
    response = client.get("/inside")
    assert response.status_code == 200
    assert f'id="requested-mode">{requested}'.encode() in response.data
    assert f'id="effective-mode">{effective}'.encode() in response.data
    for forbidden in [
        b"/admin/",
        b"XAI_API_KEY",
        b"SECRET_KEY",
        b"confirmation_token",
        b"@example.invalid",
    ]:
        assert forbidden not in response.data
    assert client.post("/inside").status_code in (400, 405)
    with app.app_context():
        assert (
            User.query.count()
            == JobApplication.query.count()
            == DemoPreparation.query.count()
            == 0
        )


def test_showcase_matching_examples_use_real_engine():
    examples = synthetic_matches()
    assert examples["welder:Delhi:32"]["score"] == 100
    assert examples["welder:Noida:32"]["eligible"] is True
    assert examples["welder:Noida:32"]["score"] == 70
    assert examples["helper:Delhi:18"]["eligible"] is False


def test_database_failure_returns_private_recoverable_error(app, journey, monkeypatch):
    def broken(*args, **kwargs):
        raise OperationalError(
            "sensitive_sql",
            {"secret": "synthetic-private-marker"},
            Exception("private_db_path"),
        )

    monkeypatch.setattr(recruitment, "discover", broken)
    response = journey[0].get("/discover")
    assert response.status_code == 503
    assert b"Retry" in response.data
    for marker in [b"sensitive_sql", b"synthetic-private-marker", b"private_db_path"]:
        assert marker not in response.data


def test_health_reports_missing_schema_without_leaking_connection(tmp_path):
    app = create_app(
        dict(
            TESTING=True,
            SECRET_KEY="test-secret",
            SQLALCHEMY_DATABASE_URI="sqlite:///"
            + str(tmp_path / "uninitialized.sqlite3"),
        )
    )
    assert app.test_client().get("/healthz").status_code == 503
    with app.app_context():
        init_database()
        assert app.test_client().get("/healthz").json["status"] == "ok"
        db.session.remove()
        db.engine.dispose()

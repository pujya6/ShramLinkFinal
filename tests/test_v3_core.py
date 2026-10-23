import json

import pytest
from conftest import PROFILE, TEST_PASSWORD, account, login, post, vacancy

from app.commands import init_database
from app.demo_fixtures import seed_v3
from app.external_jobs import PREPARED_STATUS
from app.models import (
    DemoPreparation,
    ExternalVacancy,
    Job,
    JobApplication,
    User,
    UserRole,
    db,
)
from app.settings import configure


def external(app, **overrides):
    with app.app_context():
        data = dict(
            title="प्रदर्शन वेल्डर",
            factory="काल्पनिक उद्योग",
            skill="welder",
            location="Noida",
            wage=24000,
            wage_unit="month",
            min_experience_months=24,
            shift=None,
            start_date=None,
            worksite_address=None,
            requirements="काल्पनिक कौशल परीक्षण",
            original_url="https://example.invalid/demo",
            missing_information=["कौशल प्रमाणपत्र जाँचना बाकी है।"],
        )
        data.update(overrides)
        row = ExternalVacancy(
            source_key="demo:test",
            source="Fictional demo board",
            payload=data,
            is_demo=True,
        )
        db.session.add(row)
        db.session.commit()
        return row.id


@pytest.mark.parametrize(
    "voice,jobs,mode",
    [
        ("api", "demo", "V3a"),
        ("deterministic", "demo", "V3b"),
        ("deterministic", "integrated", "V3c"),
        ("api", "integrated", "V3d"),
    ],
)
def test_four_configurations(app, voice, jobs, mode):
    app.config.update(
        VOICE_PROVIDER=voice,
        JOB_SOURCE=jobs,
        XAI_API_KEY="synthetic-key",
        XAI_MODEL="grok-4.3",
        GREENHOUSE_BOARD="synthetic",
        GREENHOUSE_EMPLOYER="Fictional",
        GREENHOUSE_FORMAL_ATTESTED=True,
    )
    configure(app)
    assert app.config["CONFIGURATION_LABEL"] == mode
    app.config.update(XAI_API_KEY="", GREENHOUSE_BOARD="")
    configure(app)
    assert app.config["CONFIGURATION_LABEL"] == "V3b"


@pytest.mark.parametrize(
    "key,value",
    [
        ("VOICE_PROVIDER", "unknown"),
        ("JOB_SOURCE", "scrape"),
        ("GREENHOUSE_BOARD", "http://127.0.0.1"),
        ("XAI_MODEL", "not-documented"),
        ("XAI_DAILY_REQUEST_LIMIT", 999),
        ("XAI_INPUT_USD_PER_MILLION", "nan"),
        ("SHRAMLINK_DEMO", "maybe"),
    ],
)
def test_invalid_settings_fail_closed(app, key, value):
    app.config[key] = value
    with pytest.raises(RuntimeError):
        configure(app)


def test_direct_formal_monthly_recruitment_and_speech(app, journey):
    worker, manager = journey
    response = post(
        manager,
        "/api/manager/post-job",
        json=vacancy(
            employment_category="direct_formal", wage_unit="month", wage=24000
        ),
    )
    assert response.status_code == 201
    job = response.json["job"]
    assert (job["wage"], job["wage_unit"], job["employment_category"]) == (
        24000,
        "month",
        "direct_formal",
    )
    assert "हर महीने चौबीस हज़ार" in job["spoken_summary"]
    assert "रोज़ चौबीस" not in job["spoken_summary"]
    assert b"24000/month" in manager.get(f"/jobs/{job['id']}/applicants").data
    application = post(worker, "/api/laborer/apply", json={"job_id": job["id"]}).json
    assert (
        post(
            manager,
            "/api/manager/hire",
            json={"application_id": application["application_id"], "action": "select"},
        ).json["status"]
        == "selected"
    )
    assert (
        worker.get("/api/laborer/my-jobs").json["applications"][0]["job"]["wage_unit"]
        == "month"
    )
    assert b"24000" in manager.get("/dashboard/manager").data.replace(b",", b"")


@pytest.mark.parametrize(
    "changes",
    [
        {"employment_category": "formal_external"},
        {"wage_unit": "year"},
        {"employment_category": True},
    ],
)
def test_employer_cannot_forge_external_categories_or_units(journey, changes):
    assert (
        post(journey[1], "/api/manager/post-job", json=vacancy(**changes)).status_code
        == 400
    )


def test_v3_additive_migration_keeps_precise_values_and_unknown_category(app, journey):
    _, manager = journey
    job_id = post(
        manager,
        "/api/manager/post-job",
        json=vacancy(min_experience_months=32, min_experience=2),
    ).json["job"]["id"]
    with app.app_context():
        for _ in range(2):
            init_database()
        job = db.session.get(Job, job_id)
        assert job.required_experience_months == 32
        assert job.category == "direct_unspecified"
        assert job.pay_amount == 850 and job.pay_unit == "day"


def test_repeatable_isolated_fixtures_no_fake_outcomes(app):
    with app.app_context():
        seed_v3(TEST_PASSWORD)
        seed_v3("different-test-password")
        assert (
            User.query.count(),
            Job.query.count(),
            ExternalVacancy.query.count(),
        ) == (5, 6, 2)
        assert JobApplication.query.count() == DemoPreparation.query.count() == 0
        assert all(u.demo_account and not u.is_verified for u in User.query.all())
        assert all(j.workers_hired == 0 for j in Job.query.all())
        assert (
            User.query.filter_by(email="worker.v3@example.invalid")
            .first()
            .check_password(TEST_PASSWORD)
        )


def test_fixtures_refuse_production_data(app, journey):
    result = app.test_cli_runner().invoke(
        args=["seed-demo-v3", "--password", TEST_PASSWORD]
    )
    assert result.exit_code != 0 and "Non-demo accounts exist" in result.output
    with app.app_context():
        assert Job.query.count() == ExternalVacancy.query.count() == 0


def test_external_preview_confirm_idempotency_and_separate_status(
    app, journey, monkeypatch
):
    worker, manager = journey
    row_id = external(app)

    def no_network(*args, **kwargs):
        pytest.fail("An external preparation must not call any third party")

    monkeypatch.setattr("app.network.request_json", no_network)
    preview = worker.get(f"/api/laborer/external/{row_id}/preview").json
    assert preview["job"]["match"]["eligible"] is False
    assert preview["job"]["match"]["reasons"]
    assert preview["job"]["match"]["unmet"]
    assert "eshram_number" not in json.dumps(preview)
    path = f"/api/laborer/external/{row_id}/prepare"
    assert post(worker, path, json={}).status_code == 400
    data = dict(confirmed="yes", confirmation_token=preview["confirmation_token"])
    assert worker.post(path, json=data).status_code == 400  # CSRF
    first = post(worker, path, json=data)
    assert first.status_code == 200 and first.json["status"] == "demo_prepared"
    assert (
        post(worker, path, json=data).json["preparation_id"]
        == first.json["preparation_id"]
    )
    with app.app_context():
        assert JobApplication.query.count() == 0 and DemoPreparation.query.count() == 1
    assert PREPARED_STATUS.encode() in worker.get("/dashboard/laborer").data
    assert worker.get("/api/laborer/my-jobs").json["applications"] == []
    assert post(manager, path, json=data).status_code == 403


def test_external_review_invalidated_by_changed_profile_and_other_user(app, journey):
    worker, _ = journey
    row_id = external(app)
    review = worker.get(f"/api/laborer/external/{row_id}/preview").json
    post(worker, "/api/laborer/profile", json=dict(PROFILE, name="बदला परीक्षण"))
    data = dict(confirmed="yes", confirmation_token=review["confirmation_token"])
    assert (
        post(worker, f"/api/laborer/external/{row_id}/prepare", json=data).status_code
        == 409
    )
    account(app, UserRole.LABORER, "second@example.invalid")
    other = app.test_client()
    login(other, "second@example.invalid")
    post(other, "/api/laborer/profile", json=PROFILE)
    assert (
        post(other, f"/api/laborer/external/{row_id}/prepare", json=data).status_code
        == 409
    )


def test_external_inactive_and_unauthorized(app, client, journey):
    row_id = external(app)
    assert client.get(f"/api/laborer/external/{row_id}/preview").status_code == 401
    with app.app_context():
        db.session.get(ExternalVacancy, row_id).active = False
        db.session.commit()
    assert journey[0].get(f"/api/laborer/external/{row_id}/preview").status_code == 404


def test_modes_hidden_from_ordinary_worker_and_admin_metrics_protected(app, journey):
    worker, manager = journey
    page = worker.get("/onboarding").data.decode()
    assert 'class="mode-indicator"' not in page
    assert worker.get("/admin/service-status").status_code == 403
    assert manager.get("/admin/service-status").status_code == 403
    assert worker.get("/healthz").json["status"] == "ok"

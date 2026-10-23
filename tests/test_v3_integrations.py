"""Provider contract simulations. These tests do NOT contact paid APIs."""

import json
from datetime import timedelta

import pytest
from conftest import post, vacancy

from app.interpretation import SCHEMA, validated_output
from app.job_feed import normalize, refresh_feed
from app.models import ExternalVacancy, ServiceMetric, db
from app.settings import configure
from app.timeutils import utcnow


def configured(app, voice="api", jobs="integrated"):
    app.config.update(
        VOICE_PROVIDER=voice,
        JOB_SOURCE=jobs,
        XAI_API_KEY="synthetic-test-only-key",
        XAI_MODEL="grok-4.3",
        GREENHOUSE_BOARD="syntheticboard",
        GREENHOUSE_EMPLOYER="Fictional board employer",
        GREENHOUSE_FORMAL_ATTESTED=True,
    )
    configure(app)


def board_row(**overrides):
    row = dict(
        id=101,
        title="Welder",
        location={"name": "Noida, India"},
        absolute_url="https://job-boards.greenhouse.io/syntheticboard/jobs/101",
        content="&lt;p&gt;Welding test required.&lt;/p&gt;&lt;script&gt;bad()&lt;/script&gt;",
    )
    row.update(overrides)
    return row


def extraction(**overrides):
    result = dict(
        intent="answer",
        field="skills",
        text_value=None,
        number_value=None,
        skills=["welder"],
        evidence="metal jodne",
        clarification="",
    )
    result.update(overrides)
    return result


def response(value=None, **overrides):
    result = dict(
        status="completed",
        output=[
            dict(
                type="message",
                content=[
                    dict(type="output_text", text=json.dumps(value or extraction()))
                ],
            )
        ],
        usage=dict(input_tokens=120, output_tokens=60),
    )
    result.update(overrides)
    return result


def interpret_request(worker, **overrides):
    data = dict(
        transcript="mujhe metal jodne ka kaam aata hai",
        field="skills",
        phase="answer",
        age=28,
    )
    data.update(overrides)
    return post(worker, "/api/laborer/interpret", json=data)


def test_feed_success_cache_honest_missing_and_retirement(app, monkeypatch):
    configured(app)
    calls = []

    def provider(url, **kwargs):
        calls.append(url)
        assert kwargs["timeout"] == 5 and "payload" not in kwargs
        return {
            "jobs": [
                board_row(),
                board_row(id=2, title="Software Engineer"),
                board_row(id=3, location={"name": "Mumbai"}),
            ]
        }

    monkeypatch.setattr("app.job_feed.request_json", provider)
    with app.app_context():
        refresh_feed()
        refresh_feed()
        assert len(calls) == 1
        row = ExternalVacancy.query.one()
        assert not row.is_demo and row.payload["wage"] is None
        assert row.payload["min_experience_months"] is None
        assert "bad()" not in row.payload["requirements"]
        assert row.payload["original_url"].startswith(
            "https://job-boards.greenhouse.io/"
        )
        monkeypatch.setattr("app.job_feed.time.time", lambda: 1999999999)
        monkeypatch.setattr("app.job_feed.request_json", lambda *a, **k: {"jobs": []})
        assert "कोई बाहरी अवसर" in refresh_feed()
        assert not db.session.get(ExternalVacancy, row.id).active


@pytest.mark.parametrize(
    "row",
    [
        board_row(title="Sales of welding equipment"),
        board_row(location={"name": "Remote, India"}),
        board_row(absolute_url="javascript:alert(1)"),
        board_row(absolute_url="https://evil.example/job"),
        board_row(id=True),
        board_row(location=None),
    ],
)
def test_feed_does_not_invent_supported_roles_places_or_trust_urls(row):
    assert normalize(row, "Example") is None


def test_feed_failure_bounded_cache_and_expiry(app, monkeypatch):
    configured(app)
    count = []

    def unavailable(*a, **k):
        count.append(1)
        raise TimeoutError()

    monkeypatch.setattr("app.job_feed.request_json", unavailable)
    with app.app_context():
        row = ExternalVacancy(
            source_key="greenhouse:syntheticboard:12",
            source="Greenhouse",
            payload={},
            retrieved_at=utcnow() - timedelta(days=2),
        )
        db.session.add(row)
        db.session.commit()
        assert "संपर्क नहीं हुआ" in refresh_feed()
        refresh_feed()
        assert count == [1] and not row.active


def test_api_structured_extraction_no_mutation_and_minimum_payload(
    app, journey, monkeypatch
):
    configured(app)
    calls = []

    def provider(url, **kwargs):
        calls.append(url)
        assert url == "https://api.x.ai/v1/responses"
        body = kwargs["payload"]
        assert body["store"] is False and body["reasoning"] == {"effort": "none"}
        assert body["max_output_tokens"] == 384
        assert body["text"]["format"]["schema"] == SCHEMA
        assert not body.get("tools") and "phone" not in body["input"][1]["content"]
        assert kwargs["timeout"] == 6 and kwargs["max_bytes"] == 32000
        return response()

    monkeypatch.setattr("app.interpretation.request_json", provider)
    worker, _ = journey
    before = worker.get("/api/laborer/profile").json
    result = interpret_request(worker)
    assert result.json == dict(
        provider="api",
        fallback=False,
        intent="answer",
        field="skills",
        value=["welder"],
    )
    assert worker.get("/api/laborer/profile").json == before
    assert len(calls) == 1
    with app.app_context():
        assert db.session.get(ServiceMetric, "voice_input_tokens").count == 120
        assert db.session.get(ServiceMetric, "voice_success").count == 1


@pytest.mark.parametrize(
    "value",
    [
        extraction(is_verified=True),
        extraction(skills=["doctor"]),
        extraction(intent="save"),
        extraction(evidence="invented words"),
        extraction(number_value=True),
        extraction(skills=[None]),
        extraction(
            intent="answer", field="name", text_value="Invented Name", skills=[]
        ),
        extraction(intent="clarify", skills=["welder"]),
        extraction(field="age", number_value=90, skills=[]),
        extraction(field="experience_months", number_value=180, skills=[]),
    ],
)
def test_provider_schema_and_contract_rejection(value):
    with pytest.raises(ValueError):
        validated_output(value, "mujhe metal jodne ka kaam aata hai", "skills", age=28)


@pytest.mark.parametrize(
    "failure", ["timeout", "malformed", "incomplete", "schema", "refusal"]
)
def test_provider_errors_fall_back_without_saving(app, journey, monkeypatch, failure):
    configured(app)

    def provider(*a, **k):
        if failure == "timeout":
            raise TimeoutError()
        if failure == "malformed":
            return []
        if failure == "incomplete":
            return response(status="incomplete")
        if failure == "schema":
            return response(extraction(verified=True))
        return response(
            output=[dict(type="message", content=[dict(type="refusal", refusal="no")])]
        )

    monkeypatch.setattr("app.interpretation.request_json", provider)
    result = interpret_request(journey[0])
    assert (
        result.status_code == 200
        and result.json["fallback"]
        and result.json["reason"] == "provider_error"
    )


def test_api_rate_limit_and_missing_key_never_fake_cloud_success(
    app, journey, monkeypatch
):
    configured(app)
    app.config["XAI_DAILY_REQUEST_LIMIT"] = 2
    calls = []
    monkeypatch.setattr(
        "app.interpretation.request_json", lambda *a, **k: calls.append(1) or response()
    )
    for _ in range(2):
        assert not interpret_request(journey[0]).json["fallback"]
    assert interpret_request(journey[0]).json["reason"] == "limit"
    app.config["XAI_API_KEY"] = ""
    configure(app)
    assert interpret_request(journey[0]).json["reason"] == "not_configured"
    assert len(calls) == 2


@pytest.mark.parametrize(
    "overrides",
    [
        {"field": "eshram_number"},
        {"phase": "review"},
        {"transcript": "x" * 401},
        {"age": True},
        {"transcript": {}},
    ],
)
def test_interpret_input_boundary(journey, overrides):
    assert interpret_request(journey[0], **overrides).status_code == 400


def test_api_auth_and_csrf(app, client, journey):
    assert post(client, "/api/laborer/interpret", json={}).status_code == 401
    assert post(journey[1], "/api/laborer/interpret", json={}).status_code == 403
    assert journey[0].post("/api/laborer/interpret", json={}).status_code == 400


def test_correction_and_ambiguity_stay_within_field_contracts():
    corrected = validated_output(
        extraction(
            intent="correct", field="name", text_value="सुरेश", skills=[], evidence="सुरेश"
        ),
        "pehli baat badal kar सुरेश rakho",
        "age",
        28,
    )
    assert corrected == dict(intent="correct", field="name", value="सुरेश")
    clarification = validated_output(
        extraction(
            intent="clarify", skills=[], evidence="", clarification="Give your password"
        ),
        "पता नहीं",
        "experience_months",
        28,
    )
    assert "password" not in clarification["clarification"]
    assert "कितने साल" in clarification["clarification"]


@pytest.mark.parametrize(
    "voice,jobs,mode",
    [
        ("api", "demo", "V3a"),
        ("deterministic", "demo", "V3b"),
        ("deterministic", "integrated", "V3c"),
        ("api", "integrated", "V3d"),
    ],
)
def test_four_modes_share_recruitment_and_optional_service_contracts(
    app, journey, monkeypatch, voice, jobs, mode
):
    configured(app, voice, jobs)
    monkeypatch.setattr(
        "app.job_feed.request_json", lambda *a, **k: {"jobs": [board_row()]}
    )
    monkeypatch.setattr("app.interpretation.request_json", lambda *a, **k: response())
    worker, manager = journey
    assert app.config["CONFIGURATION_LABEL"] == mode
    result = interpret_request(worker).json
    assert result["fallback"] is (voice == "deterministic")
    page = worker.get("/discover")
    assert page.status_code == 200
    assert (b"Greenhouse" in page.data) is (jobs == "integrated")
    job = post(
        manager,
        "/api/manager/post-job",
        json=vacancy(
            employment_category="direct_formal", wage_unit="month", wage=23000
        ),
    ).json["job"]
    applied = post(worker, "/api/laborer/apply", json={"job_id": job["id"]}).json
    assert (
        post(
            manager,
            "/api/manager/hire",
            json={"application_id": applied["application_id"], "action": "select"},
        ).json["status"]
        == "selected"
    )
    assert (
        worker.get("/api/laborer/my-jobs").json["applications"][0]["status"]
        == "selected"
    )

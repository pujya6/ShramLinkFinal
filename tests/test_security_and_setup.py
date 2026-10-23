import sqlite3
from pathlib import Path

import pytest
from conftest import PROFILE, TEST_PASSWORD, account, csrf, login, post, vacancy

from app import create_app
from app.commands import init_database
from app.models import Job, User, UserRole, db


def test_csrf_all_mutations_and_logout(client, journey):
    worker, manager = journey
    assert (
        client.post("/register/laborer", data={"phone": "6999999901"}).status_code
        == 400
    )
    assert client.post("/login", data={"identifier": "a"}).status_code == 400
    assert manager.post("/api/manager/post-job", json=vacancy()).status_code == 400
    assert worker.post("/api/laborer/profile", json=PROFILE).status_code == 400
    assert worker.post("/logout").status_code == 400
    assert worker.get("/logout").status_code == 405
    assert post(worker, "/logout").status_code == 302
    assert worker.get("/api/laborer/profile").status_code == 401


def test_role_ownership_and_anonymous_guards(app, client, journey):
    worker, manager = journey
    assert client.get("/api/manager/dashboard").status_code == 401
    assert post(client, "/api/laborer/apply", json={"job_id": 1}).status_code == 401
    assert post(worker, "/api/manager/post-job", json=vacancy()).status_code == 403
    assert post(manager, "/api/laborer/profile", json=PROFILE).status_code == 403
    assert worker.get("/admin/").status_code == 403
    assert manager.get("/admin/").status_code == 403
    account(app, UserRole.MANAGER, "outsider@example.invalid")
    other = app.test_client()
    login(other, "outsider@example.invalid")
    job_id = post(manager, "/api/manager/post-job", json=vacancy()).json["job"]["id"]
    a = post(worker, "/api/laborer/apply", json={"job_id": job_id}).json[
        "application_id"
    ]
    assert other.get(f"/jobs/{job_id}/applicants").status_code == 404
    assert other.get(f"/api/manager/workers?job_id={job_id}").status_code == 404
    assert (
        post(
            other, "/api/manager/hire", json={"application_id": a, "action": "select"}
        ).status_code
        == 404
    )
    assert (
        post(
            worker, "/api/manager/hire", json={"application_id": a, "action": "select"}
        ).status_code
        == 403
    )


def test_inactive_accounts_and_password_reset_invalidate_sessions(app, journey):
    worker, manager = journey
    with app.app_context():
        u = User.query.filter_by(email="worker@example.invalid").one()
        uid = u.id
        u.is_active = False
        db.session.commit()
    assert worker.get("/api/laborer/profile").status_code == 401
    assert login(worker, "worker@example.invalid").status_code == 400
    with app.app_context():
        u = db.session.get(User, uid)
        u.is_active = True
        db.session.commit()
    login(worker, "worker@example.invalid")
    result = app.test_cli_runner().invoke(
        args=[
            "reset-password",
            "--user-id",
            str(uid),
            "--password",
            "changed-test-password",
        ]
    )
    assert result.exit_code == 0
    assert worker.get("/api/laborer/profile").status_code == 401
    assert login(worker, "worker@example.invalid").status_code == 400
    assert (
        login(worker, "worker@example.invalid", "changed-test-password").status_code
        == 302
    )


def test_login_throttled_without_storing_identifiers(app, client):
    app.config["LOGIN_ACCOUNT_LIMIT"] = 2
    assert login(client, "not-an-account@example.invalid").status_code == 400
    assert login(client, "not-an-account@example.invalid").status_code == 400
    assert login(client, "not-an-account@example.invalid").status_code == 429


@pytest.mark.parametrize("value", [[], "bad", None, True])
def test_malformed_json_is_rejected(journey, value):
    worker, manager = journey
    result = manager.post(
        "/api/manager/post-job",
        data=__import__("json").dumps(value),
        content_type="application/json",
        headers={"X-CSRFToken": csrf(manager, "/")},
    )
    assert result.status_code == 400


def test_security_headers_and_user_content_escaping(journey):
    worker, manager = journey
    post(
        worker,
        "/api/laborer/profile",
        json=dict(PROFILE, name="<script>alert(1)</script>"),
    )
    response = worker.get("/dashboard/laborer")
    assert b"<script>alert(1)</script>" not in response.data
    assert b"&lt;script&gt;" in response.data
    assert response.headers["Cache-Control"] == "no-store"
    assert "script-src 'self'" in response.headers["Content-Security-Policy"]
    assert response.headers["X-Frame-Options"] == "DENY"


def test_retired_payment_endpoints_absent_and_no_claims(journey):
    worker, manager = journey
    for path in [
        "/api/manager/escrow",
        "/admin/api/escrow",
        "/admin/api/escrow/update",
        "/admin/api/escrow/generate-bill",
    ]:
        assert manager.get(path).status_code == 404
        assert post(manager, path, json={}).status_code == 404
    root = Path(__file__).resolve().parents[1]
    for path in list((root / "templates").rglob("*.html")) + list(
        (root / "static").rglob("*.js")
    ):
        source = path.read_text().lower()
        assert not any(
            word in source
            for word in ("escrow", "payout", "payment gateway", "razorpay", "stripe")
        )


def test_fresh_repeatable_initialization_and_explicit_demo(app):
    runner = app.test_cli_runner()
    assert runner.invoke(args=["init-db"]).exit_code == 0
    assert runner.invoke(args=["init-db"]).exit_code == 0
    with app.app_context():
        assert User.query.count() == 0
    for _ in range(2):
        assert (
            runner.invoke(args=["seed-demo", "--password", TEST_PASSWORD]).exit_code
            == 0
        )
    with app.app_context():
        assert User.query.count() == 2 and Job.query.count() == 1
        assert all(u.demo_account and not u.is_verified for u in User.query.all())


def test_legacy_upgrade_is_additive_preserves_rows_and_locks_old_credentials(tmp_path):
    path = tmp_path / "legacy.sqlite3"
    connection = sqlite3.connect(path)
    connection.executescript(
        (Path(__file__).parent / "fixtures/legacy_schema.sql").read_text()
    )
    connection.execute(
        "INSERT INTO users (id,email,password_hash,role,name,is_verified,is_active) VALUES (1,'legacy@example.invalid','old-unusable-hash','LABORER','Legacy test worker',1,1)"
    )
    connection.execute(
        "INSERT INTO jobs (id,job_code,title,skill,wage_per_day,workers_needed,workers_hired,shift_timing,location,start_date,status,manager_id,total_escrow,escrow_paid) VALUES (1,'OLD-1','Legacy vacancy','WELDER',800,2,0,'09:00-17:00','Delhi','2026-10-01','ACTIVE',1,1600,1)"
    )
    connection.execute(
        "INSERT INTO escrow_records (id,amount,workers_count,status,job_id,manager_id) VALUES (1,1600,2,'HELD',1,1)"
    )
    connection.commit()
    before = {
        table: connection.execute(f"SELECT * FROM {table}").fetchall()
        for table in ["users", "jobs", "escrow_records"]
    }
    sizes = {
        table: len(connection.execute(f"PRAGMA table_info({table})").fetchall())
        for table in before
    }
    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-only",
            "SQLALCHEMY_DATABASE_URI": "sqlite:///" + str(path),
        }
    )
    with app.app_context():
        init_database()
        init_database()
        assert db.session.get(User, 1).credential_version == 1
        assert db.session.get(
            User, 1
        ).is_verified  # Stored history preserved, never rendered as verified.
        for table, rows in before.items():
            assert [
                row[: sizes[table]]
                for row in connection.execute(f"SELECT * FROM {table}")
            ] == rows
        db.session.remove()
        db.engine.dispose()
    connection.close()


def test_production_requires_new_secret(monkeypatch):
    monkeypatch.setenv("SHRAMLINK_ENV", "production")
    monkeypatch.delenv("SECRET_KEY", raising=False)
    with pytest.raises(RuntimeError):
        create_app({"SECRET_KEY": None})
    app = create_app(
        {"SECRET_KEY": "x" * 64, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"}
    )
    assert app.config["SESSION_COOKIE_SECURE"] is True
    assert "max-age" in app.test_client().get("/").headers["Strict-Transport-Security"]

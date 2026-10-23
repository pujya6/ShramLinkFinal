from threading import Thread
from playwright.sync_api import sync_playwright
from werkzeug.serving import make_server

import re
from datetime import date, timedelta

import pytest

from app import create_app
from app.commands import init_database
from app.models import User, UserRole, db

TEST_PASSWORD = "test-only-long-password"
PROFILE = dict(
    name="परीक्षण श्रमिक",
    age=26,
    skills=["welder", "helper"],
    preferred_domain="manufacturing",
    experience_years=3,
    location="Delhi",
    eshram_number="",
    confirmed="yes",
)


def vacancy(**overrides):
    result = dict(
        title="Test arc welder",
        requirements="Arc welding experience. Safety equipment provided.",
        skill="welder",
        domain="manufacturing",
        location="Delhi",
        worksite_address="Test factory, industrial estate",
        wage=850,
        workers=1,
        min_experience=1,
        shift="09:00–17:00",
        start_date=(date.today() + timedelta(days=1)).isoformat(),
    )
    result.update(overrides)
    return result


@pytest.fixture
def app(tmp_path):
    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-key-never-for-production",
            "SQLALCHEMY_DATABASE_URI": "sqlite:///" + str(tmp_path / "test.sqlite3"),
            "LOGIN_ACCOUNT_LIMIT": 100,
            "LOGIN_IP_LIMIT": 200,
        }
    )
    with app.app_context():
        init_database()
    yield app
    with app.app_context():
        db.session.remove()
        db.engine.dispose()


@pytest.fixture
def client(app):
    return app.test_client()


def csrf(client, path="/login"):
    response = client.get(path)
    match = re.search(rb'<meta name="csrf-token" content="([^"]+)"', response.data)
    assert match, (path, response.status_code)
    return match.group(1).decode()


def post(client, path, data=None, json=None):
    token = csrf(client, "/")
    if json is not None:
        return client.post(path, json=json, headers={"X-CSRFToken": token})
    return client.post(path, data=dict(data or {}, csrf_token=token))


def account(app, role, email, **kwargs):
    with app.app_context():
        user = User(
            email=email, role=role, name="Test account", credential_version=2, **kwargs
        )
        if role == UserRole.MANAGER:
            user.factory_name = "Test Factory"
            user.factory_address = "Test Delhi factory"
        user.set_password(TEST_PASSWORD)
        db.session.add(user)
        db.session.commit()
        return user.id


def login(client, email, password=TEST_PASSWORD):
    return post(client, "/login", {"identifier": email, "password": password})


@pytest.fixture
def journey(app):
    worker = app.test_client()
    manager = app.test_client()
    account(app, UserRole.LABORER, "worker@example.invalid")
    account(app, UserRole.MANAGER, "employer@example.invalid")
    assert login(worker, "worker@example.invalid").status_code == 302
    assert post(worker, "/api/laborer/profile", json=PROFILE).status_code == 200
    assert login(manager, "employer@example.invalid").status_code == 302
    return worker, manager


@pytest.fixture(scope="module")
def browser():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, args=["--no-sandbox"])
        yield browser
        browser.close()


@pytest.fixture
def live(app):
    server = make_server("127.0.0.1", 0, app, threaded=True)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()
    thread.join(timeout=5)

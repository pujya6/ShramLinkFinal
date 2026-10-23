"""Reproducible screenshots using temporary, fictional accounts; no saved cookies.

Run from the source checkout: .venv/bin/python scripts/capture_screenshots.py --label v3
Use --source /path/to/archived-v2 for before evidence without switching branches.
"""

import argparse
import logging
import secrets
import sys
import tempfile
from datetime import timedelta
from pathlib import Path
from threading import Thread

parser = argparse.ArgumentParser()
parser.add_argument("--label", choices=["v2", "v3"], default="v3")
parser.add_argument("--source", type=Path, default=Path(__file__).resolve().parents[1])
args = parser.parse_args()
sys.path.insert(0, str(args.source))

from playwright.sync_api import sync_playwright
from werkzeug.serving import make_server

from app import create_app, recruitment
from app.commands import init_database
from app.models import User, UserRole, db
from app.timeutils import localdate

output = Path(__file__).resolve().parents[1] / "docs" / "screenshots" / args.label
output.mkdir(parents=True, exist_ok=True)
logging.getLogger("werkzeug").setLevel(logging.ERROR)
password = secrets.token_urlsafe(24)
with tempfile.TemporaryDirectory(prefix="shramlink-screenshots-") as temp:
    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": secrets.token_hex(32),
            "SQLALCHEMY_DATABASE_URI": "sqlite:///" + temp + "/screen.sqlite3",
            "VOICE_PROVIDER": "deterministic",
            "JOB_SOURCE": "demo",
        }
    )
    with app.app_context():
        init_database()
        worker = User(
            email="screen-worker@example.invalid",
            name="रमेश कुमार",
            role=UserRole.LABORER,
            credential_version=2,
            age=28,
            location="Delhi",
            experience_months=32,
            experience_years=2,
            preferred_domain="manufacturing",
            demo_account=True,
            profile_complete=True,
        )
        worker.set_skills_list(["welder", "helper"])
        manager = User(
            email="screen-employer@example.invalid",
            name="Demo hiring team",
            role=UserRole.MANAGER,
            credential_version=2,
            factory_name="उदय मेटल वर्क्स",
            factory_address="Demo worksite, Delhi",
            demo_account=True,
        )
        for user in [worker, manager]:
            user.set_password(password)
            db.session.add(user)
        db.session.commit()
        recruitment.create_vacancy(
            manager,
            dict(
                title="वेल्डर — दिन की शिफ़्ट",
                requirements="सुरक्षा के जूते और हेलमेट दिए जाएँगे। आर्क वेल्डिंग आनी चाहिए।",
                skill="welder",
                domain="manufacturing",
                location="Delhi",
                worksite_address="ओखला औद्योगिक क्षेत्र · प्रदर्शन स्थल",
                wage=850,
                wage_unit="day",
                employment_category="direct_informal",
                workers=3,
                min_experience_months=12,
                shift="09:00–17:00",
                start_date=(localdate() + timedelta(days=1)).isoformat(),
            ),
        )
    server = make_server("127.0.0.1", 0, app, threaded=True)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{server.server_port}"
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
            for width, height in [(390, 844), (768, 1024), (1440, 1000)]:
                context = browser.new_context(
                    viewport={"width": width, "height": height}, reduced_motion="reduce"
                )
                context.add_init_script(
                    "localStorage.setItem('shramlink-tutorial-v2','seen');localStorage.setItem('shramlink-tutorial-v3','seen')"
                )
                page = context.new_page()
                page.goto(url)
                page.evaluate("document.fonts.ready")
                page.screenshot(
                    path=str(output / f"landing-{width}.png"), full_page=True
                )
                page.goto(url + "/login")
                page.locator("#identifier").fill("screen-worker@example.invalid")
                page.locator("#password").fill(password)
                page.locator("button[type=submit]").click()
                for name, path in [
                    ("dashboard", "/dashboard/laborer"),
                    ("onboarding", "/onboarding"),
                    ("discovery", "/discover"),
                ]:
                    page.goto(url + path)
                    page.evaluate("document.fonts.ready")
                    assert page.evaluate(
                        "document.documentElement.scrollWidth <= innerWidth"
                    ), (name, width)
                    page.screenshot(
                        path=str(output / f"{name}-{width}.png"), full_page=True
                    )
                context.close()
            browser.close()
    finally:
        server.shutdown()
        thread.join(5)
        with app.app_context():
            db.session.remove()
            db.engine.dispose()
print(f"Saved 12 synthetic-data screenshots in {output}")

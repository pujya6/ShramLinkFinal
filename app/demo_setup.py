"""Operator-only bootstrap. Inspect before migrating; never reset demonstration activity."""

from datetime import timedelta
from pathlib import Path

import click
from flask import current_app
from sqlalchemy import inspect, text

from app import external_jobs, recruitment
from app.commands import init_database
from app.demo_fixtures import DIRECT, seed_v3
from app.models import Job, JobApplication, JobStatus, User, db
from app.timeutils import localdate


def preflight():
    if not current_app.config["SHRAMLINK_DEMO"]:
        raise click.ClickException(
            "Set SHRAMLINK_DEMO=true only for an isolated demonstration database."
        )
    if db.engine.dialect.name != "sqlite" or db.engine.url.database in (
        None,
        "",
        ":memory:",
    ):
        raise click.ClickException(
            "Demo bootstrap requires a persistent SQLite file; other databases are not verified."
        )
    Path(db.engine.url.database).parent.mkdir(parents=True, exist_ok=True)
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    quote = db.engine.dialect.identifier_preparer.quote
    allowed = {
        "users",
        "jobs",
        "job_applications",
        "external_vacancies",
        "demo_preparations",
        "login_attempts",
        "service_budgets",
        "service_metrics",
    }
    with db.engine.connect() as connection:
        for table in tables:
            has_rows = connection.execute(
                text(f"SELECT 1 FROM {quote(table)} LIMIT 1")
            ).first()
            if not has_rows:
                continue
            columns = {c["name"] for c in inspector.get_columns(table)}
            unsafe = table not in allowed
            if table == "users":
                unsafe = (
                    "demo_account" not in columns
                    or connection.execute(
                        text(
                            "SELECT 1 FROM users WHERE demo_account IS NULL OR demo_account != 1 LIMIT 1"
                        )
                    ).first()
                )
            elif table == "jobs":
                unsafe = (
                    "fixture_key" not in columns
                    or connection.execute(
                        text(
                            "SELECT 1 FROM jobs WHERE fixture_key IS NULL OR fixture_key NOT LIKE 'v3:%' LIMIT 1"
                        )
                    ).first()
                )
            elif table == "external_vacancies":
                unsafe = (
                    "is_demo" not in columns
                    or connection.execute(
                        text(
                            "SELECT 1 FROM external_vacancies WHERE is_demo IS NULL OR is_demo != 1 LIMIT 1"
                        )
                    ).first()
                )
            if unsafe:
                raise click.ClickException(
                    "Existing non-demo or unrecognized data: bootstrap refused before migration. "
                    "Keep this database; choose a separate empty DATABASE_URL. No records changed."
                )


def bootstrap(password, refresh_unused_dates=False):
    if not 10 <= len(password) <= 128:
        raise click.ClickException(
            "Use an operator-chosen password of 10–128 characters."
        )
    preflight()
    init_database()
    seed_v3(password)
    refreshed = 0
    if refresh_unused_dates:
        # Explicit date-only refresh. Never reopen filled/closed jobs or alter any
        # vacancy with application history, even if that history was withdrawn.
        for job in Job.query.filter(
            Job.fixture_key.in_(["v3:" + row[0] for row in DIRECT])
        ):
            if (
                job.start_date < localdate()
                and job.status == JobStatus.ACTIVE
                and job.workers_hired == 0
                and not JobApplication.query.filter_by(job_id=job.id).first()
            ):
                job.start_date = localdate() + timedelta(days=7)
                refreshed += 1
        db.session.commit()
    worker = User.query.filter_by(email="worker.v3@example.invalid").one()
    rows = [r for r in recruitment.discover(worker) if not r[2]]
    external, _ = external_jobs.available_cards(worker, refresh=False)
    return dict(
        visible_direct=len(rows),
        eligible_direct=sum(r[1]["eligible"] for r in rows),
        visible_external=len(external),
        visible_total=len(rows) + len(external),
        expired_direct=Job.query.filter(
            Job.fixture_key.like("v3:%"), Job.start_date < localdate()
        ).count(),
        dates_refreshed=refreshed,
    )

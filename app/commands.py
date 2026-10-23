"""Explicit, repeatable schema setup; no destructive migrations or automatic users."""

from datetime import timedelta

import click
from sqlalchemy import inspect, text

from app.models import Job, JobStatus, SkillType, User, UserRole, db
from app.timeutils import localdate

ADDITIONS = {
    "users": {
        "preferred_domain": "VARCHAR(40)",
        "experience_years": "INTEGER",
        "experience_months": "INTEGER",
        "location": "VARCHAR(100)",
        "profile_complete": "BOOLEAN NOT NULL DEFAULT 0",
        # Existing passwords / legacy OTP accounts must be reset before logging in.
        "credential_version": "INTEGER NOT NULL DEFAULT 1",
        "demo_account": "BOOLEAN NOT NULL DEFAULT 0",
    },
    "jobs": {
        "domain": "VARCHAR(40)",
        "min_experience": "INTEGER NOT NULL DEFAULT 0",
        "min_experience_months": "INTEGER",
        "worksite_address": "VARCHAR(200)",
        "employment_category": "VARCHAR(30)",
        "wage_amount": "INTEGER",
        "wage_unit": "VARCHAR(10)",
        "fixture_key": "VARCHAR(80)",
    },
}


def init_database():
    db.create_all()
    inspector = inspect(db.engine)
    with db.engine.begin() as connection:
        for table, columns in ADDITIONS.items():
            existing = {column["name"] for column in inspector.get_columns(table)}
            for name, ddl in columns.items():
                if name not in existing:
                    # Names and types are fixed constants above, never user input.
                    connection.execute(
                        text(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}")
                    )
        # Backfill only missing months; repeat runs never round away V2 precision.
        connection.execute(
            text(
                "UPDATE users SET experience_months = experience_years * 12 "
                "WHERE experience_months IS NULL AND experience_years BETWEEN 0 AND 62"
            )
        )
        connection.execute(
            text(
                "UPDATE jobs SET min_experience_months = min_experience * 12 "
                "WHERE min_experience_months IS NULL AND min_experience BETWEEN 0 AND 62"
            )
        )


def register_commands(app):
    @app.cli.command("bootstrap-demo")
    @click.option(
        "--password",
        prompt="Choose a demonstration password (10+ characters)",
        hide_input=True,
        confirmation_prompt=True,
    )
    @click.option(
        "--refresh-unused-dates",
        is_flag=True,
        help="Explicitly move expired, unused ACTIVE fixture dates forward; preserve all application history.",
    )
    def bootstrap_demo(password, refresh_unused_dates):
        from app.demo_setup import bootstrap

        result = bootstrap(password, refresh_unused_dates)
        click.echo(
            "Demo database ready. Existing accounts, passwords and decisions retained."
        )
        click.echo(
            "Worker: worker.v3@example.invalid; employers: employer1.v3@example.invalid through employer4.v3@example.invalid"
        )
        click.echo(
            f"Visible direct: {result['visible_direct']}; eligible direct: {result['eligible_direct']}; "
            f"external demo previews: {result['visible_external']}; total visible cards: {result['visible_total']}."
        )
        click.echo(
            "Counts use the saved seeded worker, no filters, and exclude prior applications/preparations; browser skips are separate."
        )
        click.echo(
            f"Expired direct fixtures: {result['expired_direct']}; unused dates refreshed: {result['dates_refreshed']}."
        )
        if result["expired_direct"]:
            click.echo(
                "For a new demonstration use a fresh database, or explicitly --refresh-unused-dates. Used/closed/filled jobs are never reset."
            )
        click.echo(
            "Seed before registering new participants. A later non-demo account makes repeat bootstrap refuse safely; ordinary startup still works."
        )

    @app.cli.command("init-db")
    def init_db_command():
        init_database()
        click.echo(
            "Database ready. Existing records retained; no demo accounts created."
        )

    @app.cli.command("seed-demo")
    @click.option(
        "--password",
        prompt="Choose a demo password (10+ characters)",
        hide_input=True,
        confirmation_prompt=True,
    )
    def seed_demo(password):
        if not 10 <= len(password) <= 128:
            raise click.ClickException("Use 10–128 characters.")
        init_database()
        identities = [
            ("worker.demo@example.invalid", UserRole.LABORER),
            ("employer.demo@example.invalid", UserRole.MANAGER),
        ]
        users = []
        for email, role in identities:
            user = User.query.filter_by(email=email).first()
            if user and not user.demo_account:
                raise click.ClickException(
                    "Demo identifier already belongs to a non-demo account."
                )
            if not user:
                user = User(
                    email=email,
                    role=role,
                    name="Demo Worker" if role == UserRole.LABORER else "Demo Factory",
                    demo_account=True,
                    credential_version=2,
                    is_verified=False,
                )
                if role == UserRole.LABORER:
                    user.age = 26
                    user.set_skills_list(["welder", "helper"])
                    user.location = "Delhi"
                    user.preferred_domain = "manufacturing"
                    user.experience_years = 3
                    user.experience_months = 36
                    user.profile_complete = True
                else:
                    user.factory_name = "Demo Factory — demonstration only"
                    user.factory_address = "Demo industrial area, Delhi"
                user.set_password(password)
                db.session.add(user)
            users.append(user)
        db.session.flush()
        if not Job.query.filter_by(job_code="DEMO-WELDER").first():
            db.session.add(
                Job(
                    job_code="DEMO-WELDER",
                    title="Demo: Arc welder",
                    skill=SkillType.WELDER,
                    domain="manufacturing",
                    wage_per_day=850,
                    workers_needed=2,
                    workers_hired=0,
                    shift_timing="09:00–17:00",
                    location="Delhi",
                    worksite_address="Demo industrial area, Delhi",
                    start_date=localdate() + timedelta(days=1),
                    status=JobStatus.ACTIVE,
                    description="Demo vacancy. Arc welding and safety equipment experience.",
                    min_experience=1,
                    min_experience_months=12,
                    verified_only=False,
                    manager_id=users[1].id,
                )
            )
        db.session.commit()
        click.echo(
            "Demo accounts ready: worker.demo@example.invalid and employer.demo@example.invalid."
        )
        click.echo(
            "Existing demo accounts and vacancies were not overwritten. Use reset-password to change a password."
        )

    @app.cli.command("seed-demo-v3")
    @click.option(
        "--password",
        prompt="Choose a demonstration password (10+ characters)",
        hide_input=True,
        confirmation_prompt=True,
    )
    def seed_demo_v3(password):
        from app.demo_fixtures import seed_v3

        init_database()
        identities = seed_v3(password)
        click.echo("Fictional fixtures ready: " + identities)
        click.echo(
            "Existing records, dates, passwords and application outcomes were not overwritten."
        )

    @app.cli.command("reset-password")
    @click.option("--user-id", type=int, required=True)
    @click.option(
        "--password",
        prompt="New password (10+ characters)",
        hide_input=True,
        confirmation_prompt=True,
    )
    def reset_password(user_id, password):
        if not 10 <= len(password) <= 128:
            raise click.ClickException("Use 10–128 characters.")
        user = db.session.get(User, user_id)
        if not user:
            raise click.ClickException("Account not found.")
        user.set_password(password)
        user.credential_version = max(2, user.credential_version + 1)
        db.session.commit()
        click.echo(
            "Password reset. Verify account ownership outside the app before using this administrator command."
        )

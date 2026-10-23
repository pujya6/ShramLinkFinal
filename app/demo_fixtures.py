"""Fictional V3 fixtures, opt-in CLI only; no fabricated application outcomes."""

from datetime import timedelta

import click
from flask import current_app

from app.models import ExternalVacancy, Job, JobStatus, SkillType, User, UserRole, db
from app.timeutils import localdate

# Explicit employer category claims, not inferred from wages or job titles.
DIRECT = [
    (
        "weld-day",
        "उदय मेटल अभ्यास इकाई",
        "वेल्डर — दिन की शिफ़्ट",
        "welder",
        "manufacturing",
        "Delhi",
        850,
        "day",
        12,
        "direct_informal",
        "09:00–17:00",
        "आर्क वेल्डिंग। हेलमेट और दस्ताने दिए जाएँगे।",
    ),
    (
        "weld-month",
        "दिशा उद्योग अभ्यास इकाई",
        "फैब्रिकेशन वेल्डर",
        "welder",
        "manufacturing",
        "Noida",
        24000,
        "month",
        24,
        "direct_formal",
        "08:00–17:00",
        "लिखित नौकरी की शर्तों का प्रदर्शन। कौशल परीक्षण और पहचान दस्तावेज़ जाँचे जाएँगे। किसी लाभ का सत्यापन नहीं हुआ है।",
    ),
    (
        "helper",
        "उदय मेटल अभ्यास इकाई",
        "कारखाना हेल्पर",
        "helper",
        "manufacturing",
        "Delhi",
        650,
        "day",
        0,
        "direct_informal",
        "09:00–17:00",
        "नए श्रमिक भी सीख सकते हैं। सुरक्षित औज़ार चलाने का प्रशिक्षण दिया जाएगा।",
    ),
    (
        "load",
        "संगम गोदाम अभ्यास इकाई",
        "गोदाम लोडर",
        "loader",
        "warehouse",
        "Ghaziabad",
        18500,
        "month",
        6,
        "direct_formal",
        "10:00–18:00",
        "सामान लोड करना। वजन और सुरक्षा की शर्तें शुरू करने से पहले तय करें। लिखित शर्तों का प्रदर्शन।",
    ),
    (
        "electric",
        "दिशा उद्योग अभ्यास इकाई",
        "रखरखाव बिजली मिस्त्री",
        "electrician",
        "maintenance",
        "Faridabad",
        1000,
        "day",
        32,
        "direct_informal",
        "09:00–17:00",
        "बिजली का सुरक्षित रखरखाव। अनुभव का परीक्षण होगा। प्रमाणपत्र की आवश्यकता नियोक्ता से जाँचें।",
    ),
    (
        "paint",
        "संगम निर्माण अभ्यास इकाई",
        "औद्योगिक पेंटर",
        "painter",
        "construction",
        "Gurugram",
        22000,
        "month",
        18,
        "direct_formal",
        "08:00–16:00",
        "सतह तैयार करना और पेंट करना। मास्क दिया जाएगा। यह काल्पनिक लिखित रोजगार प्रस्ताव है।",
    ),
]


def seed_v3(password):
    if not current_app.config["SHRAMLINK_DEMO"]:
        raise click.ClickException(
            "V3 fixtures require SHRAMLINK_DEMO=true and an isolated demo database."
        )
    if not 10 <= len(password) <= 128:
        raise click.ClickException("Use 10–128 characters.")
    # Refuse to mix sample accounts with a database containing non-demo users.
    if User.query.filter(User.demo_account.is_not(True)).first():
        raise click.ClickException(
            "Non-demo accounts exist. Use a separate empty demo DATABASE_URL; no records changed."
        )
    worker = User.query.filter_by(email="worker.v3@example.invalid").first()
    if worker and worker.role != UserRole.LABORER:
        raise click.ClickException("Fixture worker identity has an unexpected role; no account will be overwritten.")
    if not worker:
        worker = User(
            email="worker.v3@example.invalid",
            name="रमेश · अभ्यास श्रमिक",
            role=UserRole.LABORER,
            credential_version=2,
            demo_account=True,
            age=28,
            location="Delhi",
            experience_months=32,
            experience_years=2,
            preferred_domain="manufacturing",
            profile_complete=True,
        )
        worker.set_password(password)
        worker.set_skills_list(["welder", "helper"])
        db.session.add(worker)
    managers = {}
    for (
        key,
        factory,
        title,
        skill,
        domain,
        city,
        amount,
        unit,
        months,
        category,
        shift,
        requirements,
    ) in DIRECT:
        if factory not in managers:
            # Fixed synthetic identities; never overwrite accounts/passwords.
            n = list(dict.fromkeys(row[1] for row in DIRECT)).index(factory) + 1
            email = f"employer{n}.v3@example.invalid"
            manager = User.query.filter_by(email=email).first()
            if manager and manager.role != UserRole.MANAGER:
                raise click.ClickException("Fixture employer identity has an unexpected role; no account will be overwritten.")
            if not manager:
                manager = User(
                    email=email,
                    name="Demo hiring team",
                    role=UserRole.MANAGER,
                    credential_version=2,
                    demo_account=True,
                    factory_name=factory + " · DEMO",
                    factory_address="काल्पनिक प्रदर्शन स्थल, Delhi-NCR",
                )
                manager.set_password(password)
                db.session.add(manager)
                db.session.flush()
            managers[factory] = manager
        if not Job.query.filter_by(fixture_key="v3:" + key).first():
            db.session.add(
                Job(
                    fixture_key="v3:" + key,
                    job_code="DEMO-V3-" + key.upper(),
                    title=title,
                    description=requirements + " DEMO: काल्पनिक अवसर।",
                    skill=SkillType(skill),
                    domain=domain,
                    location=city,
                    wage_amount=amount,
                    wage_unit=unit,
                    wage_per_day=amount if unit == "day" else 0,
                    employment_category=category,
                    workers_needed=3,
                    workers_hired=0,
                    min_experience_months=months,
                    min_experience=months // 12,
                    shift_timing=shift,
                    worksite_address="प्रदर्शन औद्योगिक क्षेत्र, " + city,
                    start_date=localdate() + timedelta(days=7),
                    status=JobStatus.ACTIVE,
                    manager_id=managers[factory].id,
                )
            )
    for key, skill, title, amount, months, city in [
        ("external-weld", "welder", "प्रशिक्षित वेल्डर — बाहरी अवसर", 26000, 24, "Noida"),
        ("external-helper", "helper", "उत्पादन सहायक — बाहरी अवसर", 18000, 0, "Delhi"),
    ]:
        if not ExternalVacancy.query.filter_by(source_key="demo:" + key).first():
            db.session.add(
                ExternalVacancy(
                    source_key="demo:" + key,
                    source="Fictional demo board",
                    is_demo=True,
                    payload=dict(
                        title=title,
                        skill=skill,
                        factory="नवकदम अभ्यास उद्योग · काल्पनिक",
                        location=city,
                        wage=amount,
                        wage_unit="month",
                        min_experience_months=months,
                        shift="09:00–17:00",
                        start_date=None,
                        worksite_address=None,
                        original_url="https://example.invalid/demo/" + key,
                        requirements="यह काल्पनिक औपचारिक अवसर है। कौशल परीक्षण और दस्तावेज़ की जरूरत का अभ्यास करें। कोई आवेदन बाहर नहीं जाएगा।",
                        missing_information=[
                            "पहचान और कौशल दस्तावेज़ इस प्रदर्शन में जमा नहीं किए गए हैं।"
                        ],
                    ),
                )
            )
    db.session.commit()
    return "worker.v3@example.invalid; employer1.v3@example.invalid through employer4.v3@example.invalid"

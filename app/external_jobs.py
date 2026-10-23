"""External opportunities and local preparations. There is no submission client."""

import hashlib
import json

from flask import current_app
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from sqlalchemy.exc import IntegrityError

from app.catalog import CATEGORY_LABELS, SKILLS
from app.experience import experience_label
from app.models import DemoPreparation, ExternalVacancy, db
from app.recruitment import RecruitmentError

NOTICE_HI = "यह प्रदर्शन है। बाहरी कंपनी को कोई आवेदन नहीं भेजा गया है।"
NOTICE_EN = (
    "This is a demonstration. No application has been sent to an external employer."
)
PREPARED_STATUS = "Demo application prepared — not submitted externally"


def profile_snapshot(worker):
    # Deliberately omit phone, email, password and optional e-Shram number.
    return dict(
        name=worker.name,
        age=worker.age,
        skills=worker.get_skills_list(),
        location=worker.location,
        experience_months=worker.total_experience_months,
        preferred_domain=worker.preferred_domain,
    )


def assessment(vacancy, worker):
    data = vacancy.payload
    reasons, missing, score = [], [], 0
    if data.get("skill") in worker.get_skills_list():
        reasons.append("आपकी प्रोफ़ाइल का कौशल मिलता है: " + SKILLS[data["skill"]])
        score += 50
    elif data.get("skill"):
        missing.append("माँगा गया कौशल आपकी प्रोफ़ाइल में नहीं है।")
    else:
        missing.append("स्रोत से कौशल की स्पष्ट शर्त नहीं मिली; मूल विवरण जाँचें।")
    if data.get("location") == worker.location:
        reasons.append("आपके पसंद का शहर।")
        score += 30
    required = data.get("min_experience_months")
    if required is None:
        missing.append("अनुभव की शर्त स्रोत ने स्पष्ट नहीं दी।")
    elif (worker.total_experience_months or 0) >= required:
        reasons.append(
            f"अनुभव: आपके ठीक {worker.total_experience_months} महीने; शर्त {required} महीने।"
        )
        score += 5
    else:
        missing.append(f"कम से कम {required} महीने अनुभव चाहिए।")
    if not data.get("wage"):
        missing.append("वेतन नहीं बताया गया।")
    missing.extend(data.get("missing_information", []))
    missing.append("बाहरी आवेदन के दस्तावेज़ और दूसरी शर्तें जाँची नहीं गई हैं।")
    return dict(score=score, reasons=reasons, unmet=missing, eligible=False)


def card(vacancy, worker):
    data = dict(vacancy.payload)
    data.update(
        id=f"external:{vacancy.id}",
        external_id=vacancy.id,
        external=True,
        source=vacancy.source,
        demo=vacancy.is_demo,
        employment_category="formal_external",
        category_label=CATEGORY_LABELS["formal_external"],
        category_claim="प्रदर्शन श्रेणी। औपचारिकता और दस्तावेज़ सत्यापित नहीं हैं।"
        if vacancy.is_demo
        else "बोर्ड संचालक की घोषित श्रेणी; ShramLink ने औपचारिकता सत्यापित नहीं की है।",
        retrieved_at=vacancy.retrieved_at.isoformat() + "Z",
        match=assessment(vacancy, worker),
    )
    months = data.get("min_experience_months")
    data["experience_label"] = (
        experience_label(months) if months is not None else "नहीं बताया गया"
    )
    pay = (
        f"{data['wage']} रुपये प्रति {'महीना' if data.get('wage_unit') == 'month' else 'दिन'}"
        if data.get("wage")
        else "वेतन नहीं बताया गया"
    )
    data["spoken_summary"] = (
        f"बाहरी अवसर। {data['title']}। नियोक्ता {data['factory']}। जगह {data['location']}। {pay}। समय {data.get('shift') or 'नहीं बताया गया'}। अनुभव {data['experience_label']}। {NOTICE_HI}"
    )
    data["spoken_requirements"] = (
        f"स्रोत की शर्तें। {data.get('requirements') or 'मूल स्रोत पर विवरण जाँचें'}। {NOTICE_HI}"
    )
    return data


def available_cards(
    worker, skill=None, location=None, *, refresh=True, include_prepared=False
):
    mode = current_app.config["EFFECTIVE_JOB_SOURCE"]
    message = ""
    if mode == "integrated" and refresh:
        from app.job_feed import refresh_feed

        message = refresh_feed()
    elif current_app.config["JOB_SOURCE"] == "integrated":
        message = "बाहरी स्रोत तैयार नहीं है। नीचे अलग से चिह्नित प्रदर्शन अवसर हैं।"
    prepared = {
        r.vacancy_id for r in DemoPreparation.query.filter_by(laborer_id=worker.id)
    }
    query = ExternalVacancy.query.filter_by(active=True)
    if mode != "integrated":
        query = query.filter_by(is_demo=True)
    else:
        # Never surface stale opportunities from a previously configured board.
        query = query.filter(
            (ExternalVacancy.is_demo.is_(True))
            | (
                ExternalVacancy.source_key.startswith(
                    "greenhouse:" + current_app.config["GREENHOUSE_BOARD"] + ":",
                    autoescape=True,
                )
            )
        )
    rows = []
    for vacancy in query.all():
        if vacancy.id in prepared and not include_prepared:
            continue
        data = card(vacancy, worker)
        if include_prepared:
            data["prepared"] = vacancy.id in prepared
        if (
            skill
            and data.get("skill") != skill
            or location
            and data.get("location") != location
        ):
            continue
        rows.append(data)
    return sorted(
        rows, key=lambda d: (d["demo"], -d["match"]["score"], d["id"])
    ), message


def vacancy_for_preview(worker, vacancy_id):
    if not worker.profile_complete:
        raise RecruitmentError("पहले अपनी प्रोफ़ाइल पूरी करें।", 409)
    vacancy = db.session.get(ExternalVacancy, vacancy_id)
    if not vacancy or not vacancy.active:
        raise RecruitmentError("बाहरी अवसर अभी उपलब्ध नहीं है।", 404)
    if not vacancy.is_demo and (
        current_app.config["EFFECTIVE_JOB_SOURCE"] != "integrated"
        or not vacancy.source_key.startswith(
            "greenhouse:" + current_app.config["GREENHOUSE_BOARD"] + ":"
        )
    ):
        raise RecruitmentError("यह बाहरी स्रोत इस सत्र में उपलब्ध नहीं है।", 404)
    return vacancy


def digest(worker, vacancy):
    raw = json.dumps(
        [worker.id, profile_snapshot(worker), vacancy.id, vacancy.payload],
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha256(raw.encode()).hexdigest()


def signer():
    return URLSafeTimedSerializer(
        current_app.secret_key, salt="external-demo-review-v3"
    )


def preview(worker, vacancy):
    return dict(
        job=card(vacancy, worker),
        profile=profile_snapshot(worker),
        confirmation_token=signer().dumps(digest(worker, vacancy)),
        notice_hi=NOTICE_HI,
        notice_en=NOTICE_EN,
        status_label=PREPARED_STATUS,
    )


def prepare(worker, vacancy_id, data):
    vacancy = vacancy_for_preview(worker, vacancy_id)
    if data.get("confirmed") != "yes":
        raise RecruitmentError("पहले विवरण जाँचकर पुष्टि करें।")
    try:
        reviewed = signer().loads(data.get("confirmation_token", ""), max_age=900)
    except (BadSignature, SignatureExpired, TypeError):
        raise RecruitmentError("पुष्टि की अवधि पूरी हुई। विवरण फिर खोलें।", 409) from None
    if reviewed != digest(worker, vacancy):
        raise RecruitmentError("प्रोफ़ाइल या काम बदला है। नई जानकारी जाँचें।", 409)
    existing = DemoPreparation.query.filter_by(
        laborer_id=worker.id, vacancy_id=vacancy.id
    ).first()
    if existing:
        return existing
    record = DemoPreparation(
        laborer_id=worker.id,
        vacancy_id=vacancy.id,
        snapshot=dict(profile=profile_snapshot(worker), job=card(vacancy, worker)),
    )
    db.session.add(record)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        record = DemoPreparation.query.filter_by(
            laborer_id=worker.id, vacancy_id=vacancy.id
        ).first()
        if not record:
            raise
    return record

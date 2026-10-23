"""Read-only Greenhouse public Job Board adapter. No application POST exists.

Official contract: https://docs.greenhouse.io/job-board (checked 2026-10-23).
"""

import html
import re
import time
from datetime import timedelta
from html.parser import HTMLParser
from urllib.parse import urlsplit

from flask import current_app
from sqlalchemy.exc import IntegrityError

from app.models import ExternalVacancy, db
from app.network import request_json
from app.service_limits import consume, metric
from app.timeutils import utcnow

ROLE_WORDS = {
    "welder": r"\b(welder|welding operator)\b",
    "electrician": r"\belectrician\b",
    "helper": r"\b(factory helper|production helper|warehouse helper)\b",
    "loader": r"\b(loader|loading worker)\b",
    "painter": r"\b(industrial painter|painter)\b",
    "construction": r"\b(mason|construction worker)\b",
}
CITIES = [
    ("Greater Noida", r"\bgreater noida\b"),
    ("Noida", r"\bnoida\b"),
    ("Delhi", r"\b(new delhi|delhi)\b"),
    ("Gurugram", r"\b(gurugram|gurgaon)\b"),
    ("Faridabad", r"\bfaridabad\b"),
    ("Ghaziabad", r"\bghaziabad\b"),
]


class PlainText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts, self.blocked = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.blocked += 1
        if tag in ("p", "br", "li", "div", "h2", "h3"):
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.blocked = max(0, self.blocked - 1)

    def handle_data(self, data):
        if not self.blocked:
            self.parts.append(data)


def plain(value, maximum):
    if not isinstance(value, str):
        return ""
    parser = PlainText()
    parser.feed(html.unescape(value[:60000]))
    return " ".join(" ".join(parser.parts).split())[:maximum]


def normalize(row, employer):
    if not isinstance(row, dict) or type(row.get("id")) is not int or row["id"] < 1:
        return None
    title = plain(row.get("title"), 100)
    location = row.get("location")
    location = plain(location.get("name"), 200) if isinstance(location, dict) else ""
    city = next(
        (name for name, pattern in CITIES if re.search(pattern, location, re.I)), None
    )
    skill = next(
        (
            name
            for name, pattern in ROLE_WORDS.items()
            if re.search(pattern, title, re.I)
        ),
        None,
    )
    # Exact supported role titles only. Never turn a sales/engineering role into
    # an industrial skill match because its description mentions manufacturing.
    if not city or not skill:
        return None
    url = row.get("absolute_url", "")
    if not isinstance(url, str) or len(url) > 1000:
        return None
    parsed = urlsplit(url)
    if (
        parsed.scheme != "https"
        or parsed.hostname not in ("boards.greenhouse.io", "job-boards.greenhouse.io")
        or parsed.username
        or parsed.password
        or parsed.port
    ):
        return None
    requirements = plain(row.get("content"), 2000)
    return dict(
        provider_id=row["id"],
        title=title,
        factory=employer,
        location=city,
        source_location=location,
        skill=skill,
        wage=None,
        wage_unit=None,
        min_experience_months=None,
        shift=None,
        start_date=None,
        worksite_address=None,
        original_url=url,
        requirements=requirements or "मूल स्रोत पर शर्तें देखें।",
        missing_information=[
            "शिफ़्ट, तारीख और पूरा कार्यस्थल पता इस स्रोत में संरचित रूप में नहीं मिला।",
            "स्रोत का विवरण अंग्रेज़ी में हो सकता है। अंश छोटा किया जा सकता है; पूरा विवरण मूल लिंक पर देखें।",
        ],
    )


def refresh_feed():
    c = current_app.config
    board = c["GREENHOUSE_BOARD"]
    prefix = f"greenhouse:{board}:"
    now = utcnow()
    # Expire stale visibility before looking in the cache.
    ExternalVacancy.query.filter(
        ExternalVacancy.source_key.startswith(prefix, autoescape=True),
        ExternalVacancy.retrieved_at < now - timedelta(hours=24),
    ).update({"active": False})
    db.session.commit()
    key = f"feed:{board}:{int(time.time()) // 900}"
    if consume(key, 1) and consume(f"feed-day:{board}:{now.date()}", 48):
        try:
            result = request_json(
                f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs?content=true",
                timeout=5,
            )
            if (
                not isinstance(result, dict)
                or not isinstance(result.get("jobs"), list)
                or len(result["jobs"]) > 2000
            ):
                raise ValueError("Invalid job board response.")
            rows = [normalize(row, c["GREENHOUSE_EMPLOYER"]) for row in result["jobs"]]
            # Only a fully parsed successful response can retire prior vacancies.
            ExternalVacancy.query.filter(
                ExternalVacancy.source_key.startswith(prefix, autoescape=True)
            ).update({"active": False})
            for data in filter(None, rows):
                source_key = prefix + str(data.pop("provider_id"))
                vacancy = ExternalVacancy.query.filter_by(source_key=source_key).first()
                if not vacancy:
                    vacancy = ExternalVacancy(
                        source_key=source_key,
                        source="Greenhouse · " + board,
                        is_demo=False,
                    )
                    db.session.add(vacancy)
                vacancy.payload, vacancy.active, vacancy.retrieved_at = data, True, now
            db.session.commit()
            metric("feed_success")
        except (OSError, ValueError, TypeError, IntegrityError):
            db.session.rollback()
            metric("feed_error")
            return "बाहरी स्रोत से अभी संपर्क नहीं हुआ। पुरानी जानकारी हो तो प्राप्त समय साथ दिखेगा। DEMO अवसर अलग चिह्नित हैं।"
    live = ExternalVacancy.query.filter(
        ExternalVacancy.source_key.startswith(prefix, autoescape=True), ExternalVacancy.active.is_(True)
    ).count()
    if not live:
        return "इस स्रोत में दिल्ली–NCR के समर्थित औद्योगिक कौशलों का कोई बाहरी अवसर अभी उपलब्ध नहीं है। DEMO अवसर काल्पनिक हैं।"
    return "बाहरी स्रोत की सहेजी जानकारी दिख रही है; प्राप्त समय हर कार्ड पर है। बाहर आवेदन भेजना उपलब्ध नहीं है।"

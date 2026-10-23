"""Worker-safe explanations; no database paths, administration or private diagnostics."""

from flask import current_app, url_for

from app.models import ExternalVacancy, Job


def state(rows, external, all_rows, all_external, filters_active):
    eligible = sum(match["eligible"] for _, match, applied in rows if not applied)
    cards = [r for r in rows if not r[2]]
    external_cards = [r for r in external if not r.get("prepared")]
    code = "ready"
    if not cards and not external_cards:
        if rows or external:
            code = "reviewed"
        elif filters_active and (all_rows or all_external):
            code = "filters"
        elif not Job.query.first() and not ExternalVacancy.query.first():
            code = (
                "uninitialized"
                if current_app.config["SHRAMLINK_DEMO"]
                else "no_vacancies"
            )
        else:
            code = "unavailable"
    elif cards and not eligible:
        code = "no_eligible"
    messages = {
        "ready": (
            "अभी कोई नया काम नहीं बचा।",
            "मेरे आवेदन में स्थिति देखें या बाद में फिर कोशिश करें।",
            "मेरे आवेदन",
            "dashboard",
        ),
        "uninitialized": (
            "प्रदर्शन के काम अभी तैयार नहीं हैं।",
            "आयोजन टीम से प्रदर्शन के काम तैयार करने को कहें। आपकी प्रोफ़ाइल सेव है।",
            "फिर देखें",
            "reload",
        ),
        "no_vacancies": (
            "अभी कोई नौकरी नहीं आई है।",
            "नया काम आने पर यहाँ दिखेगा। बाद में फिर देखें।",
            "फिर देखें",
            "reload",
        ),
        "filters": (
            "इन फ़िल्टर में काम नहीं मिला।",
            "शहर या कौशल के फ़िल्टर हटाकर उपलब्ध काम देखें।",
            "सभी काम देखें",
            "clear",
        ),
        "reviewed": (
            "इन कामों पर आप पहले कार्रवाई कर चुके हैं।",
            "आवेदन और बाहरी प्रदर्शन तैयारी की स्थिति मेरे आवेदन में देखें।",
            "मेरे आवेदन",
            "dashboard",
        ),
        "unavailable": (
            "अभी कोई काम आवेदन नहीं ले रहा है।",
            "काम की तारीख बीत गई हो सकती है या जगह भर गई है। बाद में फिर देखें।",
            "फिर देखें",
            "reload",
        ),
        "no_eligible": (
            "सीधे आवेदन की शर्तें अभी पूरी नहीं हैं।",
            "नीचे काम की शर्तें देखें। कौशल और अनुभव सही भरे हैं तो उन्हें बदलने की जरूरत नहीं है। बाहरी तैयारी केवल प्रदर्शन है।",
            "प्रोफ़ाइल जाँचें",
            "profile",
        ),
    }
    title, message, label, action = messages[code]
    links = {
        "dashboard": url_for("dashboard.laborer_dashboard", _anchor="applications"),
        "profile": url_for("dashboard.onboarding"),
        "reload": url_for("dashboard.discovery"),
        "clear": url_for("dashboard.discovery"),
    }
    return dict(
        code=code, title=title, message=message, label=label, href=links[action]
    )

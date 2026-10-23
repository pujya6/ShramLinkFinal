"""Exact months for eligibility; completed years only for display at 24+ months."""


def months_or_legacy(months, years):
    if months is not None:
        return months
    return years * 12 if years is not None else None


def experience_label(months, language="hi"):
    if months is None:
        return "नहीं बताया" if language == "hi" else "Not provided"
    value = months if months < 24 else months // 12
    if language == "hi":
        return f"{value} {'महीने' if months < 24 else 'वर्ष'}"
    unit = "month" if months < 24 else "year"
    return f"{value} {unit}{'' if value == 1 else 's'}"

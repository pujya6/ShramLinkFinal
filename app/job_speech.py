"""Deterministic Hindi descriptions of stored vacancy data; no inferred facts."""

import re

from app.catalog import LOCATIONS, SKILLS

NUMBERS = "शून्य एक दो तीन चार पाँच छह सात आठ नौ दस ग्यारह बारह तेरह चौदह पंद्रह सोलह सत्रह अठारह उन्नीस बीस इक्कीस बाईस तेईस चौबीस पच्चीस छब्बीस सत्ताईस अट्ठाईस उनतीस तीस इकतीस बत्तीस तैंतीस चौंतीस पैंतीस छत्तीस सैंतीस अड़तीस उनतालीस चालीस इकतालीस बयालीस तैंतालीस चवालीस पैंतालीस छियालीस सैंतालीस अड़तालीस उनचास पचास इक्यावन बावन तिरपन चौवन पचपन छप्पन सत्तावन अट्ठावन उनसठ साठ इकसठ बासठ तिरसठ चौंसठ पैंसठ छियासठ सड़सठ अड़सठ उनहत्तर सत्तर इकहत्तर बहत्तर तिहत्तर चौहत्तर पचहत्तर छिहत्तर सतहत्तर अठहत्तर उनासी अस्सी इक्यासी बयासी तिरासी चौरासी पचासी छियासी सत्तासी अट्ठासी नवासी नब्बे इक्यानवे बानवे तिरानवे चौरानवे पंचानवे छियानवे सत्तानवे अट्ठानवे निन्यानवे".split()
MONTHS = "जनवरी फ़रवरी मार्च अप्रैल मई जून जुलाई अगस्त सितंबर अक्टूबर नवंबर दिसंबर".split()


def hindi_number(value):
    if value < 100:
        return NUMBERS[value]
    for scale, label in [(100000, "लाख"), (1000, "हज़ार"), (100, "सौ")]:
        if value >= scale:
            head, rest = divmod(value, scale)
            return f"{hindi_number(head)} {label}" + (
                f" {hindi_number(rest)}" if rest else ""
            )


def clock(hour, minute):
    period = (
        "सुबह"
        if 5 <= hour < 12
        else "दोपहर"
        if 12 <= hour < 17
        else "शाम"
        if 17 <= hour < 20
        else "रात"
    )
    return f"{period} {hindi_number(hour % 12 or 12)} बजे" + (
        f" {hindi_number(minute)} मिनट" if minute else ""
    )


def shift_speech(value):
    match = re.fullmatch(r"\s*(\d{1,2}):(\d{2})\s*[–—-]\s*(\d{1,2}):(\d{2})\s*", value)
    if match:
        h1, m1, h2, m2 = map(int, match.groups())
        if h1 < 24 and h2 < 24 and m1 < 60 and m2 < 60:
            return f"{clock(h1, m1)} से {clock(h2, m2)} तक"
    return value  # Never invent a translation of employer-entered timing.


def job_summary(job):
    months = job.required_experience_months
    duration = (
        f"{hindi_number(months)} महीने"
        if months < 24
        else f"{hindi_number(months // 12)} साल"
    )
    if months >= 24 and months % 12:
        duration += f" {hindi_number(months % 12)} महीने"
    condition = (job.description or "").split("\n")[0]
    if len(condition) > 180:
        condition = condition[:180].rsplit(" ", 1)[0] + "… बाकी शर्तें अलग से सुनें"
    return (
        f"यह {SKILLS[job.skill.value].split(' / ')[0]} का काम है। "
        f"काम का नाम {job.title}। नियोक्ता {job.manager.factory_name}। "
        f"जगह {LOCATIONS.get(job.location, job.location).split(' / ')[0]}। "
        f"{'हर महीने' if job.pay_unit == 'month' else 'रोज़'} {hindi_number(job.pay_amount)} रुपये मिलेंगे। "
        f"काम {shift_speech(job.shift_timing)}। "
        f"तारीख {hindi_number(job.start_date.day)} {MONTHS[job.start_date.month - 1]} {job.start_date.year}। "
        f"कम से कम {duration} का अनुभव चाहिए। "
        f"नियोक्ता की शर्तें। {condition}। पूरी शर्तें अलग से सुन सकते हैं। "
        "जानकारी नियोक्ता ने दी है। चयन की गारंटी नहीं है।"
    )

"""Small, explicit vocabulary shared by validation, matching and templates."""

SKILLS = {
    "welder": "वेल्डर / Welder",
    "construction": "निर्माण मिस्त्री / Construction",
    "loader": "लोडर / Loader",
    "electrician": "बिजली मिस्त्री / Electrician",
    "painter": "पेंटर / Painter",
    "helper": "हेल्पर / Helper",
}
DOMAINS = {
    "manufacturing": "कारखाना / Manufacturing",
    "construction": "निर्माण / Construction",
    "warehouse": "गोदाम / Warehouse",
    "maintenance": "रखरखाव / Maintenance",
}
LOCATIONS = {
    "Delhi": "दिल्ली / Delhi",
    "Noida": "नोएडा / Noida",
    "Greater Noida": "ग्रेटर नोएडा / Greater Noida",
    "Ghaziabad": "गाज़ियाबाद / Ghaziabad",
    "Faridabad": "फ़रीदाबाद / Faridabad",
    "Gurugram": "गुरुग्राम / Gurugram",
}
STATUS_LABELS = {
    "applied": "आवेदन भेजा / Applied",
    "shortlisted": "विचाराधीन / Shortlisted",
    "selected": "आप चुने गए / Selected",
    "rejected": "चयन नहीं हुआ / Not selected",
    "withdrawn": "वापस लिया / Withdrawn",
}


EMPLOYMENT_CATEGORIES = {
    "direct_informal": "अनौपचारिक · सीधा / Informal · direct",
    "direct_formal": "औपचारिक · सीधा / Formal · direct",
}
CATEGORY_LABELS = dict(
    EMPLOYMENT_CATEGORIES,
    direct_unspecified="सीधा · प्रकार नहीं बताया / Direct · category unspecified",
    formal_external="औपचारिक · बाहरी / Formal · external",
)
WAGE_UNITS = {"day": "प्रति दिन / Per day", "month": "प्रति महीना / Per month"}

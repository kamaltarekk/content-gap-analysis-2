SALES_ELEMENTS = [
    ("SE01", "core", "trigger_pain"),
    ("SE02", "core", "claim"),
    ("SE03", "core", "gain"),
    ("SE04", "core", "logistics"),
    ("SE05", "intellect", "calculation"),
    ("SE06", "intellect", "objection_handler"),
    ("SE07", "intellect", "reason"),
    ("SE08", "intellect", "comparison"),
    ("SE09", "trust", "social_proof"),
    ("SE10", "trust", "identity_proof"),
    ("SE11", "trust", "authority_proof"),
    ("SE12", "trust", "fear_free_promise"),
    ("SE13", "trust", "claim_proof"),
    ("SE14", "instinct", "urgency"),
    ("SE15", "instinct", "scarcity"),
    ("SE16", "instinct", "reciprocity"),
    ("SE17", "instinct", "offer"),
]

# SE01 (trigger_pain) is deliberately unresolved until the user settles its semantics
# (domain rule 10). It never receives a numeric score.
UNRESOLVED_ELEMENTS: set[str] = {"SE01"}

ELEMENT_IDS: list[str] = [element_id for element_id, _family, _key in SALES_ELEMENTS]
KEY_BY_ID: dict[str, str] = {element_id: key for element_id, _family, key in SALES_ELEMENTS}
FAMILY_BY_ID: dict[str, str] = {element_id: family for element_id, family, _key in SALES_ELEMENTS}

# Evidence categories (domain rule 8) map to the canonical element they inform.
CATEGORY_TO_ELEMENT: dict[str, str] = {
    "claim": "SE02",
    "social_proof": "SE09",
    "claim_proof": "SE13",
}
ELEMENT_TO_CATEGORY: dict[str, str] = {v: k for k, v in CATEGORY_TO_ELEMENT.items()}

KEYWORDS = {
    "claim": ["best", "quality", "safe", "premium", "الأفضل", "جودة", "آمن"],
    "gain": ["benefit", "save", "comfort", "يوفر", "راحة", "ميزة"],
    "logistics": ["shipping", "delivery", "return", "refund", "شحن", "توصيل", "استرجاع"],
    "calculation": ["calculator", "%", "cost", "price per", "حاسبة", "تكلفة"],
    "objection_handler": ["faq", "question", "worry", "اعتراض", "سؤال", "قلق"],
    "reason": ["because", "why", "لأن", "ليه"],
    "comparison": ["compare", "versus", "vs", "مقارنة", "بدل"],
    "social_proof": ["review", "testimonial", "customers", "تقييم", "عملاء"],
    "identity_proof": ["branches", "founded", "address", "فروع", "تأسس", "عنوان"],
    "authority_proof": ["certified", "expert", "award", "معتمد", "خبير", "جائزة"],
    "fear_free_promise": ["guarantee", "return", "risk free", "ضمان", "استرجاع"],
    "claim_proof": ["test report", "certificate", "study", "تقرير", "شهادة", "دراسة"],
    "urgency": ["today", "ends", "limited time", "اليوم", "ينتهي"],
    "scarcity": ["only", "left", "limited stock", "متبقي", "كمية محدودة"],
    "reciprocity": ["free guide", "gift", "هدية", "دليل مجاني"],
    "offer": ["discount", "sale", "free shipping", "خصم", "عرض", "شحن مجاني"],
}

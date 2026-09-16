import pandas as pd
import re

INTENTS = [
    "Playback/Technical Bug", "Account Access", "Billing/Subscription",
    "Content Availability", "Feature Request/Complaint", "Service Outage", "Other"
]

# ---- Trivial baseline ----
def trivial_predict(text, thread_context=""):
    return {
        "intent": "Playback/Technical Bug",  # most frequent class, hardcoded
        "reply": "Thanks for reaching out! Please DM us so we can look into this.",
        "escalate": False,
        "escalate_reason": "Trivial baseline never escalates"
    }

# ---- Simple baseline: keyword rules + nearest-neighbor reply ----
KEYWORD_RULES = [
    ("Service Outage", ("down", "outage", "server")),
    ("Account Access", ("login", "log in", "password", "2fa", "locked out")),
    ("Billing/Subscription", ("charge", "charged", "refund", "subscription", "billing")),
    ("Content Availability", ("missing", "unavailable", "removed", "region")),
    ("Feature Request/Complaint", ("please add", "wish", "feature", "why did you remove")),
    ("Playback/Technical Bug", ("crash", "skip", "freeze", "bug", "error")),
]

def simple_predict(text, thread_context="", knowledge_base=None):
    text_lower = str(text).lower()
    intent = "Other"
    for label, keywords in KEYWORD_RULES:
        if any(kw in text_lower for kw in keywords):
            intent = label
            break

    escalate = intent == "Billing/Subscription" and ("refund" in text_lower or "$" in text_lower)

    reply = "Thanks for letting us know, we'll look into this."
    if knowledge_base is not None and len(knowledge_base) > 0:
        # crude nearest neighbor: find a KB row sharing the most words
        text_words = set(text_lower.split())
        best_overlap, best_reply = 0, reply
        for _, row in knowledge_base.iterrows():
            kb_words = set(str(row['customer_message']).lower().split())
            overlap = len(text_words & kb_words)
            if overlap > best_overlap:
                best_overlap, best_reply = overlap, row['brand_reply']
        reply = best_reply

    return {
        "intent": intent,
        "reply": reply,
        "escalate": escalate,
        "escalate_reason": "Contains refund/dollar language" if escalate else "No trigger keywords matched"
    }


def offline_predict(text, thread_context="", knowledge_base=None):
    return simple_predict(text, thread_context, knowledge_base)
import pandas as pd
import os
import re
import time
from dotenv import load_dotenv

load_dotenv()

triples_df = pd.read_csv("data/processed/spotify_triples.csv")
taxonomy_sample = pd.read_csv("report/taxonomy_validation_sample.csv")

# Do not sample the same customer message more than once.
triples_df = triples_df.drop_duplicates(subset=["customer_message"]).reset_index(drop=True)

print("Total triples available:", len(triples_df))
print("Already-seen taxonomy sample size:", len(taxonomy_sample))

USE_GEMINI = os.getenv("USE_GEMINI", "0").lower() in {"1", "true", "yes"}
client = None
if USE_GEMINI:
    from google import genai

    client = genai.Client()

TAXONOMY_DEFINITIONS = """
1. Playback/Technical Bug - app crashes, skipping, freezing, broken features
2. Account Access - login, password, 2FA, lockout issues
3. Billing/Subscription - charges, refunds, plan/subscription issues
4. Content Availability - missing songs/podcasts, licensing/region issues
5. Feature Request/Complaint - wants a feature, dislikes a product decision
6. Service Outage - widespread known issue, "is it down for everyone"
7. Other - anything that doesn't clearly fit above
"""

def local_tag_intent(text):
    """Provide a no-API baseline when Gemini is unavailable or quota-limited."""
    text = str(text).lower()
    keyword_groups = [
        ("Service Outage", ("down", "outage", "not working for everyone", "server")),
        ("Account Access", ("login", "log in", "password", "2fa", "locked out", "sign in")),
        ("Billing/Subscription", ("charge", "charged", "refund", "subscription", "premium", "billing")),
        ("Content Availability", ("missing", "unavailable", "can't find", "cannot find", "removed", "region")),
        ("Feature Request/Complaint", ("please add", "wish", "feature", "why did you remove", "hate the new")),
        ("Playback/Technical Bug", ("crash", "crashes", "skip", "skipping", "freeze", "freezing", "bug", "error")),
    ]
    for category, keywords in keyword_groups:
        if any(re.search(rf"\b{re.escape(keyword)}\b", text) for keyword in keywords):
            return category
    return "Other"


def rough_tag_intent(text):
    global USE_GEMINI

    if not USE_GEMINI:
        return local_tag_intent(text)

    prompt = f"""Classify this customer support tweet into exactly one category.

{TAXONOMY_DEFINITIONS}

Tweet: "{text}"

Respond with ONLY the category name, nothing else."""

    try:
        response = client.interactions.create(
            model="gemini-3.5-flash",
            input=prompt
        )
        return response.output_text.strip()
    except Exception as error:
        error_text = str(error).lower()
        if "quota" not in error_text and "rate limit" not in error_text and "429" not in error_text:
            raise
        print("Gemini quota/rate limit reached; using the local classifier for the remaining rows.")
        USE_GEMINI = False
        return local_tag_intent(text)

# Local tagging is free and can use the full dataset; Gemini remains bounded by default.
default_sample_size = len(triples_df) if not USE_GEMINI else 500
sample_size = min(int(os.getenv("TAG_SAMPLE_SIZE", str(default_sample_size))), len(triples_df))
pool_for_tagging = triples_df.sample(n=sample_size, random_state=1).reset_index(drop=True)  # different seed than taxonomy sample
tags = []
for i, row in pool_for_tagging.iterrows():
    tag = rough_tag_intent(row['customer_message'])
    tags.append(tag)
    if i % 50 == 0:
        print(f"Tagged {i}/{len(pool_for_tagging)}")
    if USE_GEMINI:
        time.sleep(12.5)  # Restrict to ~4.8 requests per minute to stay safe

pool_for_tagging['rough_intent'] = tags
print(pool_for_tagging['rough_intent'].value_counts())

already_seen_texts = set(taxonomy_sample['text'].tolist())

# stratified sampling with a minimum floor per class
MIN_PER_CLASS = 30
TARGET_TOTAL = 200

stratified_samples = []

for intent, group in pool_for_tagging.groupby('rough_intent'):
    # exclude anything already seen in taxonomy design
    group = group[~group['customer_message'].isin(already_seen_texts)]

    n_to_take = min(MIN_PER_CLASS, len(group))
    if n_to_take < MIN_PER_CLASS:
        print(f"WARNING: '{intent}' only has {len(group)} available after exclusion, below target of {MIN_PER_CLASS}")

    sampled = group.sample(n=n_to_take, random_state=2)
    stratified_samples.append(sampled)

golden_pool = pd.concat(stratified_samples, ignore_index=True)
print("Golden set pool size so far:", len(golden_pool))
print(golden_pool['rough_intent'].value_counts())

if len(golden_pool) > TARGET_TOTAL:
    golden_pool = golden_pool.sample(n=TARGET_TOTAL, random_state=3)

print("Final golden set pool size:", len(golden_pool))


# ============================================================
# STEP 3: Hand-labeling loop (with accept/correct shortcuts)
# ============================================================

import json

# ---- Escalation rule suggestion (draft rules from Phase 3, as a starting guess) ----
def suggest_escalate(text, intent):
    text_lower = str(text).lower()

    if intent == "Billing/Subscription" and any(
        kw in text_lower for kw in ["refund", "$", "charged twice", "money back"]
    ):
        return True, "Billing issue mentions refund/charge — financial liability, don't auto-approve"

    if intent == "Account Access" and any(
        kw in text_lower for kw in ["hacked", "someone else", "unauthorized", "not me"]
    ):
        return True, "Possible account compromise — needs human verification"

    if any(kw in text_lower for kw in ["lawyer", "cancelling", "cancel my", "furious", "unacceptable"]):
        return True, "Anger/threat language detected — escalate regardless of intent"

    return False, "No escalation trigger matched — safe to auto-handle"


# ---- Resume support: pick up where you left off if the script was stopped ----
PROGRESS_FILE = os.getenv("PROGRESS_FILE", "eval/golden_set_in_progress.csv")

if os.path.exists(PROGRESS_FILE) and os.path.getsize(PROGRESS_FILE) > 1:
    golden_records = pd.read_csv(PROGRESS_FILE).to_dict('records')
    already_labeled_texts = set(r['text'] for r in golden_records)
    remaining_pool = golden_pool[~golden_pool['customer_message'].isin(already_labeled_texts)].reset_index(drop=True)
    print(f"\nResuming: {len(golden_records)} already labeled, {len(remaining_pool)} remaining")
else:
    golden_records = []
    remaining_pool = golden_pool.reset_index(drop=True)
    print(f"\nStarting fresh: {len(remaining_pool)} examples to label")


# ---- Main labeling loop ----
VALID_INTENTS = {
    "1": "Playback/Technical Bug",
    "2": "Account Access",
    "3": "Billing/Subscription",
    "4": "Content Availability",
    "5": "Feature Request/Complaint",
    "6": "Service Outage",
    "7": "Other",
}
BOT_MODE = os.getenv("BOT_MODE", "1").lower() in {"1", "true", "yes"}

print("\n" + "=" * 70)
print("LABELING INSTRUCTIONS")
print("=" * 70)
print("For intent: press Enter to accept the suggested tag, or type a number 1-7 to override:")
for k, v in VALID_INTENTS.items():
    print(f"  {k} = {v}")
print("For escalate: press Enter to accept the suggested decision, or type 'y'/'n' to override")
if BOT_MODE:
    print("BOT_MODE enabled: GoldenSetBot will annotate each sample automatically.\n")
else:
    print("Type 'quit' at any prompt to stop and save progress\n")

for idx, row in remaining_pool.iterrows():
    total_done = len(golden_records)
    customer_message = row.get('customer_message', row.get('text_customer', ''))
    thread_context = row.get('thread_context', row.get('text_customer', ''))
    brand_reply = row.get('brand_reply', row.get('text_brand', ''))
    if pd.isna(customer_message):
        customer_message = ''
    if pd.isna(thread_context):
        thread_context = ''
    if pd.isna(brand_reply):
        brand_reply = ''
    print(f"\n{'='*70}")
    print(f"[{total_done + 1}/{len(golden_pool)}]")
    print(f"Customer message: {customer_message}")
    print(f"Thread context: {thread_context}")
    print(f"Actual historical brand reply: {brand_reply}")

    suggested_intent = row['rough_intent']
    suggested_escalate, suggested_reason = suggest_escalate(customer_message, suggested_intent)

    if BOT_MODE:
        gold_intent = suggested_intent
    else:
        print(f"\nSuggested intent: {suggested_intent}")
        intent_input = input("Accept? [Enter] or type 1-7 to override, 'quit' to stop: ").strip()

        if intent_input.lower() == 'quit':
            print("Stopping. Progress saved.")
            break

        if intent_input == "":
            gold_intent = suggested_intent
        elif intent_input in VALID_INTENTS:
            gold_intent = VALID_INTENTS[intent_input]
        else:
            gold_intent = intent_input

    if BOT_MODE:
        gold_escalate = suggested_escalate
        gold_escalate_reason = suggested_reason
        reply_reference = brand_reply or "No historical brand reply available."
    else:
        print(f"\nSuggested escalate: {suggested_escalate} ({suggested_reason})")
        escalate_input = input("Accept? [Enter]=accept, 'y'=yes escalate, 'n'=no escalate, 'quit' to stop: ").strip().lower()

        if escalate_input == 'quit':
            print("Stopping. Progress saved.")
            break

        if escalate_input == "":
            gold_escalate = suggested_escalate
            gold_escalate_reason = suggested_reason
        elif escalate_input == 'y':
            gold_escalate = True
            gold_escalate_reason = input("Reason for escalating: ").strip()
        elif escalate_input == 'n':
            gold_escalate = False
            gold_escalate_reason = input("Reason for NOT escalating: ").strip()
        else:
            gold_escalate = suggested_escalate
            gold_escalate_reason = suggested_reason

        reply_reference = input("Reference reply or key facts (required, no default): ").strip()
        if reply_reference.lower() == 'quit':
            print("Stopping. Progress saved.")
            break

    golden_records.append({
        'id': f"golden_{len(golden_records)+1:03d}",
        'text': customer_message,
        'thread_context': thread_context,
        'actual_historical_reply': brand_reply,
        'gold_intent': gold_intent,
        'gold_reply_reference': reply_reference,
        'gold_escalate': gold_escalate,
        'gold_escalate_reason': gold_escalate_reason,
    })

    pd.DataFrame(golden_records).to_csv(PROGRESS_FILE, index=False)
    print(f"\n--- Progress saved ({len(golden_records)} done) ---")

# always save at the end too, even if the loop finished naturally or was quit
pd.DataFrame(golden_records).to_csv(PROGRESS_FILE, index=False)
print(f"\nSession ended. Total labeled so far: {len(golden_records)}")


# ============================================================
# STEP 6: Save final golden set (only meaningful once labeling is complete)
# ============================================================

if len(golden_records) >= 150:
    final_golden_df = pd.DataFrame(golden_records)
    final_golden_df = final_golden_df[[
        'id', 'text', 'thread_context', 'gold_intent',
        'gold_reply_reference', 'gold_escalate', 'gold_escalate_reason'
    ]]
    os.makedirs("eval", exist_ok=True)
    final_golden_df.to_csv("eval/golden_set.csv", index=False)
    print(f"\nFinal golden set saved: {len(final_golden_df)} examples")
    print(final_golden_df['gold_intent'].value_counts())

    # Produce a focused review queue instead of requiring manual review of every row.
    review_rows = []
    for _, record in final_golden_df.iterrows():
        text = str(record['text']).lower()
        reasons = []
        if record['gold_intent'] == 'Other':
            reasons.append('Other label needs semantic review')
        if record['gold_escalate'] and record['gold_intent'] not in {
            'Account Access', 'Billing/Subscription'
        }:
            reasons.append('Escalation outside account/billing categories')
        if sum(keyword in text for keyword in ['login', 'password', 'charge', 'refund', 'missing', 'crash', 'skip', 'down']) > 1:
            reasons.append('Multiple issue signals in message')
        if reasons:
            review_rows.append({
                'id': record['id'],
                'text': record['text'],
                'suggested_intent': record['gold_intent'],
                'suggested_escalate': record['gold_escalate'],
                'review_reason': '; '.join(reasons),
            })
    pd.DataFrame(review_rows).to_csv('eval/golden_set_review.csv', index=False)
    print(f"Review queue saved: {len(review_rows)} rows in eval/golden_set_review.csv")
else:
    print(f"\nOnly {len(golden_records)} labeled so far — need at least 150 before finalizing.")
    print("Re-run this script to resume labeling from where you left off.")
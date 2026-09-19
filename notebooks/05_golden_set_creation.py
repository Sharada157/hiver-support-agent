import sys
import os
import re
import time
import json
import pandas as pd
from dotenv import load_dotenv
from google import genai

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

triples_df = pd.read_csv("data/processed/spotify_triples.csv")
output_path = "data/processed/rough_intent_tagged.csv"
os.makedirs("data/processed", exist_ok=True)

# 1. Initialize or Load Progress Data Cleanly
if os.path.exists(output_path):
    pool_for_tagging = pd.read_csv(output_path)
    # Ensure column exists and handle empty strings/NaN consistently
    if 'rough_intent' not in pool_for_tagging.columns:
        pool_for_tagging['rough_intent'] = None
    pool_for_tagging['rough_intent'] = pool_for_tagging['rough_intent'].astype(str).str.strip().replace({'nan': None, 'None': None, '': None})
    print(f"Loaded existing progress file. Rows already tagged: {pool_for_tagging['rough_intent'].notna().sum()}/{len(pool_for_tagging)}")
else:
    pool_for_tagging = triples_df.sample(n=500, random_state=1).reset_index(drop=True)
    pool_for_tagging['rough_intent'] = None
    print("Created new sample pool of 500 rows for tagging.")

# Check if we are already completely done
if pool_for_tagging['rough_intent'].notna().all():
    print("\n All 500 rows are already tagged! Nothing to do.")
    print("\n--- Tagging Distribution ---")
    print(pool_for_tagging['rough_intent'].value_counts())
    sys.exit(0)

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

def batch_tag_intents(batch_data, max_retries=5):
    # Formulate a structured payload to get clean JSON records back
    items_prompt = ""
    for idx, text in batch_data:
        items_prompt += f"ID {idx}: {text}\n"

    prompt = f"""Classify these customer support tweets into exactly one category per item.
    
Taxonomy options:
{TAXONOMY_DEFINITIONS}

Input Data:
{items_prompt}

Respond strictly with a valid JSON object matching this structure, without markdown wrapping:
{{
  "results": [
    {{"id": ID_NUMBER, "category": "CATEGORY_NAME"}},
    ...
  ]
}}"""

    for attempt in range(max_retries):
        try:
            response = client.interactions.create(model="gemini-3.6-flash", input=prompt)
            text_result = getattr(response, 'output_text', None) or getattr(response, 'text', None)
            
            # Clean text boundaries if model yields markdown blocks
            clean_json = re.sub(r'^```json\s*|```$', '', str(text_result).strip(), flags=re.MULTILINE)
            parsed = json.loads(clean_json)
            
            # Convert response list back to a digestible dictionary mapping
            return {int(item['id']): item['category'] for item in parsed['results']}
            
        except Exception as e:
            err_msg = str(e).lower()
            if any(k in err_msg for k in ["429", "quota", "too_many_requests", "exhausted"]):
                wait_time = 30.0
                match = re.search(r'retry in (\d+\.?\d*)s', err_msg)
                if match:
                    wait_time = float(match.group(1)) + 3.0
                print(f"[RATE LIMIT] Hit rate limit during batch. Sleeping {wait_time:.1f}s (Attempt {attempt+1}/{max_retries})...")
                time.sleep(wait_time)
            else:
                print(f"[API ERROR] {e}. Retrying batch in 10s...")
                time.sleep(10.0)
                
    return {}

# 4. Processing Phase in Batches of 20
BATCH_SIZE = 20
pending_items = []

print("\nStarting batch rough intent tagging...")

for i, row in pool_for_tagging.iterrows():
    if pd.isna(row['rough_intent']):
        pending_items.append((i, row['customer_message']))
        
    # Process when batch size is reached or at the very end of dataframe
    if len(pending_items) == BATCH_SIZE or (i == len(pool_for_tagging) - 1 and pending_items):
        print(f"Processing a batch of {len(pending_items)} items...")
        
        tagged_batch = batch_tag_intents(pending_items)
        
        # Save results back directly to target dataframe rows
        for idx, tag in tagged_batch.items():
            pool_for_tagging.at[idx, 'rough_intent'] = tag
            
        pool_for_tagging.to_csv(output_path, index=False)
        print(f"Progress checkpoint saved. Total tagged: {pool_for_tagging['rough_intent'].notna().sum()}/{len(pool_for_tagging)}")
        
        pending_items = []
        # Free Tier safety delay: 15s between batch bursts ensures safe pacing
        time.sleep(15.0)

print("\n--- Tagging Distribution ---")
print(pool_for_tagging['rough_intent'].value_counts())

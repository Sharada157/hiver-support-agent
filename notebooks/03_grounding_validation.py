import pandas as pd
import re

print("Loading dataset and building indices...")
df = pd.read_csv("data/raw/twcs/twcs.csv")
df['created_at'] = pd.to_datetime(df['created_at'], format='%a %b %d %H:%M:%S +0000 %Y')

# Target brands to test and cross-verify
BRANDS = ["SpotifyCares", "AppleSupport", "AmazonHelp"]

# Compile pattern rules for cleaner classification
dm_pattern = re.compile(r'\bdm\b|\bdirect message\b|\bd\.m\.\b|\bprivate message\b', re.IGNORECASE)
closing_pattern = re.compile(r'\bglad to hear\b|\bhappy to help\b|\bhave a great day\b|\bkeep us posted\b|\byou\'re welcome\b|\bthanks for letting us know\b', re.IGNORECASE)

def classify_reply_three_types(text):
    text_lower = str(text).lower()
    word_count = len(text_lower.split())
    
    # 1. Look for explicit instructions pushing the user to another channel
    if dm_pattern.search(text_lower) and word_count < 28:
        return "Type 2: Generic DM Redirect"
        
    # 2. Look for quick pleasantries or signs of a resolved case
    elif closing_pattern.search(text_lower) and word_count < 15:
        return "Type 3: Conversational Closing"
        
    # 3. Default to detailed troubleshooting support
    else:
        return "Type 1: Substantive Help"

# Process each target brand to view distribution splits
for brand in BRANDS:
    brand_df = df[df['author_id'] == brand].copy()
    
    # Take a statistically relevant sample size of 60 records per brand
    sample_df = brand_df.sample(n=60, random_state=42).copy()
    sample_df['grounding_type'] = sample_df['text'].apply(classify_reply_three_types)
    
    print(f"\n==========================================")
    print(f"BRAND METRICS: {brand}")
    print(f"==========================================")
    print(sample_df['grounding_type'].value_counts())
    
    # Output detailed context logs for human review and validation
    for g_type in ["Type 1: Substantive Help", "Type 2: Generic DM Redirect", "Type 3: Conversational Closing"]:
        sub_samples = sample_df[sample_df['grounding_type'] == g_type]
        print(f"\n--- Verified Samples for {g_type} (Total in sample: {len(sub_samples)}) ---")
        
        # Display the first 3 actual tweets found for this specific bucket
        for idx, row_text in enumerate(sub_samples['text'].head(3), 1):
            print(f" {idx}) {row_text}")

import pandas as pd
import os
import sys

csv_path = "report/taxonomy_validation_sample.csv"

if not os.path.exists(csv_path):
    print(f"Error: {csv_path} does not exist. Please check your path.")
    sys.exit(1)

# 1. Load the existing validation sheet
df = pd.read_csv(csv_path)

# Ensure manual_intent column is treated as string text and handle empty records cleanly
if 'manual_intent' not in df.columns:
    df['manual_intent'] = ""
df['manual_intent'] = df['manual_intent'].fillna("").astype(str)

taxonomy_map = {
    "1": "Playback/Technical Bug",
    "2": "Account Access",
    "3": "Billing/Subscription",
    "4": "Content Availability",
    "5": "Feature Request/Complaint",
    "6": "Service Outage",
    "7": "Other"
}

print("\n==============================================")
print("RECOVERING MANUAL TAXONOMY EVALUATION PROCESS")
print("==============================================")
print("Keys: 1=Playback, 2=Access, 3=Billing, 4=Content, 5=Feature, 6=Outage, 7=Other\n")

# Count how many rows are already populated with a real text description label
completed_count = df[df['manual_intent'].isin(taxonomy_map.values())].shape[0]
print(f"Status: Found {completed_count} previously verified rows.")
print("Resuming stream for un-labeled lines...\n")

# 2. Iterate through and fill only missing parameters
for i, row in df.iterrows():
    # Skip if this row already has one of our clean explicit text categories assigned
    if df.at[i, 'manual_intent'] in taxonomy_map.values():
        continue
        
    print(f"\n[{i+1}/{len(df)}] Tweet ID: {row['tweet_id']}")
    print(f"Text: {row['text']}")
    
    while True:
        user_input = input("Your intent label (1-7) or type 'q' to save & exit: ").strip()
        if user_input.lower() == 'q':
            df.to_csv(csv_path, index=False)
            print("\nProgress saved successfully. Exiting.")
            sys.exit(0)
        if user_input in taxonomy_map:
            df.at[i, 'manual_intent'] = taxonomy_map[user_input]
            break
        print("Invalid choice! Choose a number between 1 and 7.")
    
    # Save incrementally after EVERY tweet input so a crash never costs you data again
    df.to_csv(csv_path, index=False)

print("\n🎉 Congratulations! All 80 records are completely grounded with human feedback.")
print(f"Saved finalized evaluation sheet to: {csv_path}")

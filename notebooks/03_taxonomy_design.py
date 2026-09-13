import pandas as pd

df = pd.read_csv("data/raw/twcs/twcs.csv")
df['created_at'] = pd.to_datetime(df['created_at'], format='%a %b %d %H:%M:%S +0000 %Y')

FINAL_BRAND = "SpotifyCares"
brand_replies = df[df['author_id'] == FINAL_BRAND]
customer_tweet_ids = brand_replies['in_response_to_tweet_id'].dropna().astype(int).unique()
customer_tweets = df[df['tweet_id'].isin(customer_tweet_ids)]

print("Customer tweets available:", len(customer_tweets))

labeling_sample = customer_tweets.sample(n=80, random_state=42).reset_index(drop=True)
print(f"Sampled {len(labeling_sample)} tweets for manual taxonomy validation")

labeling_sample['manual_intent'] = ""  # empty column you'll fill in by hand
labeling_sample[['tweet_id', 'text', 'manual_intent']].to_csv(
    "report/taxonomy_validation_sample.csv", index=False
)
print("Saved sample for manual labeling")

for i, row in labeling_sample.iterrows():
    print(f"\n[{i+1}/{len(labeling_sample)}] {row['text']}")
    label = input("Your intent label: ")
    labeling_sample.at[i, 'manual_intent'] = label

labeling_sample.to_csv("report/taxonomy_validation_sample.csv", index=False)
import pandas as pd
import re

print("Loading 2.8M rows dataset...")
df = pd.read_csv("data/raw/twcs/twcs.csv")
df['created_at'] = pd.to_datetime(df['created_at'], format='%a %b %d %H:%M:%S +0000 %Y')

# CRITICAL OPTIMIZATION: Index the dataframe ONCE here, out of the function loops
print("Building master lookup index (this takes a few seconds)...")
df_indexed = df.set_index('tweet_id')

def build_thread_optimized(indexed_df, tweet_id):
    current_id = tweet_id
    
    # 1. Walk backward to find the root message
    while True:
        if current_id not in indexed_df.index:
            break
        row = indexed_df.loc[current_id]
        parent_id = row['in_response_to_tweet_id']
        if pd.isna(parent_id) or int(parent_id) not in indexed_df.index:
            break
        current_id = int(parent_id)
        
    root_id = current_id
    thread = [root_id]
    frontier = [root_id]
    
    # 2. Walk forward to find all downstream replies
    while frontier:
        next_frontier = []
        for tid in frontier:
            row = indexed_df.loc[tid]
            responses = row['response_tweet_id']
            if pd.notna(responses):
                for rid in str(responses).split(','):
                    rid = int(rid)
                    if rid in indexed_df.index and rid not in thread:
                        thread.append(rid)
                        next_frontier.append(rid)
        frontier = next_frontier
        
    return indexed_df.loc[thread].reset_index()

# Target SpotifyCares
FINAL_BRAND = "SpotifyCares"
brand_replies = df[df['author_id'] == FINAL_BRAND]
customer_tweet_ids = brand_replies['in_response_to_tweet_id'].dropna().astype(int).unique()
customer_tweets = df[df['tweet_id'].isin(customer_tweet_ids)]

print(f"\nFinal brand: {FINAL_BRAND}")
print(f"Total Brand replies: {len(brand_replies)}")
print(f"Available matching Customer threads: {len(customer_tweets)}")

# Process a clean sample of 2000 conversations
all_threads = []
sample_size = min(2000, len(customer_tweets))
print(f"\nReconstructing {sample_size} historical threads fast...")

for idx, tweet_id in enumerate(customer_tweets['tweet_id'].sample(n=sample_size, random_state=42), 1):
    try:
        thread = build_thread_optimized(df_indexed, tweet_id)
        thread['root_tweet_id'] = tweet_id
        all_threads.append(thread)
    except KeyError:
        continue # Skip if an ID happens to be malformed or missing
        
    if idx % 500 == 0:
        print(f" -> Processed {idx}/{sample_size} threads...")

# Combine and save
full_threads_df = pd.concat(all_threads, ignore_index=True)
print("\n=== EXTRACTION RESULTS ===")
print("Total rows across all reconstructed threads:", len(full_threads_df))
print("Number of distinct conversations:", full_threads_df['root_tweet_id'].nunique())

print("Saving dataset to disk...")
full_threads_df.to_csv("data/raw/spotify_full_threads.csv", index=False)
print("Done! File saved to: data/raw/spotify_full_threads.csv")

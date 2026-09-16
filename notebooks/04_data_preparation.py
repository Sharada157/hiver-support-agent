import pandas as pd
import re

import os
from dotenv import load_dotenv
load_dotenv()

if not os.getenv("HF_TOKEN"):
    print("⚠️ Warning: 'HF_TOKEN' environment variable is not set.")
    print("Please set HF_TOKEN in your local .env file.")


full_threads_df = pd.read_csv("data/raw/spotify_full_threads.csv")
full_threads_df['created_at'] = pd.to_datetime(full_threads_df['created_at'])

print("Loaded rows:", len(full_threads_df))

def clean_text(text):
    if pd.isna(text):
        return ""
    
    # remove URLs
    text = re.sub(r'https?://\S+', '', text)
    
    # remove @mentions (Twitter handles)
    text = re.sub(r'@\w+', '', text)
    
    # collapse extra whitespace left behind after removals
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

full_threads_df['text_clean'] = full_threads_df['text'].apply(clean_text)

# sanity check: compare a few before/after
print(full_threads_df[['text', 'text_clean']].sample(5, random_state=42))

def has_negative_emoji_signal(text):
    # simple example — expand this list as you find angry emojis in your data
    negative_emojis = ['😡', '🤬', '😤', '👎']
    return any(e in text for e in negative_emojis)

full_threads_df['has_negative_emoji'] = full_threads_df['text'].apply(has_negative_emoji_signal)

from langdetect import detect, LangDetectException

def safe_detect(text):
    try:
        if len(text.strip()) < 3:
            return "unknown"
        return detect(text)
    except LangDetectException:
        return "unknown"

full_threads_df['lang'] = full_threads_df['text_clean'].apply(safe_detect)
print(full_threads_df['lang'].value_counts().head(10))

full_threads_df = full_threads_df[full_threads_df['lang'] == 'en'].reset_index(drop=True)
print("Rows after English-only filter:", len(full_threads_df))

before = len(full_threads_df)
full_threads_df = full_threads_df.drop_duplicates(subset='text_clean').reset_index(drop=True)
print(f"Removed {before - len(full_threads_df)} exact duplicate rows")

def normalize_for_dedup(text):
    # lowercase and strip digits/names to catch near-identical templates
    text = text.lower()
    text = re.sub(r'\d+', '', text)
    return text.strip()

full_threads_df['dedup_key'] = full_threads_df['text_clean'].apply(normalize_for_dedup)

before = len(full_threads_df)
full_threads_df = full_threads_df.drop_duplicates(subset='dedup_key').reset_index(drop=True)
print(f"Removed {before - len(full_threads_df)} near-duplicate rows")

full_threads_df = full_threads_df.drop(columns=['dedup_key'])

# Construct triples (customer message and corresponding brand reply)
customer_df = full_threads_df[full_threads_df['author_id'] != "SpotifyCares"].copy()
brand_df = full_threads_df[full_threads_df['author_id'] == "SpotifyCares"].copy()

triples_df = customer_df.merge(
    brand_df,
    left_on='tweet_id',
    right_on='in_response_to_tweet_id',
    suffixes=('_customer', '_brand')
).rename(columns={
    'text_clean_customer': 'customer_message',
    'text_clean_brand': 'brand_reply'
})

total_customer_messages = full_threads_df[full_threads_df['author_id'] != "SpotifyCares"].shape[0]
kept = len(triples_df)
dropped = total_customer_messages - kept

print(f"Total customer messages seen: {total_customer_messages}")
print(f"Kept (had a brand reply): {kept}")
print(f"Dropped (no brand reply found): {dropped} ({dropped/total_customer_messages*100:.1f}%)")

knowledge_base = triples_df[['customer_message', 'brand_reply']].copy()
knowledge_base = knowledge_base.reset_index(drop=True)
print("Knowledge base size:", len(knowledge_base))


from sentence_transformers import SentenceTransformer

embedder = SentenceTransformer('all-MiniLM-L6-v2')  # small, fast, well-tested model

kb_embeddings = embedder.encode(
    knowledge_base['customer_message'].tolist(),
    show_progress_bar=True,
    convert_to_numpy=True
)

print("Embeddings shape:", kb_embeddings.shape)

import numpy as np

np.save("data/processed/kb_embeddings.npy", kb_embeddings)
knowledge_base.to_csv("data/processed/knowledge_base.csv", index=False)


triples_df.to_csv("data/processed/spotify_triples.csv", index=False)
full_threads_df.to_csv("data/processed/spotify_threads_clean.csv", index=False)

print("Saved processed files to data/processed/")


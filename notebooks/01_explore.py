import pandas as pd

df = pd.read_csv("data/raw/twcs/twcs.csv")

print("Shape:", df.shape)
print("\nColumns:", df.columns.tolist())
print("\nSample rows:")
print(df.head())
print("\nData types:")
print(df.dtypes)

print("\nNull counts per column:")
print(df.isnull().sum())

print("\nDuplicate rows:", df.duplicated().sum())
print("Duplicate tweet_ids:", df['tweet_id'].duplicated().sum())


def build_thread(df, tweet_id):
    """Given a tweet_id, walk backward to the root of its conversation
    and forward through all replies, returning the full thread as a list."""
    df_indexed = df.set_index('tweet_id')
    
    # walk backward to find the root of the conversation
    current_id = tweet_id
    while True:
        row = df_indexed.loc[current_id]
        parent_id = row['in_response_to_tweet_id']
        if pd.isna(parent_id) or parent_id not in df_indexed.index:
            break
        current_id = int(parent_id)
    
    root_id = current_id
    
    # walk forward from root, following response_tweet_id chains
    thread = [root_id]
    frontier = [root_id]
    while frontier:
        next_frontier = []
        for tid in frontier:
            row = df_indexed.loc[tid]
            responses = row['response_tweet_id']
            if pd.notna(responses):
                for rid in str(responses).split(','):
                    rid = int(rid)
                    if rid in df_indexed.index:
                        thread.append(rid)
                        next_frontier.append(rid)
        frontier = next_frontier
    
    return df_indexed.loc[thread].reset_index()

sample_thread = build_thread(df, df['tweet_id'].iloc[0])
print(sample_thread[['tweet_id', 'author_id', 'text']])

print(df['inbound'].value_counts())

print(df['author_id'].value_counts().head(20))

brand_counts = df[~df['author_id'].str.isnumeric()]['author_id'].value_counts()
print(brand_counts.head(20))

df['created_at'] = pd.to_datetime(df['created_at'], format='%a %b %d %H:%M:%S +0000 %Y')
print("Earliest tweet:", df['created_at'].min())
print("Latest tweet:", df['created_at'].max())

BRAND = "SpotifyCares"

# get all tweet_ids where the brand replied
brand_replies = df[df['author_id'] == BRAND]

# get the customer tweets that the brand was replying to
customer_tweet_ids = brand_replies['in_response_to_tweet_id'].dropna().astype(int).unique()
customer_tweets = df[df['tweet_id'].isin(customer_tweet_ids)]

print("Brand replies:", len(brand_replies))
print("Customer tweets that got a brand reply:", len(customer_tweets))

SUBSAMPLE_SIZE = 8000

sampled_customer_tweets = customer_tweets.sample(
    n=min(SUBSAMPLE_SIZE, len(customer_tweets)),
    random_state=42
)

sampled_customer_tweets.to_csv("data/raw/spotify_customer_tweets_subsample.csv", index=False)
brand_replies.to_csv("data/raw/spotify_brand_replies_full.csv", index=False)
import pandas as pd
import re

full_threads_df = pd.read_csv("data/raw/spotify_full_threads.csv")
full_threads_df['created_at'] = pd.to_datetime(full_threads_df['created_at'], format='%a %b %d %H:%M:%S +0000 %Y')

print("Loaded rows:", len(full_threads_df))



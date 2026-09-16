import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

triples_df = pd.read_csv("data/processed/spotify_triples.csv")
taxonomy_sample = pd.read_csv("report/taxonomy_validation_sample.csv")

print("Total triples available:", len(triples_df))
print("Already-seen taxonomy sample size:", len(taxonomy_sample))

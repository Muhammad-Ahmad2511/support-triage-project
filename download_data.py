from datasets import load_dataset
import pandas as pd

print("Downloading dataset...")
dataset = load_dataset("Tobi-Bueck/customer-support-tickets")
df = dataset["train"].to_pandas()

print("Columns available:", df.columns.tolist())
print("Total rows:", len(df))

# Filter to English only
df_en = df[df["language"] == "en"]
df_en = df_en.dropna(subset=["subject", "body"])  # remove rows with missing subject/body
sample = df_en.sample(50, random_state=42)
sample.to_csv("tickets.csv", index=False)

print("Saved 20 English sample tickets to tickets.csv")
print(sample[["subject", "body"]].head())
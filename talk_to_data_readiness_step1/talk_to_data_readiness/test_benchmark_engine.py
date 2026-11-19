
import pandas as pd
from pathlib import Path

benchmark_path = (
    Path("data")
    / "benchmark"
    / "benchmark_questions.csv"
)

df = pd.read_csv(benchmark_path)

print("Total questions:", len(df))

print("\nQuestions by model:")
print(df["model"].value_counts())

print("\nInitial assessment distribution:")
print(df["initial_hypothesis"].value_counts())

print("\nColumns:")
print(df.columns.tolist())

assert len(df) == 25
assert df["question_id"].is_unique
assert set(df["model"].unique()) == {
    "Finance",
    "Sales",
    "HR"
}

print("\nBENCHMARK DATA TEST PASSED!")

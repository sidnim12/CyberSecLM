import json
from collections import Counter
from itertools import combinations
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATASET_PATH = (
    PROJECT_ROOT.parent
    / "Datasets"
    / "tram"
    / "data"
    / "tram2-data"
    / "multi_label.json"
)

with open(DATASET_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

cooccurrence = Counter()

for example in data:
    labels = sorted(set(example["labels"]))

    if len(labels) < 2:
        continue

    for pair in combinations(labels, 2):
        cooccurrence[pair] += 1


print("===== TECHNIQUE CO-OCCURRENCE =====")

for (technique_a, technique_b), count in cooccurrence.most_common(30):
    print(f"{technique_a} + {technique_b}: {count}")

print("\n===== SUMMARY =====")

multi_label_examples = sum(
    1 for example in data
    if len(set(example["labels"])) >= 2
)

print(f"Examples with multiple techniques: {multi_label_examples}")
print(f"Unique technique pairs: {len(cooccurrence)}")
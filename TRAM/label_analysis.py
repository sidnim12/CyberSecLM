import json
from collections import Counter, defaultdict
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


# --------------------------------------------------
# Build technique -> documents mapping
# --------------------------------------------------

technique_documents = defaultdict(set)

for example in data:
    document = example["doc_title"]

    for technique in example["labels"]:
        technique_documents[technique].add(document)


# --------------------------------------------------
# Technique coverage
# --------------------------------------------------

print("===== TECHNIQUE DOCUMENT COVERAGE =====")

for technique, documents in sorted(
    technique_documents.items(),
    key=lambda item: len(item[1])
):
    print(
        f"{technique}: "
        f"{len(documents)} document(s)"
    )


# --------------------------------------------------
# Rare techniques
# --------------------------------------------------

print("\n===== RARE TECHNIQUES =====")

rare = [
    (technique, len(documents))
    for technique, documents in technique_documents.items()
    if len(documents) <= 3
]

for technique, count in sorted(rare):
    print(f"{technique}: {count} document(s)")


# --------------------------------------------------
# Documents per technique statistics
# --------------------------------------------------

document_counts = [
    len(documents)
    for documents in technique_documents.values()
]

print("\n===== SUMMARY =====")

print(f"Techniques: {len(document_counts)}")
print(f"Minimum documents per technique: {min(document_counts)}")
print(f"Maximum documents per technique: {max(document_counts)}")
print(
    f"Average documents per technique: "
    f"{sum(document_counts) / len(document_counts):.2f}"
)
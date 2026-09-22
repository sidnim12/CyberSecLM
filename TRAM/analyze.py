import json
from collections import Counter
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
# Basic statistics
# --------------------------------------------------

total_examples = len(data)

labeled_examples = [
    example for example in data
    if example["labels"]
]

unlabeled_examples = [
    example for example in data
    if not example["labels"]
]


print("===== BASIC STATISTICS =====")
print(f"Total examples: {total_examples}")
print(f"Labeled examples: {len(labeled_examples)}")
print(f"Unlabeled examples: {len(unlabeled_examples)}")


# --------------------------------------------------
# Technique statistics
# --------------------------------------------------

technique_counts = Counter()

for example in labeled_examples:
    for technique in example["labels"]:
        technique_counts[technique] += 1


print("\n===== TECHNIQUES =====")
print(f"Unique techniques: {len(technique_counts)}")

print("\nTop 20 techniques:")

for technique, count in technique_counts.most_common(20):
    print(f"{technique}: {count}")


# --------------------------------------------------
# Multi-label statistics
# --------------------------------------------------

label_count_distribution = Counter(
    len(example["labels"])
    for example in labeled_examples
)


print("\n===== LABEL DISTRIBUTION =====")

for number_of_labels, count in sorted(label_count_distribution.items()):
    print(
        f"{number_of_labels} technique(s): "
        f"{count} examples"
    )


# --------------------------------------------------
# Document statistics
# --------------------------------------------------

document_counts = Counter(
    example["doc_title"]
    for example in data
)


print("\n===== DOCUMENTS =====")
print(f"Unique documents: {len(document_counts)}")

print("\nTop 20 documents by number of sentences:")

for document, count in document_counts.most_common(20):
    print(f"{count}: {document}")


# --------------------------------------------------
# Labeled documents
# --------------------------------------------------

labeled_document_counts = Counter(
    example["doc_title"]
    for example in labeled_examples
)


print("\n===== LABELED DOCUMENTS =====")
print(
    f"Documents containing labeled examples: "
    f"{len(labeled_document_counts)}"
)


# --------------------------------------------------
# Summary
# --------------------------------------------------

print("\n===== SUMMARY =====")

print(
    f"Average labels per labeled example: "
    f"{sum(len(x['labels']) for x in labeled_examples) / len(labeled_examples):.2f}"
)

print(
    f"Average sentences per document: "
    f"{len(data) / len(document_counts):.2f}"
)
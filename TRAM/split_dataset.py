import json
import random
from collections import defaultdict
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

OUTPUT_DIR = PROJECT_ROOT / "data" / "tram"


SEED = 42
TRAIN_RATIO = 0.70
VALIDATION_RATIO = 0.15
TEST_RATIO = 0.15


with open(DATASET_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)


# --------------------------------------------------
# 1. Group examples by document
# --------------------------------------------------

documents = defaultdict(list)

for example in data:
    documents[example["doc_title"]].append(example)


document_names = list(documents.keys())

print("===== DATASET =====")
print(f"Total examples: {len(data)}")
print(f"Total documents: {len(document_names)}")


# --------------------------------------------------
# 2. Shuffle documents
# --------------------------------------------------

random.seed(SEED)
random.shuffle(document_names)


# --------------------------------------------------
# 3. Calculate split sizes
# --------------------------------------------------

total_documents = len(document_names)

train_end = int(total_documents * TRAIN_RATIO)
validation_end = train_end + int(total_documents * VALIDATION_RATIO)

train_documents = document_names[:train_end]
validation_documents = document_names[train_end:validation_end]
test_documents = document_names[validation_end:]


# --------------------------------------------------
# 4. Collect examples
# --------------------------------------------------

train_data = []

for document in train_documents:
    train_data.extend(documents[document])


validation_data = []

for document in validation_documents:
    validation_data.extend(documents[document])


test_data = []

for document in test_documents:
    test_data.extend(documents[document])


# --------------------------------------------------
# 5. Create output directory
# --------------------------------------------------

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------
# 6. Save datasets
# --------------------------------------------------

datasets = {
    "train": train_data,
    "validation": validation_data,
    "test": test_data,
}

for split_name, split_data in datasets.items():

    output_path = OUTPUT_DIR / f"{split_name}.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(split_data, f, indent=2)

    print(
        f"{split_name.capitalize()}: "
        f"{len(split_data)} examples, "
        f"{len(set(example['doc_title'] for example in split_data))} documents"
    )


# --------------------------------------------------
# 7. Verify document leakage
# --------------------------------------------------

train_docs = set(train_documents)
validation_docs = set(validation_documents)
test_docs = set(test_documents)


assert train_docs.isdisjoint(validation_docs)
assert train_docs.isdisjoint(test_docs)
assert validation_docs.isdisjoint(test_docs)


print("\n===== SPLIT VERIFICATION =====")
print("No document leakage detected!")
print("Split completed successfully.")
import json
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "tram"


def load_split(name):
    path = DATA_DIR / f"{name}.json"

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


splits = {
    "train": load_split("train"),
    "validation": load_split("validation"),
    "test": load_split("test"),
}


print("===== TECHNIQUE COVERAGE =====")

techniques_by_split = {}

for split_name, data in splits.items():

    techniques = Counter()

    for example in data:
        for technique in example["labels"]:
            techniques[technique] += 1

    techniques_by_split[split_name] = set(techniques)

    print(
        f"{split_name.capitalize()}: "
        f"{len(techniques)} unique techniques"
    )


train_techniques = techniques_by_split["train"]
validation_techniques = techniques_by_split["validation"]
test_techniques = techniques_by_split["test"]


print("\n===== CROSS-SPLIT COVERAGE =====")

print(
    "Validation techniques unseen during training:",
    sorted(validation_techniques - train_techniques)
)

print(
    "Test techniques unseen during training:",
    sorted(test_techniques - train_techniques)
)

print(
    "\nTechniques present in all three splits:",
    len(
        train_techniques
        & validation_techniques
        & test_techniques
    )
)

print(
    "Techniques in training:",
    len(train_techniques)
)

print(
    "Techniques in validation:",
    len(validation_techniques)
)

print(
    "Techniques in test:",
    len(test_techniques)
)
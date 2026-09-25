import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "tram"

OUTPUT_DIR = DATA_DIR / "prepared"


SYSTEM_PROMPT = (
    "You are a cybersecurity threat intelligence assistant. "
    "Given a cybersecurity-related sentence, identify the MITRE ATT&CK "
    "technique IDs explicitly supported by the text. "
    "Return only valid JSON in the format "
    '{"techniques": ["Txxxx", "Txxxx.xxx"]}. '
    "Do not infer techniques that are not supported by the text."
)


def load_split(split_name):
    path = DATA_DIR / f"{split_name}.json"

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def convert_example(example):
    sentence = example["sentence"]
    labels = sorted(set(example["labels"]))

    assistant_output = json.dumps(
        {"techniques": labels},
        ensure_ascii=False
    )

    return {
        "messages": [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": sentence
            },
            {
                "role": "assistant",
                "content": assistant_output
            }
        ]
    }


def prepare_split(split_name):
    data = load_split(split_name)

    labeled_data = [
        example
        for example in data
        if example["labels"]
    ]

    skipped_examples = len(data) - len(labeled_data)

    prepared_data = [
        convert_example(example)
        for example in labeled_data
    ]

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    output_path = OUTPUT_DIR / f"{split_name}.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(
            prepared_data,
            f,
            indent=2,
            ensure_ascii=False
        )

    print(
        f"{split_name.capitalize()}: "
        f"{len(prepared_data)} labeled examples"
    )

    print(
        f"Skipped: {skipped_examples} unlabeled examples"
    )

    print(f"Saved → {output_path}\n")


if __name__ == "__main__":

    print("===== PREPARING TRAM DATASET =====\n")

    for split in ["train", "validation", "test"]:
        prepare_split(split)

    print("Dataset preparation completed!")
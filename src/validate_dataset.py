import json
import sys
from pathlib import Path


REQUIRED_FIELDS = {"techniques"}


def validate_dataset(path: str):

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"\nValidating: {path}")
    print(f"Examples: {len(data)}")

    for i, example in enumerate(data, start=1):

        # Check messages
        assert "messages" in example, (
            f"Example {i}: missing messages"
        )

        messages = example["messages"]

        assert len(messages) == 3, (
            f"Example {i}: expected 3 messages, got {len(messages)}"
        )

        roles = [message["role"] for message in messages]

        assert roles == ["system", "user", "assistant"], (
            f"Example {i}: invalid roles {roles}"
        )

        # Check message contents
        for message in messages:

            assert isinstance(message["content"], str), (
                f"Example {i}: message content must be a string"
            )

            assert message["content"].strip(), (
                f"Example {i}: message content is empty"
            )

        # Check assistant JSON
        assistant_output = messages[2]["content"]

        try:
            output = json.loads(assistant_output)

        except json.JSONDecodeError:
            raise AssertionError(
                f"Example {i}: assistant output is not valid JSON"
            )

        # Check required fields
        missing_fields = REQUIRED_FIELDS - output.keys()

        assert not missing_fields, (
            f"Example {i}: missing fields {missing_fields}"
        )

        # Check techniques
        techniques = output["techniques"]

        assert isinstance(techniques, list), (
            f"Example {i}: techniques must be a list"
        )

        assert len(techniques) > 0, (
            f"Example {i}: techniques list is empty"
        )

        for technique in techniques:

            assert isinstance(technique, str), (
                f"Example {i}: technique ID must be a string"
            )

            assert technique.startswith("T"), (
                f"Example {i}: invalid technique ID {technique}"
            )

    print("Validation passed!")


if __name__ == "__main__":

    if len(sys.argv) != 2:

        print(
            "Usage:\n"
            "python TRAM/validate_dataset.py <dataset_path>"
        )

        sys.exit(1)

    validate_dataset(sys.argv[1])
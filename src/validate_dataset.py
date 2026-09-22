import json
import sys


REQUIRED_FIELDS = {
    "entities",
    "techniques",
    "vulnerabilities",
    "iocs",
    "evidence",
}


def validate_dataset(path: str):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"\nValidating: {path}")
    print(f"Examples: {len(data)}")

    for i, example in enumerate(data, start=1):

        assert "messages" in example, f"Example {i}: missing messages"

        messages = example["messages"]

        assert len(messages) == 3, (
            f"Example {i}: expected 3 messages, got {len(messages)}"
        )

        roles = [message["role"] for message in messages]

        assert roles == ["system", "user", "assistant"], (
            f"Example {i}: invalid roles {roles}"
        )

        for message in messages:
            assert isinstance(message["content"], str), (
                f"Example {i}: message content must be a string"
            )

        assistant_output = messages[2]["content"]

        try:
            output = json.loads(assistant_output)
        except json.JSONDecodeError:
            raise AssertionError(
                f"Example {i}: assistant output is not valid JSON"
            )

        missing_fields = REQUIRED_FIELDS - output.keys()

        assert not missing_fields, (
            f"Example {i}: missing fields {missing_fields}"
        )

    print("Validation passed!")


if __name__ == "__main__":

    if len(sys.argv) != 2:
        print("Usage:")
        print("python src/validate_dataset.py <dataset_path>")
        sys.exit(1)

    validate_dataset(sys.argv[1])
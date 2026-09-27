"""Inspect assistant-only supervision using the same tokenizer as v2 training."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data/tram/v2/prepared"
TOKENIZER = ROOT / "experiments/cyberseclm-tram-qlora"
MAX_LENGTH = 1024


def load_tokenizer():
    from transformers import AutoTokenizer
    from trl.chat_template_utils import get_training_chat_template, has_generation_markers
    tokenizer = AutoTokenizer.from_pretrained(TOKENIZER, local_files_only=True)
    if not has_generation_markers(tokenizer.chat_template):
        tokenizer.chat_template = get_training_chat_template(tokenizer)
    tokenizer.padding_side = "right"
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    return tokenizer


def inspect(tokenizer):
    from transformers import AutoTokenizer
    original = AutoTokenizer.from_pretrained(TOKENIZER, local_files_only=True)
    summary, example_view = {}, None
    for split in ("train", "validation"):
        rows = json.loads((DATA / f"{split}.json").read_text(encoding="utf-8"))
        total = supervised = 0
        for index, row in enumerate(rows):
            messages = row["messages"]
            encoded = tokenizer.apply_chat_template(messages, tokenize=True,
                add_generation_prompt=False, return_dict=True, return_assistant_tokens_mask=True)
            ids, mask = encoded["input_ids"], encoded["assistant_masks"]
            baseline = original.apply_chat_template(messages, tokenize=True,
                add_generation_prompt=False, return_dict=True)["input_ids"]
            if ids != baseline:
                raise ValueError(f"{split}/{index}: training template changed the token sequence")
            prompt = tokenizer.apply_chat_template(messages[:2], tokenize=True,
                add_generation_prompt=True, return_dict=True)["input_ids"]
            if ids[:len(prompt)] != prompt or any(mask[:len(prompt)]):
                raise ValueError(f"{split}/{index}: prompt prefix/mask mismatch")
            selected = [t for t, active in zip(ids, mask) if active]
            expected = messages[2]["content"] + tokenizer.eos_token
            if not selected or tokenizer.decode(selected).rstrip("\n") != expected:
                raise ValueError(f"{split}/{index}: mask must cover the full JSON and stop token")
            if len(ids) > MAX_LENGTH:
                raise ValueError(f"{split}/{index}: would truncate")
            total += len(ids)
            supervised += sum(mask)
            if example_view is None and len(json.loads(messages[2]["content"])["techniques"]) > 1:
                example_view = {"split": split, "index": index,
                    "cti_text": messages[1]["content"], "expected_answer": messages[2]["content"],
                    "supervised_text": tokenizer.decode(selected),
                    "tokens": [{"id": t, "text": tokenizer.decode([t]),
                                "label": t if active else -100} for t, active in zip(ids, mask)]}
        summary[split] = {"examples_checked": len(rows), "total_tokens": total,
                          "supervised_tokens": supervised}
    return {"status": "PASS", "splits": summary, "example": example_view,
            "meaning": "label=-100 ignores a token in loss; context is still visible to the model."}


def main():
    result = inspect(load_tokenizer())
    path = ROOT / "experiments/audit/training_mask.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print("PASS: prompts masked; complete JSON answers and stop tokens supervised; no truncation.")
    for split, stats in result["splits"].items():
        print(f"{split}: {stats['examples_checked']} examples checked")
    print("CTI example:", result["example"]["cti_text"])
    print("Learned answer:", result["example"]["supervised_text"])
    print(f"Details: {path}")


if __name__ == "__main__":
    main()

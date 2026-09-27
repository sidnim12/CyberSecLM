"""Small fixtures test audit behavior without a GPU or downloaded model."""
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from audit_dataset import audit, inspect_split, token_lengths
from prepare_dataset import convert_example


def row(text="PowerShell executed a script.", labels=None, doc="Report A"):
    return {"sentence": text, "labels": ["T1059.001"] if labels is None else labels, "doc_title": doc}


class AuditTests(unittest.TestCase):
    def test_prepared_mismatch_and_bad_id(self):
        good = row()
        bad = row(labels=["T1234oops"])
        prepared = [convert_example(good)]
        prepared[0]["messages"][1]["content"] = "Wrong sentence"
        _, errors, _, _ = inspect_split("train", [good, bad], prepared)
        self.assertTrue(any("invalid label" in e for e in errors))
        self.assertTrue(any("differs" in e for e in errors))

    def test_unknown_is_not_a_negative(self):
        raw = [row(), row(labels=[])]
        stats, errors, _, _ = inspect_split("train", raw, [convert_example(raw[0])])
        self.assertEqual(errors, [])
        self.assertEqual(stats["labeled_examples"], 1)

    def test_overlap_conflict_and_document_leakage(self):
        root = Path("fixture")
        splits = {
                "train": [row()],
                "validation": [row(" powershell  executed a script. ", ["T1105"], "Report B")],
                "test": [row("Other text", [], "Report A")],
        }
        files = {}
        for split, rows in splits.items():
            files[root / f"{split}.json"] = json.dumps(rows).encode()
            files[root / "prepared" / f"{split}.json"] = json.dumps(
                [convert_example(r) for r in rows if r["labels"]]).encode()
        with patch.object(Path, "read_bytes", lambda path: files[path]):
            result = audit(root)
            self.assertEqual(result["status"], "fail")
            self.assertEqual(result["overlaps"]["train/validation"]["shared_labeled_sentence_count"], 1)
            self.assertEqual(len(result["conflicting_labeled_sentences"]), 1)
            self.assertEqual(result["overlaps"]["train/test"]["documents"], ["Report A"])

    def test_token_limit_boundary(self):
        class Tokenizer:
            def apply_chat_template(self, messages, **kwargs):
                return {"input_ids": list(range(int(messages[0]["content"])))}
        samples = [{"messages": [{"content": str(n)}]} for n in (4, 5, 6)]
        result = token_lengths(samples, Tokenizer(), 5)
        self.assertEqual(result["over_limit"], [{"prepared_index": 2, "tokens": 6}])
        self.assertEqual(result["max_tokens"], 6)


if __name__ == "__main__":
    unittest.main()

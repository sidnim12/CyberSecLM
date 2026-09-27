import unittest

from clean_dataset import clean_rows


def row(text, labels=None, doc="A"):
    return {"sentence": text, "labels": ["T1105"] if labels is None else labels, "doc_title": doc}


class CleanupTests(unittest.TestCase):
    def test_quarantine_dedup_priority_and_unchanged_test(self):
        raw = {
            "train": [row("shared"), row("conflict"), row("unique"), row("UNIQUE"),
                      row("long"), row("bad report", doc="excluded"), row("unknown", [])],
            "validation": [row("shared", doc="B"), row("conflict", ["T1059.001"], "B")],
            "test": [row("test", doc="C")],
        }
        clean, provenance, removed = clean_rows(
            raw, lambda e: 1025 if e["messages"][1]["content"] == "long" else 100, {"excluded"})
        self.assertEqual([r["sentence"] for r in clean["train"]], ["unique", "unknown"])
        self.assertEqual([r["sentence"] for r in clean["validation"]], ["shared"])
        self.assertIs(clean["test"], raw["test"])
        self.assertEqual(provenance["train"][0]["original_raw_index"], 2)
        self.assertEqual(len(removed), 6)
        self.assertEqual(len(raw["train"]), 7)

    def test_limit_boundary_and_unknown_annotations(self):
        raw = {"train": [row("same"), row("same", [])], "validation": [], "test": []}
        clean, _, removed = clean_rows(raw, lambda e: 1024, set())
        self.assertEqual(len(clean["train"]), 2)
        self.assertEqual(removed, [])


if __name__ == "__main__":
    unittest.main()

"""Turn the saved audit into a readable review queue. Never edit labels automatically."""

import hashlib
import json
from collections import Counter
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AUDIT = ROOT / "experiments" / "audit" / "dataset_audit.json"
OUTPUT = ROOT / "experiments" / "audit" / "dataset_review.md"


def context_lines(rows, index):
    """Adjacent records give context only when they belong to the same report."""
    doc = rows[index]["doc_title"]
    return [
        f"- Raw index {i}: {rows[i]['sentence']}"
        for i in range(max(0, index - 1), min(len(rows), index + 2))
        if rows[i]["doc_title"] == doc
    ]


def build_review(report, raw):
    lines = ["# TRAM dataset review", "",
             "Review queue only: source data and labels have not been changed.",
             "All record indices below start at zero.", "",
             "## 1. Report pairs sharing labeled sentences", ""]
    # Count unique shared sentences per report pair, not every duplicate occurrence.
    pairs = Counter()
    for overlap in report["overlaps"].values():
        for item in overlap["sentences"]:
            sources = {(r["split"], r["doc_title"]) for r in item["occurrences"] if r["labels"]}
            for first, second in combinations(sorted(sources), 2):
                if first[0] != second[0]:
                    pairs[(first, second)] += 1
    for (first, second), count in pairs.most_common():
        lines.append(f"- **{count} shared labeled sentences**: {first[0]} / {first[1]} ↔ {second[0]} / {second[1]}")
    lines += ["", "Check whether these are copies of the same original report. Different titles alone do not prove independence.",
              "For a future dataset version, group confirmed report copies before splitting; preserve the original benchmark.", "",
              "## 2. Conflicting annotations", ""]
    for number, item in enumerate(report["conflicting_labeled_sentences"], 1):
        lines += [f"### Conflict {number}", "", item["normalized_text"], ""]
        for occurrence in item["occurrences"]:
            split, index = occurrence["split"], occurrence["raw_index"]
            lines += [f"**{split}, raw index {index} — {occurrence['doc_title']}**",
                      f"Labels: {', '.join(occurrence['labels']) or 'Unknown / unannotated'}", ""]
            lines.extend(context_lines(raw[split], index))
            lines.append("")
        lines += ["Decision: pending source review. Do not merge label lists automatically.", ""]

    lines += ["## 3. Examples exceeding the token limit", ""]
    tokens = report["tokenization"]
    if tokens["status"] != "checked":
        raise ValueError("Run audit_dataset.py with --tokenizer first to include long examples.")
    long_count = 0
    for split, stats in tokens["splits"].items():
        # Preparation drops unlabeled rows; map prepared indices back to raw indices.
        labeled = [(i, row) for i, row in enumerate(raw[split]) if row["labels"]]
        for item in stats["over_limit"]:
            index, row = labeled[item["prepared_index"]]
            long_count += 1
            lines += [f"### {split}: prepared index {item['prepared_index']}, raw index {index}", "",
                      f"Document: {row['doc_title']}",
                      f"Tokens: {item['tokens']} / limit {stats['max_length_checked']}",
                      f"Labels: {', '.join(row['labels'])}", "",
                      "Text preview (first 700 characters):", "", row["sentence"][:700], "",
                      "Decision: inspect full raw record. Preserve evidence and the complete target answer; do not blindly truncate.", ""]
    lines += ["## Recommended next step", "",
              "Resolve report identity first. Then review label conflicts against the original source, recording each decision.",
              "For long records, inspect token masks before choosing a larger context limit or an evidence-preserving transformation.",
              "An IOC list or configuration block should not be split into chunks that all inherit the full record's labels.", ""]
    return "\n".join(line.rstrip() for line in lines), len(pairs), long_count


def main():
    report = json.loads(AUDIT.read_text(encoding="utf-8"))
    # Prevent stale indices from pointing at different records after data edits.
    for filename, expected in report["files"].items():
        if hashlib.sha256(Path(filename).read_bytes()).hexdigest() != expected:
            raise ValueError(f"Dataset changed: {filename}. Rerun the audit first.")
    raw = {split: json.loads((ROOT / "data" / "tram" / f"{split}.json").read_text(encoding="utf-8"))
           for split in ("train", "validation", "test")}
    text, pairs, long_count = build_review(report, raw)
    OUTPUT.write_text(text, encoding="utf-8")
    print(f"Report pairs to inspect: {pairs}")
    print(f"Annotation conflicts: {len(report['conflicting_labeled_sentences'])}")
    print(f"Long examples: {long_count}")
    print(f"Review: {OUTPUT}")


if __name__ == "__main__":
    main()

"""Audit TRAM splits without modifying them. No model weights are loaded."""

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

from prepare_dataset import convert_example

ROOT = Path(__file__).resolve().parent.parent
SPLITS = ("train", "validation", "test")
ATTACK_ID = re.compile(r"T\d{4}(?:\.\d{3})?", re.ASCII)


def normalize_text(text):
    # Different reports can quote the same CTI sentence.
    return " ".join(text.casefold().split())


def inspect_split(name, raw, prepared):
    errors = []
    documents = set()
    sentences = defaultdict(list)
    counts = Counter()
    expected = []
    for index, row in enumerate(raw):
        location = f"{name}: raw row {index}"
        if not isinstance(row, dict):
            errors.append(f"{location}: expected an object")
            continue
        sentence, doc, labels = (row.get(k) for k in ("sentence", "doc_title", "labels"))
        if not isinstance(sentence, str) or not sentence.strip():
            errors.append(f"{location}: missing/empty sentence")
            continue
        if not isinstance(doc, str) or not doc.strip():
            errors.append(f"{location}: missing/empty document title")
            continue
        documents.add(doc)
        if not isinstance(labels, list) or any(
            not isinstance(label, str) or not ATTACK_ID.fullmatch(label) for label in labels
        ):
            errors.append(f"{location}: invalid label list or ATT&CK ID format")
            continue
        if len(labels) != len(set(labels)):
            errors.append(f"{location}: repeated labels")
        sentences[normalize_text(sentence)].append({
            "split": name, "raw_index": index, "doc_title": doc,
            "labels": sorted(set(labels)),
        })
        # Empty annotations are unknown, not verified negative examples.
        if labels:
            counts.update(set(labels))
            expected.append(convert_example(row))

    if len(expected) != len(prepared):
        errors.append(f"{name}: expected {len(expected)} prepared rows, found {len(prepared)}")
    for index, (actual, target) in enumerate(zip(prepared, expected)):
        if actual != target:
            errors.append(f"{name}: prepared row {index} differs from raw conversion")

    summary = {
        "raw_examples": len(raw), "labeled_examples": len(expected),
        "prepared_examples": len(prepared), "documents": len(documents),
        "unique_labels": len(counts), "label_frequencies": dict(sorted(counts.items())),
        "duplicate_sentence_groups": sum(len(rows) > 1 for rows in sentences.values()),
    }
    return summary, errors, documents, sentences


def token_lengths(examples, tokenizer, max_length):
    lengths = []
    over_limit = []
    for index, example in enumerate(examples):
        tokens = tokenizer.apply_chat_template(
            example["messages"], tokenize=True, add_generation_prompt=False,
        )
        # Some Transformers versions return a dictionary-like BatchEncoding.
        if hasattr(tokens, "keys"):
            tokens = tokens["input_ids"]
        length = len(tokens)
        lengths.append(length)
        if length > max_length:
            over_limit.append({"prepared_index": index, "tokens": length})
    ordered = sorted(lengths)
    return {
        "examples": len(lengths), "max_tokens": max(lengths, default=0),
        "p95_tokens": ordered[max(0, (95 * len(ordered) + 99) // 100 - 1)] if ordered else 0,
        "max_length_checked": max_length, "over_limit": over_limit,
    }


def audit(data_dir, tokenizer=None, max_length=1024):
    report = {"files": {}, "splits": {}, "errors": [], "warnings": [],
              "overlaps": {}, "conflicting_labeled_sentences": []}
    docs, texts, prepared = {}, {}, {}
    for split in SPLITS:
        paths = (data_dir / f"{split}.json", data_dir / "prepared" / f"{split}.json")
        loaded = []
        for path in paths:
            payload = path.read_bytes()
            report["files"][str(path)] = hashlib.sha256(payload).hexdigest()
            value = json.loads(payload)
            if not isinstance(value, list):
                raise ValueError(f"{path}: expected a JSON array")
            loaded.append(value)
        prepared[split] = loaded[1]
        summary, errors, docs[split], texts[split] = inspect_split(split, *loaded)
        report["splits"][split] = summary
        report["errors"].extend(errors)

    for first, second in combinations(SPLITS, 2):
        shared = sorted(set(texts[first]) & set(texts[second]))
        labeled = [text for text in shared if
                   any(r["labels"] for r in texts[first][text]) and
                   any(r["labels"] for r in texts[second][text])]
        doc_overlap = sorted(docs[first] & docs[second])
        report["overlaps"][f"{first}/{second}"] = {
            "documents": doc_overlap, "shared_sentence_count": len(shared),
            "shared_labeled_sentence_count": len(labeled),
            "sentences": [{"normalized_text": text,
                           "occurrences": texts[first][text] + texts[second][text]}
                          for text in shared],
        }
        if doc_overlap:
            report["errors"].append(f"{first}/{second}: {len(doc_overlap)} shared documents")
        if shared:
            report["warnings"].append(
                f"{first}/{second}: {len(shared)} shared sentences ({len(labeled)} labeled in both)"
            )

    combined = defaultdict(list)
    for index in texts.values():
        for text, rows in index.items():
            combined[text].extend(rows)
    for text, rows in combined.items():
        # Compare annotated instances only; [] is not a negative annotation.
        label_sets = {tuple(row["labels"]) for row in rows if row["labels"]}
        if len(label_sets) > 1:
            report["conflicting_labeled_sentences"].append(
                {"normalized_text": text, "occurrences": rows}
            )
    conflicts = len(report["conflicting_labeled_sentences"])
    if conflicts:
        report["warnings"].append(f"{conflicts} sentences have differing nonempty annotations")

    report["tokenization"] = {"status": "skipped", "reason": "No tokenizer supplied"}
    if tokenizer is not None and not report["errors"]:
        report["tokenization"] = {
            "status": "checked", "splits": {
                split: token_lengths(prepared[split], tokenizer, max_length) for split in SPLITS
            },
        }
        for split, stats in report["tokenization"]["splits"].items():
            if stats["over_limit"]:
                report["warnings"].append(f"{split}: {len(stats['over_limit'])} examples exceed token limit")
    elif tokenizer is not None:
        report["tokenization"]["reason"] = "Fix data errors before tokenization"
    report["status"] = "fail" if report["errors"] else ("review" if report["warnings"] else "pass")
    report["notes"] = [
        "ATT&CK IDs are checked for syntax, not membership in an official release.",
        "Duplicate detection ignores case and whitespace; it does not detect paraphrases.",
        "Indices are zero-based. Conflicting annotations need review, not automatic relabeling.",
        "Token lengths include the full training conversation, without truncation.",
    ]
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data" / "tram")
    parser.add_argument("--output", type=Path, default=ROOT / "experiments" / "audit" / "dataset_audit.json")
    parser.add_argument("--tokenizer", help="Local tokenizer directory or already cached model ID")
    parser.add_argument("--max-length", type=int, default=1024, help="Token limit to check; default: 1024")
    args = parser.parse_args()
    if args.max_length < 1:
        parser.error("--max-length must be positive")
    tokenizer = None
    if args.tokenizer:
        from transformers import AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained(args.tokenizer, local_files_only=True)
    report = audit(args.data_dir.resolve(), tokenizer, args.max_length)
    # Refuse to overwrite any input dataset with an audit report.
    if str(args.output.resolve()) in report["files"]:
        parser.error("--output must not overwrite an input dataset")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Audit: {report['status'].upper()}")
    for split, stats in report["splits"].items():
        print(f"{split}: {stats['prepared_examples']} prepared examples, {stats['unique_labels']} labels")
    for message in report["errors"] + report["warnings"]:
        print(f"- {message}")
    print(f"Tokenization: {report['tokenization']['status']}")
    print(f"Report: {args.output.resolve()}")
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

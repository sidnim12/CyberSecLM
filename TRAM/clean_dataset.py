"""Build conservative TRAM v2; preserve v1 and copy the test set unchanged."""

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from audit_dataset import audit, normalize_text, ATTACK_ID
from prepare_dataset import convert_example

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "data" / "tram"
DEST = SOURCE / "v2"
MAX_LENGTH = 1024
ADVISORY = "Iranian GovernmentSponsored APT Actors Compromise Federal Network Deploy Crypto Miner Credential Harvester"
QUARANTINE_DOCUMENTS = {ADVISORY, "AA22320A " + ADVISORY}
SOURCE_URL = "https://www.cisa.gov/news-events/cybersecurity-advisories/aa22-320a"


def clean_rows(raw, length_fn, excluded_documents):
    """Return cleaned rows, per-example provenance and a reversible removal log.

    Decisions use train/validation annotations only. Test data never chooses labels.
    Validation takes priority when an identical labeled sentence occurs in training.
    """
    annotations = defaultdict(set)
    for split in ("train", "validation"):
        for row in raw[split]:
            if row["labels"]:
                annotations[normalize_text(row["sentence"])].add(tuple(sorted(set(row["labels"]))))
    conflicts = {text for text, labels in annotations.items() if len(labels) > 1}
    cleaned, provenance, quarantine = {}, {}, []
    validation_texts = set()
    for split in ("validation", "train"):
        cleaned[split], provenance[split] = [], []
        seen = set()
        for index, row in enumerate(raw[split]):
            text = normalize_text(row["sentence"])
            reason = None
            tokens = None
            if row["doc_title"] in excluded_documents:
                reason = "duplicate_advisory_with_inconsistent_annotations"
            elif row["labels"]:
                if text in conflicts:
                    reason = "conflicting_nonempty_annotations"
                elif split == "train" and text in validation_texts:
                    reason = "labeled_text_already_in_validation"
                elif text in seen:
                    reason = "duplicate_labeled_text_within_split"
                else:
                    tokens = length_fn(convert_example(row))
                    if tokens > MAX_LENGTH:
                        reason = "over_1024_tokens_quarantined_without_truncation"
            if reason:
                quarantine.append({"split": split, "original_raw_index": index,
                                   "reason": reason, "tokens": tokens, "record": row})
                continue
            cleaned[split].append(row)
            if row["labels"]:
                seen.add(text)
                provenance[split].append({
                    "prepared_index": len(provenance[split]), "original_split": split,
                    "original_raw_index": index, "v2_raw_index": len(cleaned[split]) - 1,
                    "doc_title": row["doc_title"], "tokens": tokens,
                })
        if split == "validation":
            validation_texts = seen
    cleaned["test"] = raw["test"]
    provenance["test"] = [
        {"prepared_index": n, "original_split": "test", "original_raw_index": i,
         "v2_raw_index": i, "doc_title": row["doc_title"]}
        for n, (i, row) in enumerate((i, r) for i, r in enumerate(raw["test"]) if r["labels"])
    ]
    return cleaned, provenance, quarantine


def save(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")


def main():
    from transformers import AutoTokenizer

    paths = [SOURCE / f"{s}.json" for s in ("train", "validation", "test")]
    paths += [SOURCE / "prepared" / f"{s}.json" for s in ("train", "validation", "test")]
    source_hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    raw = {s: json.loads((SOURCE / f"{s}.json").read_text(encoding="utf-8"))
           for s in ("train", "validation", "test")}
    # Fail before writing if source conversion or basic label checks no longer pass.
    original_audit = audit(SOURCE)
    if original_audit["errors"]:
        raise ValueError(original_audit["errors"])
    tokenizer_dir = ROOT / "experiments" / "cyberseclm-tram-qlora"
    tokenizer = AutoTokenizer.from_pretrained(tokenizer_dir, local_files_only=True)

    def length(example):
        tokens = tokenizer.apply_chat_template(example["messages"], tokenize=True, add_generation_prompt=False)
        return len(tokens["input_ids"] if hasattr(tokens, "keys") else tokens)

    clean, provenance, quarantine = clean_rows(raw, length, QUARANTINE_DOCUMENTS)
    prepared = {s: [convert_example(row) for row in rows if row["labels"]] for s, rows in clean.items()}
    for split in ("train", "validation", "test"):
        if not prepared[split]:
            raise ValueError(f"Empty split: {split}")
    train_labels = {label for row in clean["train"] for label in row["labels"]}
    for split in ("validation", "test"):
        missing = {label for row in clean[split] for label in row["labels"]} - train_labels
        if missing:
            raise ValueError(f"{split} has labels absent from training: {missing}")

    # Check membership against the existing pinned ATT&CK snapshot, without remapping labels.
    bundle_path = ROOT / "data" / "enterprise-attack-19.2.json"
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    official = {}
    for obj in bundle["objects"]:
        if obj.get("type") == "attack-pattern":
            for ref in obj.get("external_references", []):
                if ref.get("source_name") == "mitre-attack":
                    official[ref["external_id"]] = obj
    unknown = sorted(label for label in train_labels if label not in official or not ATTACK_ID.fullmatch(label))
    if unknown:
        raise ValueError(f"Unknown ATT&CK labels: {unknown}")
    historical = sorted(label for label in train_labels if
                        official[label].get("revoked") or official[label].get("x_mitre_deprecated"))

    # Only generated v2 files are replaced on rerun; original input files are never written.
    (DEST / "prepared").mkdir(parents=True, exist_ok=True)
    for split in ("train", "validation"):
        save(DEST / f"{split}.json", clean[split])
        save(DEST / "prepared" / f"{split}.json", prepared[split])
    for relative in (Path("test.json"), Path("prepared/test.json")):
        (DEST / relative).write_bytes((SOURCE / relative).read_bytes())
    save(DEST / "provenance.json", provenance)
    save(DEST / "quarantine.json", quarantine)

    result = audit(DEST, tokenizer, MAX_LENGTH)
    save(DEST / "audit.json", result)
    for p, digest in source_hashes.items():
        if hashlib.sha256(Path(p).read_bytes()).hexdigest() != digest:
            raise RuntimeError(f"Source changed during cleanup: {p}")
    if result["errors"] or result["conflicting_labeled_sentences"]:
        raise ValueError("V2 validation failed; inspect audit.json")
    if any(x["shared_labeled_sentence_count"] for x in result["overlaps"].values()):
        raise ValueError("V2 still has cross-split labeled overlap")
    if any(x["over_limit"] for x in result["tokenization"]["splits"].values()):
        raise ValueError("V2 still exceeds context limit")

    summary = {
        "ready_for_training_batch_inspection": True, "max_length": MAX_LENGTH,
        "source_sha256": source_hashes,
        "tokenizer_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                             for p in sorted(tokenizer_dir.iterdir())
                             if p.name in {"tokenizer.json", "tokenizer_config.json", "chat_template.jinja"}},
        "attack_snapshot_sha256": hashlib.sha256(bundle_path.read_bytes()).hexdigest(),
        "source_identity_evidence": SOURCE_URL,
        "excluded_document_titles": sorted(QUARANTINE_DOCUMENTS),
        "historical_labels_retained": historical,
        "removed_raw_by_reason": dict(Counter(x["reason"] for x in quarantine)),
        "removed_labeled_by_reason": dict(Counter(x["reason"] for x in quarantine if x["record"]["labels"])),
        "splits": {s: {"before": sum(bool(r["labels"]) for r in raw[s]),
                       "after": len(prepared[s]), "labels": result["splits"][s]["unique_labels"],
                       "max_tokens": result["tokenization"]["splits"][s]["max_tokens"]}
                   for s in ("train", "validation", "test")},
        "limitations": [
            "Quarantined annotations are excluded, not adjudicated or corrected.",
            "Unlabeled raw sentences may still overlap; they do not enter supervised training.",
            "Exact text checks do not establish absence of paraphrase or semantic leakage.",
            "V2 validation is smaller than v1; compare models on the same v2 validation set.",
            "The original test set has already been inspected in prior development; it is not a fresh external benchmark.",
            "Dataset filtering changes the experiment; do not attribute all improvement to the training objective.",
        ],
    }
    save(DEST / "manifest.json", summary)
    lines = ["# TRAM v2 cleanup", "", "Status: ready for training-batch inspection.", "",
             "| Split | Original labeled | V2 labeled | Labels | Longest example |",
             "|---|---:|---:|---:|---:|"]
    for split, stats in summary["splits"].items():
        lines.append(f"| {split} | {stats['before']} | {stats['after']} | {stats['labels']} | {stats['max_tokens']} tokens |")
    lines += ["", "## Decisions", "",
              f"- Both conflicting advisory copies excluded from train/validation. Source: {SOURCE_URL}",
              "- All occurrences of conflicting labeled sentences excluded from train/validation; labels were not guessed.",
              "- Identical labeled rows within a split deduplicated; validation retained over identical training sentences.",
              "- Four oversized configuration/IOC-heavy records quarantined, without truncation or inherited chunk labels.",
              "- Original raw and prepared test files copied byte-for-byte. All v1 source fingerprints unchanged.",
              "- Empty annotations retained in raw data but excluded from prepared examples.",
              "- Prepared examples retain the existing prompt and label format; provenance stored separately.", "",
              "## Removed labeled records", ""]
    lines += [f"- {reason}: {count}" for reason, count in summary["removed_labeled_by_reason"].items()]
    lines += ["", "## Verification", "",
              "No shared labeled text, conflicting labeled text, document overlap or over-limit examples in v2.",
              "All validation/test labels remain represented in training. Label frequencies are in audit.json.",
              f"Historical/deprecated labels retained for benchmark consistency: {historical}.", "",
              "## Limits", ""] + [f"- {note}" for note in summary["limitations"]]
    lines += ["", "## Next training configuration", "",
              "Use data/tram/v2/prepared/train.json and validation.json; set max_length=1024 explicitly.",
              "Verify assistant token masks before training. Save the new adapter to a separate v2 experiment directory.", ""]
    (DEST / "README.md").write_text("\n".join(lines), encoding="utf-8")
    print("V2 READY: data/tram/v2")
    for split, stats in summary["splits"].items():
        print(f"{split}: {stats['before']} -> {stats['after']}; {stats['labels']} labels; max {stats['max_tokens']} tokens")
    print("Original datasets unchanged; test copied byte-for-byte.")
    print("Details: data/tram/v2/README.md")


if __name__ == "__main__":
    main()

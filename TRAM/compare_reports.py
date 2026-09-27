"""Compare report text across splits; save evidence without changing datasets."""

import json
from collections import defaultdict
from itertools import combinations
from pathlib import Path

from audit_dataset import normalize_text

ROOT = Path(__file__).resolve().parent.parent


def compare(first, second):
    """Use distinct sentences so repeated boilerplate cannot inflate counts."""
    shared = first & second
    return {
        "first_sentences": len(first), "second_sentences": len(second),
        "shared_sentences": len(shared),
        "first_coverage": len(shared) / len(first) if first else 0,
        "second_coverage": len(shared) / len(second) if second else 0,
        "jaccard": len(shared) / len(first | second) if first | second else 0,
    }


def main():
    docs, labeled = defaultdict(set), defaultdict(set)
    for split in ("train", "validation", "test"):
        rows = json.loads((ROOT / "data" / "tram" / f"{split}.json").read_text(encoding="utf-8"))
        for row in rows:
            key = (split, row["doc_title"])
            text = normalize_text(row["sentence"])
            if text:
                docs[key].add(text)
                if row["labels"]:
                    labeled[key].add(text)

    candidates = []
    # Scan every cross-split report pair, including overlaps with no labels.
    for first, second in combinations(sorted(docs), 2):
        if first[0] == second[0]:
            continue
        stats = compare(docs[first], docs[second])
        shared_labels = labeled[first] & labeled[second]
        # A review heuristic, not proof that the source reports are identical.
        substantial = stats["shared_sentences"] >= 10 and min(
            stats["first_coverage"], stats["second_coverage"]
        ) >= 0.8
        if not shared_labels and not substantial:
            continue
        candidates.append({
            "first": {"split": first[0], "title": first[1]},
            "second": {"split": second[0], "title": second[1]},
            **stats,
            "shared_labeled_sentences": sorted(shared_labels),
            "assessment": "substantial text overlap; source review needed" if substantial
                          else "limited overlap; insufficient evidence to group reports",
            "substantial_overlap": substantial,
            "first_only_examples": sorted(docs[first] - docs[second])[:3],
            "second_only_examples": sorted(docs[second] - docs[first])[:3],
        })
    candidates.sort(key=lambda x: x["jaccard"], reverse=True)
    out = ROOT / "experiments" / "audit"
    out.mkdir(parents=True, exist_ok=True)
    (out / "report_comparison.json").write_text(
        json.dumps(candidates, indent=2, ensure_ascii=False), encoding="utf-8")
    lines = ["# Report identity review", "",
             "All cross-split report pairs were compared using normalized, distinct sentence text.",
             "Shown below: pairs sharing labeled sentences or substantial full-text overlap.",
             "Substantial overlap means at least 10 shared sentences and at least 80% coverage of each report.",
             "This is a review heuristic, not confirmation of source identity. No datasets were changed.", ""]
    for number, item in enumerate(candidates, 1):
        lines += [f"## Pair {number}", "",
                  f"A: {item['first']['split']} / {item['first']['title']}",
                  f"B: {item['second']['split']} / {item['second']['title']}", "",
                  f"- Shared sentences: {item['shared_sentences']}",
                  f"- Coverage of A: {item['first_coverage']:.1%} ({item['first_sentences']} distinct sentences)",
                  f"- Coverage of B: {item['second_coverage']:.1%} ({item['second_sentences']} distinct sentences)",
                  f"- Assessment: {item['assessment']}", "", "Shared labeled text:", ""]
        lines.extend(f"- {text}" for text in item["shared_labeled_sentences"])
        lines.append("")
    lines += ["## Decision guidance", "",
              "Review substantial-overlap pairs against the original source. Confirmed copies should share a document group in a future split.",
              "A command such as cmd.exe /c appearing in unrelated reports is not enough to merge their document identities.",
              "Preserve the original experiment. Record source evidence before creating a versioned split or changing annotations.", ""]
    (out / "report_comparison.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Compared {len(docs)} split/report combinations")
    print(f"Pairs for review: {len(candidates)}")
    for i, item in enumerate(candidates, 1):
        print(f"Pair {i}: {item['shared_sentences']} shared sentences; "
              f"coverage {item['first_coverage']:.1%} / {item['second_coverage']:.1%}; "
              f"{item['assessment']}")
    print(f"Report: {out / 'report_comparison.md'}")


if __name__ == "__main__":
    main()

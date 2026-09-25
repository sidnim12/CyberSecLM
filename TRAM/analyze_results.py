import json
from pathlib import Path
from collections import defaultdict, Counter


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

EVALUATION_DIR = PROJECT_ROOT / "experiments" / "evaluation"

BASE_RESULTS_PATH = EVALUATION_DIR / "base_predictions.json"

FINETUNED_RESULTS_PATH = EVALUATION_DIR / "finetuned_predictions.json"

TRAIN_DATASET_PATH = (
    PROJECT_ROOT
    / "data"
    / "tram"
    / "prepared"
    / "train.json"
)


# ============================================================
# LOAD DATA
# ============================================================

def load_results(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ============================================================
# BASIC METRICS
# ============================================================

def calculate_scores(tp, fp, fn):

    if tp + fp > 0:
        precision = tp / (tp + fp)
    else:
        precision = 0.0

    if tp + fn > 0:
        recall = tp / (tp + fn)
    else:
        recall = 0.0

    if precision + recall > 0:
        f1 = 2 * precision * recall / (precision + recall)
    else:
        f1 = 0.0

    return precision, recall, f1


# ============================================================
# PER-TECHNIQUE STATISTICS
# ============================================================

def calculate_technique_stats(results):

    stats = defaultdict(
        lambda: {
            "tp": 0,
            "fp": 0,
            "fn": 0
        }
    )

    for result in results:

        ground_truth = set(result["ground_truth"])
        prediction = set(result["prediction"])

        for technique in prediction & ground_truth:
            stats[technique]["tp"] += 1

        for technique in prediction - ground_truth:
            stats[technique]["fp"] += 1

        for technique in ground_truth - prediction:
            stats[technique]["fn"] += 1

    return stats


def print_technique_performance(results):

    stats = calculate_technique_stats(results)

    rows = []

    for technique, values in stats.items():

        tp = values["tp"]
        fp = values["fp"]
        fn = values["fn"]

        precision, recall, f1 = calculate_scores(
            tp,
            fp,
            fn
        )

        support = tp + fn

        rows.append(
            (
                technique,
                support,
                precision,
                recall,
                f1,
                tp,
                fp,
                fn
            )
        )

    rows.sort(
        key=lambda row: row[4],
        reverse=True
    )

    print("\n" + "=" * 80)
    print("PER-TECHNIQUE PERFORMANCE")
    print("=" * 80)

    print(
        f"{'Technique':<15}"
        f"{'Support':>9}"
        f"{'Precision':>12}"
        f"{'Recall':>10}"
        f"{'F1':>10}"
        f"{'TP':>7}"
        f"{'FP':>7}"
        f"{'FN':>7}"
    )

    print("-" * 80)

    for row in rows:

        (
            technique,
            support,
            precision,
            recall,
            f1,
            tp,
            fp,
            fn
        ) = row

        print(
            f"{technique:<15}"
            f"{support:>9}"
            f"{precision:>12.3f}"
            f"{recall:>10.3f}"
            f"{f1:>10.3f}"
            f"{tp:>7}"
            f"{fp:>7}"
            f"{fn:>7}"
        )


# ============================================================
# MISSED TECHNIQUES
# ============================================================

def find_missed_techniques(results):

    missed = Counter()

    for result in results:

        ground_truth = set(result["ground_truth"])
        prediction = set(result["prediction"])

        missing = ground_truth - prediction

        for technique in missing:
            missed[technique] += 1

    return missed


def find_false_positives(results):

    false_positives = Counter()

    for result in results:

        ground_truth = set(result["ground_truth"])
        prediction = set(result["prediction"])

        extra = prediction - ground_truth

        for technique in extra:
            false_positives[technique] += 1

    return false_positives


def print_error_summary(results):

    missed = find_missed_techniques(results)

    false_positives = find_false_positives(results)

    print("\n" + "=" * 60)
    print("MOST MISSED TECHNIQUES")
    print("=" * 60)

    for technique, count in missed.most_common(15):

        print(
            f"{technique:<15}"
            f"{count:>6} misses"
        )

    print("\n" + "=" * 60)
    print("MOST COMMON FALSE POSITIVES")
    print("=" * 60)

    for technique, count in false_positives.most_common(15):

        print(
            f"{technique:<15}"
            f"{count:>6} false positives"
        )


# ============================================================
# EXACT MATCH ANALYSIS
# ============================================================

def analyze_exact_matches(results):

    exact_matches = []
    incorrect = []

    for result in results:

        ground_truth = set(result["ground_truth"])
        prediction = set(result["prediction"])

        if prediction == ground_truth:

            exact_matches.append(result)

        else:

            incorrect.append(result)

    print("\n" + "=" * 60)
    print("EXACT MATCH ANALYSIS")
    print("=" * 60)

    print(
        f"Exact matches: {len(exact_matches)}"
    )

    print(
        f"Incorrect: {len(incorrect)}"
    )

    return exact_matches, incorrect


# ============================================================
# REPRESENTATIVE ERRORS
# ============================================================

def show_representative_errors(
    results,
    limit=10
):

    print("\n" + "=" * 80)
    print("REPRESENTATIVE ERRORS")
    print("=" * 80)

    shown = 0

    for result in results:

        ground_truth = set(result["ground_truth"])
        prediction = set(result["prediction"])

        if prediction == ground_truth:
            continue

        print("\n" + "-" * 80)

        print(
            f"Example ID: {result['id']}"
        )

        print(
            f"\nGround truth:\n"
            f"{sorted(ground_truth)}"
        )

        print(
            f"\nPrediction:\n"
            f"{sorted(prediction)}"
        )

        missing = ground_truth - prediction

        extra = prediction - ground_truth

        print(
            f"\nMissed:\n"
            f"{sorted(missing)}"
        )

        print(
            f"\nFalse positives:\n"
            f"{sorted(extra)}"
        )

        print(
            f"\nText:\n"
            f"{result['text'][:500]}"
        )

        shown += 1

        if shown >= limit:
            break


# ============================================================
# SINGLE VS MULTI LABEL
# ============================================================

def analyze_single_vs_multi_label(results):

    single_label = []
    multi_label = []

    for result in results:

        ground_truth = set(result["ground_truth"])
        prediction = set(result["prediction"])

        if len(ground_truth) == 1:

            single_label.append(
                (
                    ground_truth,
                    prediction
                )
            )

        else:

            multi_label.append(
                (
                    ground_truth,
                    prediction
                )
            )

    print("\n" + "=" * 70)
    print("SINGLE-LABEL VS MULTI-LABEL PERFORMANCE")
    print("=" * 70)

    for name, examples in [
        ("Single-label", single_label),
        ("Multi-label", multi_label)
    ]:

        if not examples:
            continue

        total_tp = 0
        total_fp = 0
        total_fn = 0
        exact = 0

        for ground_truth, prediction in examples:

            total_tp += len(
                ground_truth & prediction
            )

            total_fp += len(
                prediction - ground_truth
            )

            total_fn += len(
                ground_truth - prediction
            )

            if ground_truth == prediction:

                exact += 1

        precision, recall, f1 = calculate_scores(
            total_tp,
            total_fp,
            total_fn
        )

        print(f"\n{name}")

        print("-" * 40)

        print(
            f"Examples:       {len(examples)}"
        )

        print(
            f"Exact matches:  {exact}"
        )

        print(
            f"Exact match %:  "
            f"{exact / len(examples):.3f}"
        )

        print(
            f"Precision:      {precision:.3f}"
        )

        print(
            f"Recall:         {recall:.3f}"
        )

        print(
            f"F1:             {f1:.3f}"
        )


# ============================================================
# TEST FREQUENCY VS PERFORMANCE
# ============================================================

def analyze_frequency_buckets(results):

    technique_stats = calculate_technique_stats(
        results
    )

    buckets = {
        "1-2": [],
        "3-5": [],
        "6-10": [],
        "11-20": [],
        "21-50": [],
        "51+": []
    }

    for technique, values in technique_stats.items():

        support = (
            values["tp"]
            + values["fn"]
        )

        if support <= 2:

            bucket = "1-2"

        elif support <= 5:

            bucket = "3-5"

        elif support <= 10:

            bucket = "6-10"

        elif support <= 20:

            bucket = "11-20"

        elif support <= 50:

            bucket = "21-50"

        else:

            bucket = "51+"

        _, _, f1 = calculate_scores(
            values["tp"],
            values["fp"],
            values["fn"]
        )

        buckets[bucket].append(f1)

    print("\n" + "=" * 70)
    print("TEST FREQUENCY VS PERFORMANCE")
    print("=" * 70)

    for bucket, scores in buckets.items():

        if not scores:
            continue

        average_f1 = (
            sum(scores)
            / len(scores)
        )

        print(
            f"Test support {bucket:<6}"
            f"Techniques: {len(scores):>3}   "
            f"Average F1: {average_f1:.3f}"
        )


# ============================================================
# ERROR TYPE BREAKDOWN
# ============================================================

def analyze_error_types(results):

    counts = Counter()

    for result in results:

        ground_truth = set(
            result["ground_truth"]
        )

        prediction = set(
            result["prediction"]
        )

        if prediction == ground_truth:

            counts["Exact match"] += 1

            continue

        if not prediction:

            counts["Complete miss"] += 1

            continue

        if not (
            prediction - ground_truth
        ):

            counts["Underprediction only"] += 1

            continue

        if not (
            ground_truth - prediction
        ):

            counts["Overprediction only"] += 1

            continue

        counts["Mixed error"] += 1

    print("\n" + "=" * 70)
    print("ERROR TYPE BREAKDOWN")
    print("=" * 70)

    total = len(results)

    for error_type, count in counts.most_common():

        percentage = count / total

        print(
            f"{error_type:<25}"
            f"{count:>6}"
            f" ({percentage:.3f})"
        )


# ============================================================
# TRAINING FREQUENCY VS TEST PERFORMANCE
# ============================================================

def analyze_training_frequency_vs_performance(
    train_path,
    test_results
):

    # --------------------------------------------------------
    # Load prepared training dataset
    # --------------------------------------------------------

    with open(
        train_path,
        "r",
        encoding="utf-8"
    ) as f:

        train_data = json.load(f)

    # --------------------------------------------------------
    # Count how many training examples contain each technique
    # --------------------------------------------------------

    train_counts = Counter()

    for example in train_data:

        assistant_output = (
            example["messages"][2]["content"]
        )

        output = json.loads(
            assistant_output
        )

        techniques = set(
            output["techniques"]
        )

        for technique in techniques:

            train_counts[technique] += 1

    # --------------------------------------------------------
    # Calculate test performance
    # --------------------------------------------------------

    test_stats = calculate_technique_stats(
        test_results
    )

    rows = []

    for technique, values in test_stats.items():

        test_support = (
            values["tp"]
            + values["fn"]
        )

        precision, recall, f1 = calculate_scores(
            values["tp"],
            values["fp"],
            values["fn"]
        )

        train_support = train_counts.get(
            technique,
            0
        )

        rows.append(
            (
                technique,
                train_support,
                test_support,
                precision,
                recall,
                f1
            )
        )

    # Sort from least training examples to most

    rows.sort(
        key=lambda row: row[1]
    )

    # --------------------------------------------------------
    # Print technique-level results
    # --------------------------------------------------------

    print("\n" + "=" * 90)
    print("TRAINING FREQUENCY VS TEST PERFORMANCE")
    print("=" * 90)

    print(
        f"{'Technique':<15}"
        f"{'Train':>10}"
        f"{'Test':>10}"
        f"{'Precision':>12}"
        f"{'Recall':>10}"
        f"{'F1':>10}"
    )

    print("-" * 90)

    for row in rows:

        (
            technique,
            train_support,
            test_support,
            precision,
            recall,
            f1
        ) = row

        print(
            f"{technique:<15}"
            f"{train_support:>10}"
            f"{test_support:>10}"
            f"{precision:>12.3f}"
            f"{recall:>10.3f}"
            f"{f1:>10.3f}"
        )

    # --------------------------------------------------------
    # Training-frequency buckets
    # --------------------------------------------------------

    buckets = {
        "1-5": [],
        "6-10": [],
        "11-25": [],
        "26-50": [],
        "51-100": [],
        "101+": []
    }

    for row in rows:

        train_support = row[1]
        f1 = row[5]

        if train_support <= 5:

            bucket = "1-5"

        elif train_support <= 10:

            bucket = "6-10"

        elif train_support <= 25:

            bucket = "11-25"

        elif train_support <= 50:

            bucket = "26-50"

        elif train_support <= 100:

            bucket = "51-100"

        else:

            bucket = "101+"

        buckets[bucket].append(f1)

    print("\n" + "=" * 70)
    print("TRAINING FREQUENCY BUCKETS")
    print("=" * 70)

    for bucket, scores in buckets.items():

        if not scores:
            continue

        average_f1 = (
            sum(scores)
            / len(scores)
        )

        print(
            f"Train support {bucket:<7}"
            f"Techniques: {len(scores):>3}   "
            f"Average F1: {average_f1:.3f}"
        )


# ============================================================
# BASE VS FINE-TUNED COMPARISON
# ============================================================

def compare_models(
    base_results,
    finetuned_results
):

    base_exact = 0
    finetuned_exact = 0

    base_better = 0
    finetuned_better = 0
    same = 0

    for base, fine in zip(
        base_results,
        finetuned_results
    ):

        base_prediction = set(
            base["prediction"]
        )

        fine_prediction = set(
            fine["prediction"]
        )

        ground_truth = set(
            fine["ground_truth"]
        )

        base_tp = len(
            base_prediction
            & ground_truth
        )

        fine_tp = len(
            fine_prediction
            & ground_truth
        )

        if base_prediction == ground_truth:

            base_exact += 1

        if fine_prediction == ground_truth:

            finetuned_exact += 1

        if fine_tp > base_tp:

            finetuned_better += 1

        elif base_tp > fine_tp:

            base_better += 1

        else:

            same += 1

    print("\n" + "=" * 60)
    print("MODEL-BY-MODEL EXAMPLE COMPARISON")
    print("=" * 60)

    print(
        f"Base exact matches: "
        f"{base_exact}"
    )

    print(
        f"CyberSecLM exact matches: "
        f"{finetuned_exact}"
    )

    print(
        f"CyberSecLM better: "
        f"{finetuned_better}"
    )

    print(
        f"Base better: "
        f"{base_better}"
    )

    print(
        f"Same number of correct labels: "
        f"{same}"
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print("=" * 80)
    print("CyberSecLM TRAM Error Analysis")
    print("=" * 80)

    # --------------------------------------------------------
    # Load evaluation results
    # --------------------------------------------------------

    base_data = load_results(
        BASE_RESULTS_PATH
    )

    finetuned_data = load_results(
        FINETUNED_RESULTS_PATH
    )

    base_results = base_data["results"]

    finetuned_results = (
        finetuned_data["results"]
    )

    print(
        f"\nBase examples: "
        f"{len(base_results)}"
    )

    print(
        f"CyberSecLM examples: "
        f"{len(finetuned_results)}"
    )

    print("\n\n")

    # --------------------------------------------------------
    # 1. Per-technique performance
    # --------------------------------------------------------

    print("CYBERSECLM ANALYSIS")

    print_technique_performance(
        finetuned_results
    )

    # --------------------------------------------------------
    # 2. Most missed + false positives
    # --------------------------------------------------------

    print_error_summary(
        finetuned_results
    )

    # --------------------------------------------------------
    # 3. Exact-match analysis
    # --------------------------------------------------------

    analyze_exact_matches(
        finetuned_results
    )

    # --------------------------------------------------------
    # 4. Representative errors
    # --------------------------------------------------------

    show_representative_errors(
        finetuned_results,
        limit=10
    )

    # --------------------------------------------------------
    # 5. Single-label vs multi-label
    # --------------------------------------------------------

    analyze_single_vs_multi_label(
        finetuned_results
    )

    # --------------------------------------------------------
    # 6. Test frequency vs performance
    # --------------------------------------------------------

    analyze_frequency_buckets(
        finetuned_results
    )

    # --------------------------------------------------------
    # 7. Error type breakdown
    # --------------------------------------------------------

    analyze_error_types(
        finetuned_results
    )

    # --------------------------------------------------------
    # 8. Training frequency vs test performance
    # --------------------------------------------------------

    analyze_training_frequency_vs_performance(
        TRAIN_DATASET_PATH,
        finetuned_results
    )

    # --------------------------------------------------------
    # 9. Base vs fine-tuned comparison
    # --------------------------------------------------------

    compare_models(
        base_results,
        finetuned_results
    )

    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)

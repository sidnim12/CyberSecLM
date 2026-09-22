import json


# -------------------------
# Load data
# -------------------------

with open("data/cti_baseline_predictions.json", "r") as file:
    predictions = json.load(file)

with open("data/cti_ground_truth.json", "r") as file:
    ground_truth = json.load(file)


# -------------------------
# Initialize TP / FP / FN
# -------------------------

total_technique_tp = 0
total_technique_fp = 0
total_technique_fn = 0

total_entity_tp = 0
total_entity_fp = 0
total_entity_fn = 0

total_vulnerability_tp = 0
total_vulnerability_fp = 0
total_vulnerability_fn = 0

total_ioc_tp = 0
total_ioc_fp = 0
total_ioc_fn = 0


# -------------------------
# Evaluate each sample
# -------------------------

for prediction_item, truth_item in zip(predictions, ground_truth):

    try:
        prediction = json.loads(prediction_item["prediction"])
    except json.JSONDecodeError:
        prediction = None

    print(f"ID: {prediction_item['id']}")

    if prediction is None:
        print("Invalid JSON")
        print()
        continue

    # -------------------------
    # Count-level comparison
    # -------------------------

    print("Predicted techniques:", len(prediction["techniques"]))
    print("True techniques:", len(truth_item["techniques"]))

    print("Predicted entities:", len(prediction["entities"]))
    print("True entities:", len(truth_item["entities"]))

    print("Predicted vulnerabilities:", len(prediction["vulnerabilities"]))
    print("True vulnerabilities:", len(truth_item["vulnerabilities"]))

    print("Predicted IOCs:", len(prediction["iocs"]))
    print("True IOCs:", len(truth_item["iocs"]))

    # -------------------------
    # Technique matching
    # -------------------------

    predicted_techniques = {
        technique["id"].strip().upper()
        for technique in prediction["techniques"]
        if technique["id"].strip()
    }

    true_techniques = {
        technique["id"].strip().upper()
        for technique in truth_item["techniques"]
        if technique["id"].strip()
    }

    matched_techniques = predicted_techniques & true_techniques

    print()
    print("Matched techniques:", len(matched_techniques))
    print("Predicted technique IDs:", predicted_techniques)
    print("True technique IDs:", true_techniques)
    print("Missing techniques:", true_techniques - predicted_techniques)
    print("Incorrect techniques:", predicted_techniques - true_techniques)

    # -------------------------
    # Entity matching
    # -------------------------

    predicted_entities = {
        entity["name"].strip().lower()
        for entity in prediction["entities"]
        if entity["name"].strip()
    }

    true_entities = {
        entity["name"].strip().lower()
        for entity in truth_item["entities"]
        if entity["name"].strip()
    }

    matched_entities = predicted_entities & true_entities

    print()
    print("Matched entities:", len(matched_entities))
    print("Predicted entity names:", predicted_entities)
    print("True entity names:", true_entities)

    # -------------------------
    # Vulnerability matching
    # -------------------------

    predicted_vulnerabilities = {
        vulnerability["cve_id"].strip().lower()
        for vulnerability in prediction["vulnerabilities"]
        if vulnerability["cve_id"].strip()
    }

    true_vulnerabilities = {
        vulnerability["cve_id"].strip().lower()
        for vulnerability in truth_item["vulnerabilities"]
        if vulnerability["cve_id"].strip()
    }

    matched_vulnerabilities = (
        predicted_vulnerabilities & true_vulnerabilities
    )

    print()
    print("Matched vulnerabilities:", len(matched_vulnerabilities))
    print("Predicted CVEs:", predicted_vulnerabilities)
    print("True CVEs:", true_vulnerabilities)

    # -------------------------
    # IOC matching
    # -------------------------

    predicted_iocs = {
        (
            ioc["type"].strip().lower(),
            ioc["value"].strip().lower()
        )
        for ioc in prediction["iocs"]
        if ioc["type"].strip() and ioc["value"].strip()
    }

    true_iocs = {
        (
            ioc["type"].strip().lower(),
            ioc["value"].strip().lower()
        )
        for ioc in truth_item["iocs"]
        if ioc["type"].strip() and ioc["value"].strip()
    }

    matched_iocs = predicted_iocs & true_iocs

    print()
    print("Matched IOCs:", len(matched_iocs))
    print("Predicted IOCs:", predicted_iocs)
    print("True IOCs:", true_iocs)

    # -------------------------
    # Accumulate TP / FP / FN
    # -------------------------

    total_technique_tp += len(matched_techniques)
    total_technique_fp += len(
        predicted_techniques - true_techniques
    )
    total_technique_fn += len(
        true_techniques - predicted_techniques
    )

    total_entity_tp += len(matched_entities)
    total_entity_fp += len(
        predicted_entities - true_entities
    )
    total_entity_fn += len(
        true_entities - predicted_entities
    )

    total_vulnerability_tp += len(matched_vulnerabilities)
    total_vulnerability_fp += len(
        predicted_vulnerabilities - true_vulnerabilities
    )
    total_vulnerability_fn += len(
        true_vulnerabilities - predicted_vulnerabilities
    )

    total_ioc_tp += len(matched_iocs)
    total_ioc_fp += len(
        predicted_iocs - true_iocs
    )
    total_ioc_fn += len(
        true_iocs - predicted_iocs
    )


# -------------------------
# Metric calculation
# -------------------------

def calculate_metrics(tp, fp, fn):

    if tp + fp == 0:
        precision = 0.0
    else:
        precision = tp / (tp + fp)

    if tp + fn == 0:
        recall = 0.0
    else:
        recall = tp / (tp + fn)

    if precision + recall == 0:
        f1 = 0.0
    else:
        f1 = 2 * precision * recall / (precision + recall)

    return precision, recall, f1


# -------------------------
# Calculate final metrics
# -------------------------

technique_precision, technique_recall, technique_f1 = calculate_metrics(
    total_technique_tp,
    total_technique_fp,
    total_technique_fn
)

entity_precision, entity_recall, entity_f1 = calculate_metrics(
    total_entity_tp,
    total_entity_fp,
    total_entity_fn
)

vulnerability_precision, vulnerability_recall, vulnerability_f1 = calculate_metrics(
    total_vulnerability_tp,
    total_vulnerability_fp,
    total_vulnerability_fn
)

ioc_precision, ioc_recall, ioc_f1 = calculate_metrics(
    total_ioc_tp,
    total_ioc_fp,
    total_ioc_fn
)


# -------------------------
# Print final metrics
# -------------------------

print("\n===== FINAL METRICS =====")

print(
    f"Techniques      | "
    f"Precision: {technique_precision:.3f} | "
    f"Recall: {technique_recall:.3f} | "
    f"F1: {technique_f1:.3f}"
)

print(
    f"Entities        | "
    f"Precision: {entity_precision:.3f} | "
    f"Recall: {entity_recall:.3f} | "
    f"F1: {entity_f1:.3f}"
)

print(
    f"Vulnerabilities | "
    f"Precision: {vulnerability_precision:.3f} | "
    f"Recall: {vulnerability_recall:.3f} | "
    f"F1: {vulnerability_f1:.3f}"
)

print(
    f"IOCs            | "
    f"Precision: {ioc_precision:.3f} | "
    f"Recall: {ioc_recall:.3f} | "
    f"F1: {ioc_f1:.3f}"
)
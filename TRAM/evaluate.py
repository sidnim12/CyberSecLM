import json
from pathlib import Path

import torch
from peft import PeftModel
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
)


# ============================================================
# 1. PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

TEST_DATASET_PATH = (
    PROJECT_ROOT
    / "data"
    / "tram"
    / "prepared"
    / "test.json"
)

EVALUATION_DIR = (
    PROJECT_ROOT
    / "experiments"
    / "evaluation"
)

MODEL_NAME = "Qwen/Qwen3-4B-Instruct-2507"

ADAPTER_PATH = (
    PROJECT_ROOT
    / "experiments"
    / "cyberseclm-tram-qlora"
)


# ============================================================
# 2. LOAD BASE MODEL
# ============================================================

def load_base_model():

    quantization_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )

    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_NAME
    )

    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        quantization_config=quantization_config,
        device_map="auto",
    )

    return tokenizer, model


# ============================================================
# 3. LOAD FINE-TUNED MODEL
# ============================================================

def load_finetuned_model():

    tokenizer, model = load_base_model()

    model = PeftModel.from_pretrained(
        model,
        ADAPTER_PATH,
    )

    return tokenizer, model


# ============================================================
# 4. LOAD TEST DATASET
# ============================================================

def load_test_dataset():

    with open(
        TEST_DATASET_PATH,
        "r",
        encoding="utf-8",
    ) as f:

        return json.load(f)


# ============================================================
# 5. EXTRACT GROUND TRUTH
# ============================================================

def extract_ground_truth(example):

    assistant_output = (
        example["messages"][2]["content"]
    )

    output = json.loads(
        assistant_output
    )

    return set(
        output["techniques"]
    )


# ============================================================
# 6. PARSE MODEL OUTPUT
# ============================================================

def parse_prediction(response):

    response = response.strip()

    # Handle Markdown code fences.
    if response.startswith("```"):

        lines = response.splitlines()

        if lines[0].startswith("```"):
            lines = lines[1:]

        if (
            lines
            and lines[-1].strip() == "```"
        ):
            lines = lines[:-1]

        response = "\n".join(
            lines
        ).strip()

    try:

        output = json.loads(
            response
        )

    except json.JSONDecodeError:

        return set(), False

    techniques = output.get(
        "techniques",
        []
    )

    if not isinstance(
        techniques,
        list,
    ):

        return set(), False

    techniques = {
        technique
        for technique in techniques
        if isinstance(
            technique,
            str,
        )
    }

    return techniques, True


# ============================================================
# 7. GENERATE PREDICTION
# ============================================================

def generate_prediction(
    model,
    tokenizer,
    example,
):

    messages = example[
        "messages"
    ][:2]

    inputs = tokenizer.apply_chat_template(
        messages,
        tokenize=True,
        add_generation_prompt=True,
        return_tensors="pt",
    ).to(model.device)

    with torch.no_grad():

        output = model.generate(
            **inputs,
            max_new_tokens=100,
            do_sample=False,
        )

    generated_ids = output[0][
        inputs["input_ids"].shape[-1]:
    ]

    response = tokenizer.decode(
        generated_ids,
        skip_special_tokens=True,
    )

    return response


# ============================================================
# 8. CALCULATE METRICS
# ============================================================

def calculate_metrics(results):

    true_positive = 0
    false_positive = 0
    false_negative = 0

    exact_matches = 0

    for result in results:

        predicted = set(
            result["prediction"]
        )

        ground_truth = set(
            result["ground_truth"]
        )

        true_positive += len(
            predicted & ground_truth
        )

        false_positive += len(
            predicted - ground_truth
        )

        false_negative += len(
            ground_truth - predicted
        )

        if predicted == ground_truth:

            exact_matches += 1

    if true_positive + false_positive > 0:

        precision = (
            true_positive
            / (
                true_positive
                + false_positive
            )
        )

    else:

        precision = 0.0

    if true_positive + false_negative > 0:

        recall = (
            true_positive
            / (
                true_positive
                + false_negative
            )
        )

    else:

        recall = 0.0

    if precision + recall > 0:

        f1 = (
            2
            * precision
            * recall
            / (
                precision
                + recall
            )
        )

    else:

        f1 = 0.0

    exact_match = (
        exact_matches
        / len(results)
    )

    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "exact_match": exact_match,
        "true_positive": true_positive,
        "false_positive": false_positive,
        "false_negative": false_negative,
    }


# ============================================================
# 9. EVALUATE MODEL
# ============================================================

def evaluate_model(
    model_name,
    model,
    tokenizer,
    test_data,
):

    print("\n" + "=" * 60)
    print(
        f"EVALUATING: {model_name}"
    )
    print("=" * 60)

    results = []

    parse_errors = 0

    for index, example in enumerate(
        test_data,
        start=1,
    ):

        ground_truth = (
            extract_ground_truth(
                example
            )
        )

        raw_response = (
            generate_prediction(
                model,
                tokenizer,
                example,
            )
        )

        prediction, valid_json = (
            parse_prediction(
                raw_response
            )
        )

        if not valid_json:

            parse_errors += 1

        results.append(
            {
                "id": index,

                "text": (
                    example[
                        "messages"
                    ][1]["content"]
                ),

                "ground_truth": sorted(
                    ground_truth
                ),

                "prediction": sorted(
                    prediction
                ),

                "raw_response": (
                    raw_response
                ),

                "valid_json": (
                    valid_json
                ),
            }
        )

        if (
            index % 25 == 0
            or index == len(test_data)
        ):

            print(
                f"Processed "
                f"{index}/{len(test_data)}"
            )

    metrics = calculate_metrics(
        results
    )

    print("\n----- RESULTS -----")

    print(
        f"Precision:   "
        f"{metrics['precision']:.4f}"
    )

    print(
        f"Recall:      "
        f"{metrics['recall']:.4f}"
    )

    print(
        f"F1:          "
        f"{metrics['f1']:.4f}"
    )

    print(
        f"Exact Match: "
        f"{metrics['exact_match']:.4f}"
    )

    print(
        f"TP: {metrics['true_positive']}"
    )

    print(
        f"FP: {metrics['false_positive']}"
    )

    print(
        f"FN: {metrics['false_negative']}"
    )

    print(
        f"JSON parse errors: "
        f"{parse_errors}"
    )

    return results, metrics


# ============================================================
# 10. SAVE RESULTS
# ============================================================

def save_results(
    filename,
    model_name,
    results,
    metrics,
):

    EVALUATION_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = (
        EVALUATION_DIR
        / filename
    )

    output = {

        "model": model_name,

        "metrics": metrics,

        "results": results,
    }

    with open(
        output_path,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            output,
            f,
            indent=2,
            ensure_ascii=False,
        )

    print(
        f"\nSaved results to:"
        f"\n{output_path}"
    )


# ============================================================
# 11. MAIN
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("CyberSecLM TRAM Evaluation")
    print("=" * 60)

    test_data = (
        load_test_dataset()
    )

    print(
        f"\nTest examples: "
        f"{len(test_data)}"
    )

    # --------------------------------------------------------
    # BASE MODEL
    # --------------------------------------------------------

    tokenizer, base_model = (
        load_base_model()
    )

    base_results, base_metrics = (
        evaluate_model(
            "BASE QWEN3-4B",
            base_model,
            tokenizer,
            test_data,
        )
    )

    save_results(
        "base_predictions.json",
        "BASE QWEN3-4B",
        base_results,
        base_metrics,
    )

    del base_model

    torch.cuda.empty_cache()

    # --------------------------------------------------------
    # FINE-TUNED MODEL
    # --------------------------------------------------------

    tokenizer, finetuned_model = (
        load_finetuned_model()
    )

    finetuned_results, finetuned_metrics = (
        evaluate_model(
            "CYBERSECLM QLORA",
            finetuned_model,
            tokenizer,
            test_data,
        )
    )

    save_results(
        "finetuned_predictions.json",
        "CYBERSECLM QLORA",
        finetuned_results,
        finetuned_metrics,
    )

    # --------------------------------------------------------
    # FINAL COMPARISON
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("FINAL COMPARISON")
    print("=" * 60)

    print(
        f"\n{'Metric':<15}"
        f"{'Base':>12}"
        f"{'CyberSecLM':>15}"
    )

    print("-" * 42)

    print(
        f"{'Precision':<15}"
        f"{base_metrics['precision']:>12.4f}"
        f"{finetuned_metrics['precision']:>15.4f}"
    )

    print(
        f"{'Recall':<15}"
        f"{base_metrics['recall']:>12.4f}"
        f"{finetuned_metrics['recall']:>15.4f}"
    )

    print(
        f"{'F1':<15}"
        f"{base_metrics['f1']:>12.4f}"
        f"{finetuned_metrics['f1']:>15.4f}"
    )

    print(
        f"{'Exact Match':<15}"
        f"{base_metrics['exact_match']:>12.4f}"
        f"{finetuned_metrics['exact_match']:>15.4f}"
    )

    print("\nEvaluation complete!")
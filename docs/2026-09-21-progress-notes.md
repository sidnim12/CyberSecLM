# CyberSecLM Progress Notes — 2026-09-21

## Objective

Move from manual inspection of CTI responses to a repeatable baseline evaluation pipeline.

## Ground truth

Created a ground-truth answer key for the five CTI baseline samples. Each entry contains the expected entities, ATT&CK techniques, vulnerabilities, IOCs, and supporting evidence.

The ground truth is kept separate from model input. It is used only to compare expected output with the base model's predictions.

## Saving baseline predictions

Updated `src/baseline.py` so that generated responses are collected with their sample IDs and written to `data/cti_baseline_predictions.json`.

This changed the baseline workflow from terminal-only output to reusable experiment data:

```text
CTI samples → Base Qwen → Saved predictions
```

## Inference issue resolved

The baseline initially failed because the result of `apply_chat_template()` was passed incorrectly to `model.generate()`.

With the installed Transformers version, the chat template returns a dictionary-like `BatchEncoding`. The model inputs must therefore be unpacked:

```python
model.generate(**input_ids)
```

The generated portion is separated from the prompt using:

```python
input_ids["input_ids"].shape[-1]
```

The generation limit was increased to 500 tokens to reduce truncated JSON responses.

## Initial evaluator

Created `src/evaluate.py` to compare saved predictions against the ground truth. The first evaluator:

- Loads predictions and ground truth
- Matches samples in their stored order
- Handles invalid prediction JSON without stopping the entire run
- Normalizes case and whitespace
- Uses set intersections and differences to count matches, missing items, and incorrect items
- Calculates micro precision, recall, and F1

The current matching keys are:

| Category | Matching value |
| --- | --- |
| Techniques | ATT&CK technique ID |
| Entities | Entity name |
| Vulnerabilities | CVE ID |
| IOCs | IOC type and value |

## Baseline results

The initial five-sample evaluation produced:

| Category | Precision | Recall | F1 |
| --- | ---: | ---: | ---: |
| Techniques | 0.000 | 0.000 | 0.000 |
| Entities | 0.667 | 0.500 | 0.571 |
| Vulnerabilities | 1.000 | 1.000 | 1.000 |
| IOCs | 1.000 | 1.000 | 1.000 |

These values describe only the five-sample prototype and are not final research results. The technique score confirms the previously observed problem: the base model understands portions of the text but does not reliably place techniques and ATT&CK IDs into the required schema.

## Next step

Prepare schema-consistent train, validation, and test examples for the first QLoRA experiment while keeping the test sample out of training.

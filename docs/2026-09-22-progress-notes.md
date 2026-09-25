# CyberSecLM Progress Notes — 2026-09-22

## Objective

Prepare and validate the first QLoRA experiment, then inspect the TRAM dataset as a possible source for broader ATT&CK-focused dataset development.

## Dataset splits

Created chat-formatted CTI datasets:

- `data/cti_train.json`: 3 examples
- `data/cti_validation.json`: 1 example
- `data/cti_test.json`: 1 example

Each example contains three messages in this order:

```text
system → user → assistant
```

The assistant message contains the target structured CTI output as a JSON string.

Created `src/validate_dataset.py` to verify:

- The `messages` field exists
- Each example has exactly three messages
- Roles appear in the required order
- Message content is text
- The assistant output is valid JSON
- All five top-level schema fields are present

All three dataset splits passed validation.

## QLoRA setup

Added the initial QLoRA workflow:

- `src/qlora_test.py` tests loading Qwen in 4-bit mode and running inference.
- `src/qlora_model.py` prepares the quantized model and attaches LoRA adapters.
- `src/train.py` loads the training split and runs supervised fine-tuning with TRL's `SFTTrainer`.
- `src/test_adapter.py` loads the saved adapter and runs a CTI extraction test.

The current configuration uses:

| Setting | Value |
| --- | --- |
| Quantization | 4-bit NF4 with double quantization |
| Compute type | bfloat16 |
| LoRA rank | 16 |
| LoRA alpha | 32 |
| LoRA dropout | 0.05 |
| Target modules | `q_proj`, `k_proj`, `v_proj`, `o_proj` |
| Epochs | 3 |
| Batch size | 1 |
| Gradient accumulation | 4 |
| Learning rate | 2e-4 |
| Optimizer | paged AdamW 8-bit |

The initial training run produced adapter and checkpoint artifacts under `experiments/cyberseclm-qlora`. These generated files are excluded from Git because model weights and training checkpoints should not be stored in the repository.

## TRAM dataset analysis

Added three scripts under `TRAM/`:

- `analyze.py` measures dataset, label, and document statistics.
- `label_analysis.py` measures how widely each technique appears across documents.
- `cooccurance.py` counts pairs of techniques assigned to the same example.

The analyzed TRAM dataset contains:

| Statistic | Value |
| --- | ---: |
| Total examples | 19,178 |
| Labeled examples | 4,070 |
| Unlabeled examples | 15,108 |
| Unique techniques | 50 |
| Unique documents | 151 |
| Documents containing labeled examples | 149 |
| Average labels per labeled example | 1.26 |
| Multi-label examples | 831 |
| Unique technique pairs | 481 |

The most frequent techniques include `T1027`, `T1140`, `T1059.003`, `T1055`, and `T1105`. The most frequent co-occurrence is `T1027 + T1140`, appearing 101 times.

Technique coverage is imbalanced. `T1027` appears across 109 documents, while `T1557.001` appears in only one. This imbalance must be considered when creating data splits and reporting per-technique performance.

## Repository update

Committed and pushed the QLoRA source code, dataset splits, validation utility, and TRAM analysis scripts to `sid-exp` in commit `a9af7d4`.

Updated `.gitignore` to exclude virtual environments, Python caches, environment files, and generated QLoRA experiment artifacts.

## Next step

Evaluate the trained adapter on the held-out test example using the same schema and metrics as the base model. Because the current dataset is extremely small, treat this run as a pipeline test rather than evidence of model improvement. The next research task is to define how TRAM examples can be converted into the project's structured extraction format without introducing document leakage.

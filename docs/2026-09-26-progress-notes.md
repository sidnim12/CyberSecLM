# CyberSecLM Progress Notes — 2026-09-26

## Objective

Scale the initial CTI prototype into a document-separated TRAM experiment, train the QLoRA adapter, and compare the fine-tuned model with the original Qwen model on the same held-out test set.

## TRAM dataset pipeline

Added scripts to turn the TRAM multi-label dataset into a reproducible training and evaluation pipeline:

- `TRAM/split_dataset.py` groups examples by source document and creates deterministic 70/15/15 train, validation, and test splits using seed 42.
- `TRAM/split_analysis.py` checks technique coverage across the splits.
- `TRAM/prepare_dataset.py` converts labeled sentences into system, user, and assistant chat messages.
- `src/validate_dataset.py` validates the prepared ATT&CK extraction format.

Splitting by document prevents sentences from the same CTI report from appearing in both training and evaluation data. The verification found no document overlap between the three splits.

The prepared datasets contain:

| Split | Labeled examples | Unique techniques |
| --- | ---: | ---: |
| Train | 2,866 | 50 |
| Validation | 653 | 48 |
| Test | 551 | 47 |

Every validation and test technique is represented in the training split. All three prepared files passed schema and JSON validation.

## TRAM QLoRA training

Updated `src/train.py` to train on the prepared TRAM data and evaluate once per epoch on the validation split. The experiment retains the earlier 4-bit NF4 and LoRA configuration and writes generated adapters and checkpoints under `experiments/cyberseclm-tram-qlora`.

Model weights, optimizer states, tokenizer artifacts, and checkpoints remain excluded from Git. They are reproducible experiment outputs rather than source files.

## Base and fine-tuned evaluation

Added `TRAM/evaluate.py` to run both models on the same 551 held-out examples. It:

- Loads the base model or the trained LoRA adapter
- Generates deterministic predictions
- Parses the expected JSON technique list
- Calculates micro precision, recall, F1, and exact-match accuracy
- Saves predictions and metrics under `experiments/evaluation/`

The measured results are:

| Model | Precision | Recall | F1 | Exact match |
| --- | ---: | ---: | ---: | ---: |
| Base Qwen3-4B | 0.045 | 0.025 | 0.032 | 0.013 |
| CyberSecLM QLoRA | 0.652 | 0.605 | 0.627 | 0.515 |

The fine-tuned model produced 442 true positives, 236 false positives, and 289 false negatives. It exactly matched 284 of 551 test examples, compared with 7 exact matches for the base model.

These results show that task-specific fine-tuning substantially improved ATT&CK technique extraction on this split. They remain specific to TRAM, the current document split, prompt, schema, and training configuration.

## Error analysis

Added `TRAM/analyze_results.py` for per-technique scores, common misses and false positives, representative errors, label-count analysis, and frequency-based analysis.

Key findings include:

- Single-label examples achieved F1 0.673 and exact match 0.649.
- Multi-label examples achieved F1 0.551 and exact match 0.104.
- The model performed better on techniques with more training examples.
- Frequent misses included `T1059.003`, `T1027`, `T1070.004`, and `T1105`.
- Frequent false positives included `T1027`, `T1059.003`, `T1082`, and `T1105`.
- `T1190` achieved perfect precision and recall on 11 test examples, while several rare techniques received zero F1.

The error distribution was:

| Outcome | Examples | Proportion |
| --- | ---: | ---: |
| Exact match | 284 | 0.515 |
| Mixed error | 161 | 0.292 |
| Underprediction only | 77 | 0.140 |
| Overprediction only | 29 | 0.053 |

## Repository presentation

Added `assets/banner.png`. The README maintained on GitHub references it as `assets/banner.png`, so committing the image makes the banner render on the repository page.

## Next step

Preserve this run as the first full TRAM baseline and investigate the main sources of error:

1. Multi-label recall
2. Class imbalance and rare techniques
3. Confusion among semantically related techniques
4. Sensitivity to prompt and generation settings
5. Repeated runs or controlled configurations to measure result stability

After the extraction results are stable and documented, begin constructing temporally ordered ATT&CK sequences for the Markov analysis stage.

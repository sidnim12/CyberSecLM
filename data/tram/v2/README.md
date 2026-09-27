# TRAM v2 cleanup

Status: ready for training-batch inspection.

| Split | Original labeled | V2 labeled | Labels | Longest example |
|---|---:|---:|---:|---:|
| train | 2866 | 2820 | 50 | 826 tokens |
| validation | 653 | 610 | 48 | 399 tokens |
| test | 551 | 551 | 47 | 686 tokens |

## Decisions

- Both conflicting advisory copies excluded from train/validation. Source: https://www.cisa.gov/news-events/cybersecurity-advisories/aa22-320a
- All occurrences of conflicting labeled sentences excluded from train/validation; labels were not guessed.
- Identical labeled rows within a split deduplicated; validation retained over identical training sentences.
- Four oversized configuration/IOC-heavy records quarantined, without truncation or inherited chunk labels.
- Original raw and prepared test files copied byte-for-byte. All v1 source fingerprints unchanged.
- Empty annotations retained in raw data but excluded from prepared examples.
- Prepared examples retain the existing prompt and label format; provenance stored separately.

## Removed labeled records

- over_1024_tokens_quarantined_without_truncation: 4
- conflicting_nonempty_annotations: 2
- duplicate_advisory_with_inconsistent_annotations: 78
- duplicate_labeled_text_within_split: 2
- labeled_text_already_in_validation: 3

## Verification

No shared labeled text, conflicting labeled text, document overlap or over-limit examples in v2.
All validation/test labels remain represented in training. Label frequencies are in audit.json.
Historical/deprecated labels retained for benchmark consistency: ['T1562.001', 'T1574.002'].

## Limits

- Quarantined annotations are excluded, not adjudicated or corrected.
- Unlabeled raw sentences may still overlap; they do not enter supervised training.
- Exact text checks do not establish absence of paraphrase or semantic leakage.
- V2 validation is smaller than v1; compare models on the same v2 validation set.
- The original test set has already been inspected in prior development; it is not a fresh external benchmark.
- Dataset filtering changes the experiment; do not attribute all improvement to the training objective.

## Next training configuration

Use data/tram/v2/prepared/train.json and validation.json; set max_length=1024 explicitly.
Verify assistant token masks before training. Save the new adapter to a separate v2 experiment directory.

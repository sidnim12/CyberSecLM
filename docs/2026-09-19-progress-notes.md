# CyberSecLM Progress Notes — 2026-09-19

## Objective

Move CyberSecLM from general cybersecurity question answering toward a defined task: extracting structured cyber threat intelligence (CTI) from unstructured reports.

## Starting point

The project already had:

- A Python virtual environment
- Hugging Face and Transformers dependencies
- CUDA support on an NVIDIA GeForce RTX 5070 Ti Laptop GPU
- The `Qwen/Qwen3-4B-Instruct-2507` model downloaded and loading locally
- A working inference function
- Basic conversational inference testing
- A Git repository connected to GitHub

Development now takes place on the `sid-exp` branch. Changes should be merged or pushed to `main` only when explicitly requested.

## Generic cybersecurity baseline

The first baseline used 10 questions from `data/baseline_questions.json`. The questions tested general CVE knowledge, including:

- The meaning and purpose of a CVE
- The difference between CVE and CVSS
- CVE assignment
- Vulnerabilities compared with exploits
- Affected software versions
- Extracting CVE identifiers from reports

The base model handled common cybersecurity concepts reasonably well. It could explain CVEs, distinguish CVE from CVSS, and describe vulnerabilities, exploits, and affected versions.

The baseline also revealed limitations:

- Some answers were truncated by the `max_new_tokens=200` generation limit.
- Some procedural answers were oversimplified.
- One question requested extraction from a report but did not provide a report, so it was not a meaningful extraction test.
- Generic question answering did not directly measure the intended CyberSecLM task.

## CTI baseline dataset

The next baseline uses five manually written samples in `data/cti_baseline.json`. Keeping the dataset small allowed the extraction pipeline to be tested before collecting a larger corpus.

The samples cover:

1. Log4j exploitation using CVE-2021-44228 and a malicious JNDI lookup
2. PowerShell payload delivery and Cobalt Strike deployment
3. CVE-2023-23397 affecting Microsoft Outlook
4. RDP-based lateral movement during a ransomware operation
5. Spearphishing, malicious Word macros, PowerShell, and payload download

## Structured extraction pipeline

`src/baseline.py` now reads the CTI samples and builds an explicit extraction prompt for each one:

```text
CTI text
   ↓
Extraction prompt
   ↓
Qwen3-4B
   ↓
Structured JSON-like output
```

The prompt instructs the model to extract only facts explicitly supported by the supplied text and return JSON containing:

- `entities`
- `techniques`
- `vulnerabilities`
- `iocs`
- `evidence`

Entities, techniques, vulnerabilities, IOCs, and evidence use structured objects rather than plain strings. The prompt also tells the model not to invent MITRE ATT&CK technique IDs and to use empty values when information cannot be determined.

## Baseline findings

The base Qwen model demonstrated useful CTI understanding. It successfully extracted examples such as:

- CVE-2021-44228
- Apache Log4j 2.14.1
- Remote code execution
- Cobalt Strike as malware
- A malicious URL as an IOC
- CVE-2023-23397 and Microsoft Outlook

It also showed several consistency problems:

- It sometimes placed a CVE in both `entities` and `vulnerabilities`.
- It missed PowerShell as a technique even when PowerShell was stated explicitly.
- It omitted Microsoft Outlook from `entities` in one result.
- It left some vulnerability fields empty despite supporting language in the text.
- It returned no extracted items for the RDP lateral-movement sample.
- A stricter schema reduced technique recall in the spearphishing sample.
- Some JSON responses were incomplete because generation stopped at the token limit.

The main finding is that understanding the CTI text does not guarantee reliable mapping into the required schema. Schema adherence, category separation, completeness, technique extraction, and evidence consistency remain weak areas.

## Development issues resolved

Several implementation problems were found and corrected during baseline development:

- `baseline_questions.json` initially caused a `JSONDecodeError` because the file was empty on disk. Saving its contents resolved the error.
- `for i in range(data)` was replaced with `for i in data` because the loaded JSON value is a list.
- Conflicting quotes in an f-string were corrected by using `i['text']` inside the expression.
- CTI text remains part of the user prompt; it is not sent as an assistant message.
- The extraction work was added to `baseline.py` without changing the existing inference pipeline for this stage.

## Current project status

| Area | Status |
| --- | --- |
| Project and Python environment | Complete |
| GPU and CUDA setup | Complete |
| Qwen model setup | Complete |
| Basic inference pipeline | Complete |
| Generic cybersecurity baseline | Complete |
| Small CTI baseline dataset | Complete |
| Structured extraction prompt | Complete |
| Initial structured extraction test | Complete |
| Ground-truth dataset | Started, incomplete |
| Evaluation framework | Not started |
| CTI training dataset | Not started |
| QLoRA fine-tuning | Not started |
| ATT&CK temporal modeling | Not started |
| Markov forecasting | Not started |

## Next step

Create ground-truth structured answers for each CTI sample. Predictions can then be compared against expected outputs using measurable criteria such as:

- JSON validity
- Field-level precision, recall, and F1
- Missing and hallucinated entities
- Schema-category errors
- Evidence correctness

This evaluation layer is needed before testing whether QLoRA improves the model.

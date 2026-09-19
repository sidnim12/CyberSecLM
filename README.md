# CyberSecLM

**Domain-Specific LLM for Cyber Threat Intelligence**

CyberSecLM is an experimental domain-specific Large Language Model project focused on **Cyber Threat Intelligence (CTI)**.

The project investigates whether a small open-source language model can be adapted to reliably extract structured, evidence-grounded cybersecurity intelligence from CTI reports using **parameter-efficient fine-tuning (QLoRA)**.

A later stage of the project will use extracted MITRE ATT&CK techniques to model temporal technique transitions with a lightweight **Markov model**.

---

## Project Goal

The core research direction is:

> **Can a resource-efficient, domain-adapted LLM reliably extract structured and temporally ordered cyber-threat intelligence, and can those extracted ATT&CK sequences support lightweight probabilistic forecasting of subsequent techniques?**

The project is designed around a consumer GPU and focuses on improving the capabilities of a relatively small language model rather than relying on large-scale models.

---

## Current Architecture

```text
CTI Report
    │
    ▼
Qwen3-4B-Instruct
    │
    │  QLoRA fine-tuning
    ▼
CyberSecLM
    │
    ▼
Structured CTI Extraction
    │
    ├── Entities
    ├── MITRE ATT&CK Techniques
    ├── Vulnerabilities
    ├── IOCs
    └── Evidence
    │
    ▼
Temporal ATT&CK Sequences
    │
    ▼
Markov Transition Model
    │
    ▼
Probabilistic Next-Technique Estimates
```

---

## Current Model

The initial base model is:

**Qwen/Qwen3-4B-Instruct-2507**

The current baseline uses the pretrained/instruction-tuned model without domain-specific fine-tuning.

QLoRA fine-tuning will be introduced after establishing a measurable baseline.

---

## Current CTI Extraction Task

The first version of CyberSecLM focuses on converting unstructured CTI text into structured information.

The target schema currently contains:

```json
{
  "entities": [],
  "techniques": [],
  "vulnerabilities": [],
  "iocs": [],
  "evidence": []
}
```

### Entities

Examples include:

* Threat actors
* Malware
* Campaigns
* Products

### Techniques

Techniques are intended to contain:

* MITRE ATT&CK technique ID
* Technique name
* Supporting evidence

### Vulnerabilities

Vulnerability records contain:

* CVE ID
* Product
* Version
* Vulnerability type
* Supporting evidence

### IOCs

Currently considered IOC types include:

* IP addresses
* Domains
* Hashes
* URLs

### Evidence

Extracted claims should be grounded in the supplied CTI text.

The model should not invent information that is not supported by the source text.

---

## Baseline Experiments

The first experiments test the base Qwen model before any fine-tuning.

### Generic Cybersecurity QA

An initial set of CVE-related questions was used to verify the model's general cybersecurity knowledge.

The model was generally capable of answering basic questions about:

* CVEs
* CVSS
* Vulnerabilities
* Exploits
* Affected software versions

This established that the model already has useful general cybersecurity knowledge.

### CTI Extraction Baseline

The project then moved to a more relevant task: extracting structured intelligence from CTI snippets.

The initial baseline dataset contains five manually constructed CTI samples covering:

* CVE / Log4j exploitation
* PowerShell and Cobalt Strike
* Microsoft Outlook vulnerability
* RDP-based lateral movement
* Spearphishing and PowerShell execution

The base model demonstrated that it can identify some cybersecurity entities and IOCs, but extraction quality is inconsistent.

Observed baseline issues include:

* Missing techniques
* Incomplete extraction
* Incorrect categorization
* Inconsistent schema adherence
* Missing evidence
* Occasional generation truncation

These observations motivate the need for a formal evaluation dataset and later domain adaptation.

---

## Project Structure

```text
CyberSecLM/
│
├── data/
│   ├── baseline_questions.json
│   └── cti_baseline.json
│
├── src/
│   ├── model.py
│   ├── inference.py
│   ├── baseline.py
│   └── utils.py
│
├── experiments/
│
├── requirements.txt
├── README.md
└── .venv/
```

---

## Development Status

### Completed

* [x] Python environment setup
* [x] CUDA/GPU setup
* [x] Qwen3-4B model loading
* [x] Basic inference pipeline
* [x] Chat-template based inference
* [x] Generic cybersecurity baseline
* [x] Initial CTI extraction dataset
* [x] Initial structured extraction prompt
* [x] Initial CTI baseline experiment

### In Progress

* [ ] Ground-truth CTI annotations
* [ ] Automated evaluation
* [ ] Extraction precision / recall / F1
* [ ] Hallucination analysis
* [ ] Evidence-grounding evaluation

### Planned

* [ ] Larger CTI dataset
* [ ] Dataset cleaning and preprocessing
* [ ] QLoRA fine-tuning
* [ ] Base model vs fine-tuned model comparison
* [ ] MITRE ATT&CK technique extraction evaluation
* [ ] Temporal ATT&CK sequence construction
* [ ] Markov transition modeling
* [ ] Probabilistic next-technique estimation
* [ ] Final experiments and analysis

---

## Technologies

* Python
* PyTorch
* Hugging Face Transformers
* Hugging Face Accelerate
* Hugging Face Hub
* Qwen
* PEFT / LoRA
* QLoRA
* MITRE ATT&CK
* Cyber Threat Intelligence

---

## Hardware

Initial development and experimentation is performed on a consumer gaming laptop equipped with an NVIDIA RTX 5070 Ti Laptop GPU with 12 GB VRAM.

The project intentionally targets resource-efficient experimentation suitable for this hardware constraint.

---

## Research Direction

The project is centered around three connected components:

### 1. Domain Adaptation

Adapt a small language model to cybersecurity and CTI terminology using QLoRA.

### 2. Structured CTI Extraction

Convert unstructured CTI reports into structured, evidence-grounded intelligence, particularly:

* vulnerabilities
* entities
* IOCs
* MITRE ATT&CK techniques
* supporting evidence

### 3. Temporal Threat Modeling

Use extracted ATT&CK techniques as temporal sequences and model transitions between techniques using a lightweight Markov model.

The forecasting component is intended to provide **probabilistic estimates based on historical technique transitions**, rather than deterministic predictions of attacker behavior.

---

## Status

**Early research / experimental stage**

The current implementation establishes the base-model inference and initial CTI extraction baseline. Formal evaluation and QLoRA fine-tuning are the next major stages.

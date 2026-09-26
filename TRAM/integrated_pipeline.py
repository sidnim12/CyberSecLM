# CyberSecLM validated temporal forecasting pipeline

import json
import re
from collections import Counter
from pathlib import Path
from urllib.request import urlopen, Request

import pandas as pd
import torch
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
)
from peft import PeftModel


# ============================================================
# CONFIGURATION
# ============================================================

BASE_MODEL = "Qwen/Qwen3-4B-Instruct-2507"

ADAPTER_PATH = (
    r"C:\Siddu\LLMs\CyberSecLM\experiments\cyberseclm-tram-qlora"
)

DATASET_PATH = (
    r"C:\Siddu\LLMs\Datasets\ChronoCTI-main\ChronoCTI-main"
    r"\Datasets\Dataset\temporal_relation_dataset.xlsx"
)

MITRE_VERSION = "19.2"

MITRE_URL = (
    "https://raw.githubusercontent.com/mitre-attack/"
    "attack-stix-data/master/enterprise-attack/"
    f"enterprise-attack-{MITRE_VERSION}.json"
)

MITRE_CACHE_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / f"enterprise-attack-{MITRE_VERSION}.json"
)

TOP_K = 5

ALLOW_PARENT_FALLBACK_FOR_FORECAST = True


# ============================================================
# MODEL
# ============================================================

def load_cybersec_model():

    print("\nLoading tokenizer...")

    tokenizer = AutoTokenizer.from_pretrained(
        BASE_MODEL
    )

    print("Loading base model in 4-bit...")

    quantization_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
    )

    base_model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        quantization_config=quantization_config,
        device_map="auto",
    )

    print("Loading QLoRA adapter...")

    model = PeftModel.from_pretrained(
        base_model,
        ADAPTER_PATH,
    )

    model.eval()

    print("CyberSecLM loaded successfully!")

    return tokenizer, model


# ============================================================
# MITRE ATT&CK
# ============================================================

def load_mitre_metadata():

    MITRE_CACHE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if not MITRE_CACHE_PATH.exists():

        print(
            f"\nDownloading MITRE ATT&CK Enterprise "
            f"v{MITRE_VERSION}..."
        )

        request = Request(
            MITRE_URL,
            headers={
                "User-Agent": "CyberSecLM/1.0"
            },
        )

        with urlopen(
            request,
            timeout=60,
        ) as response:

            data = response.read()

        MITRE_CACHE_PATH.write_bytes(data)

        print(
            f"Saved ATT&CK metadata to:\n"
            f"{MITRE_CACHE_PATH}"
        )

    else:

        print(
            f"\nUsing cached MITRE ATT&CK "
            f"v{MITRE_VERSION}:\n"
            f"{MITRE_CACHE_PATH}"
        )

    with MITRE_CACHE_PATH.open(
        "r",
        encoding="utf-8",
    ) as f:

        bundle = json.load(f)

    technique_map = {}

    for obj in bundle.get(
        "objects",
        [],
    ):

        if obj.get("type") != "attack-pattern":
            continue

        external_id = None

        for reference in obj.get(
            "external_references",
            [],
        ):

            if reference.get(
                "source_name"
            ) == "mitre-attack":

                external_id = reference.get(
                    "external_id"
                )

                break

        if external_id:

            technique_map[external_id] = {
                "name": obj.get(
                    "name",
                    "",
                ),
                "description": obj.get(
                    "description",
                    "",
                ),
                "deprecated": bool(
                    obj.get(
                        "x_mitre_deprecated",
                        False,
                    )
                ),
                "revoked": bool(
                    obj.get(
                        "revoked",
                        False,
                    )
                ),
            }

    print(
        f"Loaded {len(technique_map)} "
        "official ATT&CK techniques."
    )

    return technique_map


# ============================================================
# HELPERS
# ============================================================

def extract_attack_id(value):

    if value is None:
        return None

    match = re.search(
        r"T\d{4}(?:\.\d{3})?",
        str(value),
    )

    if match:
        return match.group(0).upper()

    return None


def normalize_text(text):

    text = str(text).lower()

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    text = re.sub(
        r"[^a-z0-9]+",
        " ",
        text,
    )

    return text.strip()


def extract_json(text):

    try:

        return json.loads(text)

    except json.JSONDecodeError:

        pass

    match = re.search(
        r"\{.*\}",
        text,
        re.DOTALL,
    )

    if match:

        try:

            return json.loads(
                match.group()
            )

        except json.JSONDecodeError:

            pass

    return None


def parent_technique_id(
    technique_id
):

    if "." in technique_id:

        return technique_id.split(
            "."
        )[0]

    return technique_id


# ============================================================
# CHRONOCTI
# ============================================================

def load_temporal_dataset():

    print(
        "\nLoading temporal dataset..."
    )

    df = pd.read_excel(
        DATASET_PATH,
        sheet_name="Sheet1",
    )

    df = df[
        (df["relation"] == "NEXT")
        & (df["mask"] == "train")
    ]

    edges = []

    for _, row in df.iterrows():

        t1 = extract_attack_id(
            row["T1"]
        )

        t2 = extract_attack_id(
            row["T2"]
        )

        if t1 and t2:

            edges.append(
                (t1, t2)
            )

    print(
        f"Loaded {len(edges)} "
        "training temporal transitions."
    )

    return edges


# ============================================================
# MARKOV MODEL
# ============================================================

def build_markov_model(
    edges
):

    transition_counts = Counter(
        edges
    )

    outgoing_counts = Counter(
        t1
        for t1, _ in edges
    )

    return {
        (t1, t2):
        count / outgoing_counts[t1]
        for (t1, t2), count
        in transition_counts.items()
    }


def get_markov_vocabulary(
    edges
):

    return {
        technique
        for edge in edges
        for technique in edge
    }


def get_next_techniques(
    current_technique,
    probabilities,
    top_k=5,
):

    candidates = [
        (t2, probability)
        for (t1, t2), probability
        in probabilities.items()
        if t1 == current_technique
    ]

    candidates.sort(
        key=lambda x: x[1],
        reverse=True,
    )

    return candidates[:top_k]


# ============================================================
# BASIC VALIDATION
# ============================================================

def validate_attack_id(
    technique_id,
    technique_name,
    mitre_metadata,
):

    result = {
        "id_valid": False,
        "name_corrected": False,
        "official_name": None,
        "errors": [],
    }

    if not technique_id:

        result["errors"].append(
            "Missing ATT&CK technique ID."
        )

        return result

    official = mitre_metadata.get(
        technique_id
    )

    if official is None:

        result["errors"].append(
            "Technique ID does not exist "
            f"in MITRE ATT&CK v{MITRE_VERSION}."
        )

        return result

    result["official_name"] = (
        official["name"]
    )

    if official["revoked"]:

        result["errors"].append(
            "Technique is revoked."
        )

        return result

    if official["deprecated"]:

        result["errors"].append(
            "Technique is deprecated."
        )

        return result

    result["id_valid"] = True

    if normalize_text(
        technique_name
    ) != normalize_text(
        official["name"]
    ):

        result["name_corrected"] = True

    return result


def evidence_is_grounded(
    evidence,
    report,
):

    if not evidence:
        return False

    normalized_evidence = normalize_text(
        evidence
    )

    normalized_report = normalize_text(
        report
    )

    return (
        bool(normalized_evidence)
        and normalized_evidence
        in normalized_report
    )


# ============================================================
# EVIDENCE ATTRIBUTION
# ============================================================

def attribute_evidence(
    report,
    technique_ids,
    tokenizer,
    model,
):

    """
    Recover exact evidence when CyberSecLM returns
    technique IDs without evidence.
    """

    if not technique_ids:
        return []

    ids_text = ", ".join(
        technique_ids
    )

    system_prompt = f"""
You are a cybersecurity evidence attribution model.

For each MITRE ATT&CK technique ID below,
find supporting text that is explicitly present
in the CTI report.

Technique IDs:
{ids_text}

Rules:

1. Copy evidence EXACTLY from the report.
2. Do not paraphrase.
3. Do not invent evidence.
4. The evidence must directly describe the
   behavior represented by the technique.
5. Do not use a sentence merely because it
   contains unrelated cybersecurity activity.
6. If there is no explicit support, use an
   empty evidence string.
7. Return ONLY valid JSON.

Required format:

{{
  "techniques": [
    {{
      "id": "Txxxx",
      "evidence": "Exact text copied from the report"
    }}
  ]
}}
"""

    messages = [
        {
            "role": "system",
            "content": system_prompt,
        },
        {
            "role": "user",
            "content": report,
        },
    ]

    inputs = tokenizer.apply_chat_template(
        messages,
        tokenize=True,
        add_generation_prompt=True,
        return_tensors="pt",
    ).to(model.device)

    with torch.no_grad():

        outputs = model.generate(
            **inputs,
            max_new_tokens=500,
            do_sample=False,
        )

    generated = outputs[
        0
    ][
        inputs[
            "input_ids"
        ].shape[-1]:
    ]

    decoded = tokenizer.decode(
        generated,
        skip_special_tokens=True,
    )

    print(
        "\nRAW EVIDENCE ATTRIBUTION OUTPUT:"
    )

    print(decoded)

    parsed = extract_json(
        decoded
    )

    if not parsed:
        return []

    results = parsed.get(
        "techniques",
        [],
    )

    if not isinstance(
        results,
        list,
    ):
        return []

    return results


# ============================================================
# SEMANTIC EVIDENCE VALIDATION
# ============================================================

def validate_evidence_semantically(
    report,
    candidates,
    mitre_metadata,
    tokenizer,
    model,
):

    """
    Uses the same CyberSecLM model as a strict
    semantic validator.

    No additional model is introduced.
    """

    if not candidates:
        return []

    candidate_text = []

    for index, item in enumerate(
        candidates
    ):

        technique_id = item[
            "id"
        ]

        official_name = mitre_metadata[
            technique_id
        ]["name"]

        evidence = item[
            "evidence"
        ]

        candidate_text.append(
            f"""
Candidate {index + 1}:
ATT&CK ID: {technique_id}
Official name: {official_name}
Evidence: {evidence}
"""
        )

    candidates_block = "\n".join(
        candidate_text
    )

    system_prompt = f"""
You are a strict MITRE ATT&CK evidence validator.

Your ONLY job is to determine whether each proposed
ATT&CK technique is actually supported by its evidence.

CTI REPORT:
{report}

PROPOSED TECHNIQUES:
{candidates_block}

Rules:

1. Judge every candidate independently.
2. The evidence must explicitly support the
   ATT&CK technique.
3. Evidence merely appearing somewhere in the
   report is NOT sufficient.
4. Do not infer a technique from unrelated text.
5. Do not accept a technique just because the
   evidence contains cybersecurity activity.
6. Compare the actual behavior described in the
   evidence with the ATT&CK technique.
7. If the evidence does not support the technique,
   mark it false.
8. Do not change IDs.
9. Do not add new techniques.
10. Return ONLY valid JSON.

Required format:

{{
  "results": [
    {{
      "id": "Txxxx",
      "supported": true,
      "reason": "Short reason"
    }}
  ]
}}
"""

    messages = [
        {
            "role": "system",
            "content": system_prompt,
        },
        {
            "role": "user",
            "content": (
                "Validate the proposed "
                "techniques."
            ),
        },
    ]

    inputs = tokenizer.apply_chat_template(
        messages,
        tokenize=True,
        add_generation_prompt=True,
        return_tensors="pt",
    ).to(model.device)

    with torch.no_grad():

        outputs = model.generate(
            **inputs,
            max_new_tokens=400,
            do_sample=False,
        )

    generated = outputs[
        0
    ][
        inputs[
            "input_ids"
        ].shape[-1]:
    ]

    decoded = tokenizer.decode(
        generated,
        skip_special_tokens=True,
    )

    print(
        "\nRAW SEMANTIC VALIDATION OUTPUT:"
    )

    print(decoded)

    parsed = extract_json(
        decoded
    )

    if not parsed:
        return []

    results = parsed.get(
        "results",
        [],
    )

    if not isinstance(
        results,
        list,
    ):
        return []

    return results


# ============================================================
# EXTRACTION
# ============================================================

def extract_techniques(
    report,
    tokenizer,
    model,
):

    system_prompt = """
You are a cybersecurity threat intelligence
extraction model.

Extract MITRE ATT&CK techniques explicitly
supported by the CTI report.

Rules:

1. Return the exact ATT&CK technique ID.
2. Do not invent ATT&CK IDs.
3. Only return techniques explicitly supported
   by the report.
4. Do not infer unsupported techniques.
5. Do not duplicate technique IDs.
6. If you can confidently identify the technique,
   return its exact ID.
7. Evidence may be omitted from this first
   extraction step because it will be attributed
   separately.

Return ONLY valid JSON.

Required format:

{
  "techniques": [
    "Txxxx"
  ]
}

If no techniques are supported:

{
  "techniques": []
}
"""

    messages = [
        {
            "role": "system",
            "content": system_prompt,
        },
        {
            "role": "user",
            "content": report,
        },
    ]

    inputs = tokenizer.apply_chat_template(
        messages,
        tokenize=True,
        add_generation_prompt=True,
        return_tensors="pt",
    ).to(model.device)

    with torch.no_grad():

        outputs = model.generate(
            **inputs,
            max_new_tokens=500,
            do_sample=False,
        )

    generated = outputs[
        0
    ][
        inputs[
            "input_ids"
        ].shape[-1]:
    ]

    return tokenizer.decode(
        generated,
        skip_special_tokens=True,
    )


# ============================================================
# NORMALIZE MODEL OUTPUT
# ============================================================

def normalize_extractions(
    extracted,
):

    """
    Handles both:

        {"techniques": ["T1105", "T1204.002"]}

    and:

        {"techniques": [
            {
                "id": "T1105",
                "evidence": "..."
            }
        ]}

    and a single technique object.
    """

    if not isinstance(
        extracted,
        dict,
    ):

        return None

    if isinstance(
        extracted.get(
            "techniques"
        ),
        list,
    ):

        raw_items = extracted[
            "techniques"
        ]

    elif (
        "id" in extracted
        and "evidence" in extracted
    ):

        raw_items = [
            extracted
        ]

    else:

        return None

    normalized = []

    seen = {}

    for item in raw_items:

        # ID-only output
        if isinstance(
            item,
            str,
        ):

            technique_id = extract_attack_id(
                item
            )

            if not technique_id:
                continue

            candidate = {
                "id": technique_id,
                "name": "",
                "evidence": "",
            }

        # Full object output
        elif isinstance(
            item,
            dict,
        ):

            technique_id = extract_attack_id(
                item.get(
                    "id",
                    "",
                )
            )

            if not technique_id:
                continue

            candidate = {
                "id": technique_id,
                "name": str(
                    item.get(
                        "name",
                        "",
                    )
                ).strip(),
                "evidence": str(
                    item.get(
                        "evidence",
                        "",
                    )
                ).strip(),
            }

        else:

            continue

        # Deduplicate IDs
        if technique_id not in seen:

            seen[
                technique_id
            ] = candidate

        elif (
            not seen[
                technique_id
            ]["evidence"]
            and candidate["evidence"]
        ):

            seen[
                technique_id
            ] = candidate

    normalized = list(
        seen.values()
    )

    return normalized


# ============================================================
# FULL VALIDATION
# ============================================================

def validate_extractions(
    techniques,
    report,
    mitre_metadata,
    markov_vocabulary,
    tokenizer,
    model,
):

    accepted = []
    rejected = []

    # ========================================================
    # STEP 0
    # Recover evidence if extraction returned IDs only
    # ========================================================

    missing_evidence_ids = [
        item["id"]
        for item in techniques
        if item.get("id")
        and not item.get("evidence")
    ]

    if missing_evidence_ids:

        print(
            "\nSome techniques were returned "
            "without evidence."
        )

        print(
            "Running evidence attribution..."
        )

        evidence_items = attribute_evidence(
            report,
            missing_evidence_ids,
            tokenizer,
            model,
        )

        evidence_by_id = {}

        for item in evidence_items:

            if not isinstance(
                item,
                dict,
            ):
                continue

            technique_id = extract_attack_id(
                item.get(
                    "id",
                    "",
                )
            )

            evidence = str(
                item.get(
                    "evidence",
                    "",
                )
            ).strip()

            if technique_id:

                evidence_by_id[
                    technique_id
                ] = evidence

        for item in techniques:

            if not item.get(
                "evidence"
            ):

                item[
                    "evidence"
                ] = evidence_by_id.get(
                    item["id"],
                    "",
                )

    # ========================================================
    # STEP 1
    # Basic ID + grounding validation
    # ========================================================

    candidates = []

    for item in techniques:

        technique_id = extract_attack_id(
            item.get(
                "id",
                "",
            )
        )

        name = item.get(
            "name",
            "",
        )

        evidence = item.get(
            "evidence",
            "",
        )

        validation = validate_attack_id(
            technique_id,
            name,
            mitre_metadata,
        )

        reasons = list(
            validation[
                "errors"
            ]
        )

        if not validation[
            "id_valid"
        ]:

            rejected.append(
                {
                    "id":
                        technique_id or "",
                    "name":
                        name,
                    "evidence":
                        evidence,
                    "official_name":
                        validation[
                            "official_name"
                        ],
                    "reasons":
                        reasons,
                }
            )

            continue

        if not evidence_is_grounded(
            evidence,
            report,
        ):

            rejected.append(
                {
                    "id":
                        technique_id,
                    "name":
                        name,
                    "evidence":
                        evidence,
                    "official_name":
                        validation[
                            "official_name"
                        ],
                    "reasons": [
                        "Evidence is not directly "
                        "present in the CTI report."
                    ],
                }
            )

            continue

        candidates.append(
            {
                "id":
                    technique_id,
                "name":
                    name,
                "evidence":
                    evidence,
                "official_name":
                    validation[
                        "official_name"
                    ],
                "name_corrected":
                    validation[
                        "name_corrected"
                    ],
            }
        )

    # ========================================================
    # STEP 2
    # Semantic evidence validation
    # ========================================================

    semantic_results = (
        validate_evidence_semantically(
            report,
            candidates,
            mitre_metadata,
            tokenizer,
            model,
        )
    )

    semantic_by_id = {}

    for result in semantic_results:

        if not isinstance(
            result,
            dict,
        ):
            continue

        technique_id = extract_attack_id(
            result.get(
                "id",
                "",
            )
        )

        if technique_id:

            semantic_by_id[
                technique_id
            ] = result

    # ========================================================
    # STEP 3
    # Markov eligibility
    # ========================================================

    for candidate in candidates:

        technique_id = candidate[
            "id"
        ]

        semantic = semantic_by_id.get(
            technique_id
        )

        if not semantic:

            rejected.append(
                {
                    "id":
                        technique_id,
                    "name":
                        candidate[
                            "name"
                        ],
                    "evidence":
                        candidate[
                            "evidence"
                        ],
                    "official_name":
                        candidate[
                            "official_name"
                        ],
                    "reasons": [
                        "Semantic evidence "
                        "validation returned "
                        "no decision."
                    ],
                }
            )

            continue

        supported = semantic.get(
            "supported",
            False,
        )

        if supported is not True:

            rejected.append(
                {
                    "id":
                        technique_id,
                    "name":
                        candidate[
                            "name"
                        ],
                    "evidence":
                        candidate[
                            "evidence"
                        ],
                    "official_name":
                        candidate[
                            "official_name"
                        ],
                    "reasons": [
                        "Evidence does not "
                        "semantically support "
                        "this ATT&CK technique.",
                        str(
                            semantic.get(
                                "reason",
                                "",
                            )
                        ),
                    ],
                }
            )

            continue

        # ----------------------------------------------------
        # Determine Markov representation
        # ----------------------------------------------------

        forecast_id = None
        mapping_note = None

        if technique_id in markov_vocabulary:

            forecast_id = technique_id

        elif (
            ALLOW_PARENT_FALLBACK_FOR_FORECAST
        ):

            parent_id = parent_technique_id(
                technique_id
            )

            if parent_id in markov_vocabulary:

                forecast_id = parent_id

                mapping_note = (
                    f"Sub-technique "
                    f"{technique_id} mapped to "
                    f"parent {parent_id} for "
                    "Markov forecasting."
                )

        if forecast_id is None:

            rejected.append(
                {
                    "id":
                        technique_id,
                    "name":
                        candidate[
                            "name"
                        ],
                    "evidence":
                        candidate[
                            "evidence"
                        ],
                    "official_name":
                        candidate[
                            "official_name"
                        ],
                    "reasons": [
                        "Technique is not "
                        "represented in the "
                        "Markov vocabulary "
                        "or through its parent."
                    ],
                }
            )

            continue

        # ----------------------------------------------------
        # ACCEPT
        # ----------------------------------------------------

        accepted.append(
            {
                "original_id":
                    technique_id,

                "forecast_id":
                    forecast_id,

                "name":
                    candidate[
                        "official_name"
                    ],

                "model_name":
                    candidate[
                        "name"
                    ],

                "evidence":
                    candidate[
                        "evidence"
                    ],

                "mapping_note":
                    mapping_note,

                "name_corrected":
                    candidate[
                        "name_corrected"
                    ],
            }
        )

    return accepted, rejected


# ============================================================
# DISPLAY
# ============================================================

def display_validation_results(
    accepted,
    rejected,
):

    print(
        "\n" + "-" * 70
    )

    print(
        "VALIDATION RESULTS"
    )

    print(
        "-" * 70
    )

    print(
        "\nACCEPTED TECHNIQUES"
    )

    if not accepted:

        print("  None")

    for item in accepted:

        print(
            f"• {item['original_id']} "
            f"→ {item['name']}"
        )

        print(
            f"  Evidence: "
            f"{item['evidence']}"
        )

        if item[
            "name_corrected"
        ]:

            print(
                f"  Canonicalized name: "
                f"{item['name']}"
            )

        if item[
            "mapping_note"
        ]:

            print(
                f"  Note: "
                f"{item['mapping_note']}"
            )

    print(
        "\nREJECTED TECHNIQUES"
    )

    if not rejected:

        print("  None")

    for item in rejected:

        print(
            f"• {item['id']} "
            f"→ {item['name']}"
        )

        if item[
            "official_name"
        ]:

            print(
                f"  Official name: "
                f"{item['official_name']}"
            )

        print(
            f"  Evidence: "
            f"{item['evidence']}"
        )

        for reason in item[
            "reasons"
        ]:

            if reason:

                print(
                    f"  Reason: {reason}"
                )


def display_forecasts(
    accepted,
    probabilities,
):

    print(
        "\n" + "-" * 70
    )

    print(
        "PROBABILISTIC NEXT-TECHNIQUE ESTIMATES"
    )

    print(
        "-" * 70
    )

    if not accepted:

        print(
            "\nNo validated techniques "
            "reached the forecasting stage."
        )

        return

    for item in accepted:

        current = item[
            "forecast_id"
        ]

        predictions = get_next_techniques(
            current,
            probabilities,
            TOP_K,
        )

        print(
            f"\nExtracted technique:\n"
            f"  {item['original_id']} "
            f"→ {item['name']}"
        )

        if current != item[
            "original_id"
        ]:

            print(
                f"  Forecasting representation: "
                f"{current}"
            )

        if not predictions:

            print(
                "  No learned transitions."
            )

            continue

        print(
            "\n  Possible next techniques:"
        )

        for rank, (
            technique,
            probability,
        ) in enumerate(
            predictions,
            start=1,
        ):

            print(
                f"    {rank}. "
                f"{technique} "
                f"({probability:.2%})"
            )

        print(
            "  Note: probabilities are learned "
            "transition frequencies from the "
            "ChronoCTI training relations; they "
            "are not deterministic predictions "
            "of attacker behavior."
        )


# ============================================================
# RUN SINGLE REPORT
# ============================================================

def run_single_report(
    report,
    tokenizer,
    model,
    probabilities,
    mitre_metadata,
    markov_vocabulary,
    report_number=None,
):

    print(
        "\n\n" + "=" * 70
    )

    print(
        f"CTI REPORT TEST "
        f"{report_number}"
    )

    print(
        "=" * 70
    )

    print(
        "\nCTI REPORT:"
    )

    print(
        report.strip()
    )

    print(
        "\n" + "-" * 70
    )

    print(
        "EXTRACTING ATT&CK TECHNIQUES..."
    )

    print(
        "-" * 70
    )

    raw_output = extract_techniques(
        report,
        tokenizer,
        model,
    )

    print(
        "\nRAW CYBERSECLM OUTPUT:"
    )

    print(
        raw_output
    )

    extracted = extract_json(
        raw_output
    )

    if extracted is None:

        print(
            "\nERROR: CyberSecLM output "
            "could not be parsed as JSON."
        )

        return {
            "status": "json_error",
            "accepted": [],
            "rejected": [],
        }

    techniques = normalize_extractions(
        extracted
    )

    if techniques is None:

        print(
            "\nERROR: Invalid extraction schema."
        )

        return {
            "status": "schema_error",
            "accepted": [],
            "rejected": [],
        }

    if not techniques:

        print(
            "\nNo technique candidates "
            "were returned."
        )

        return {
            "status": "ok",
            "accepted": [],
            "rejected": [],
        }

    accepted, rejected = (
        validate_extractions(
            techniques,
            report,
            mitre_metadata,
            markov_vocabulary,
            tokenizer,
            model,
        )
    )

    display_validation_results(
        accepted,
        rejected,
    )

    display_forecasts(
        accepted,
        probabilities,
    )

    return {
        "status": "ok",
        "accepted": accepted,
        "rejected": rejected,
    }


# ============================================================
# TEST REPORTS
# ============================================================

TEST_REPORTS = [

    """
The threat actor sent a phishing email containing a malicious
Microsoft Word document. The victim opened the attachment and
enabled macros. The malware then downloaded an additional payload
from a remote server and executed commands using PowerShell.
""",

    """
The attacker used PowerShell to execute a script on the compromised
Windows host. The script downloaded a second-stage payload from a
remote server and then queried the operating system version.
""",

    """
The threat actor established persistence by creating a scheduled
task that launched a malicious executable every time the victim
logged in. The executable then contacted a remote command and
control server.
""",
]


# ============================================================
# SUMMARY
# ============================================================

def print_test_summary(
    results
):

    print(
        "\n\n" + "=" * 70
    )

    print(
        "PIPELINE TEST SUMMARY"
    )

    print(
        "=" * 70
    )

    total_accepted = 0
    total_rejected = 0
    errors = 0

    for index, result in enumerate(
        results,
        start=1,
    ):

        accepted_count = len(
            result["accepted"]
        )

        rejected_count = len(
            result["rejected"]
        )

        total_accepted += (
            accepted_count
        )

        total_rejected += (
            rejected_count
        )

        if result[
            "status"
        ] != "ok":

            errors += 1

        print(
            f"\nReport {index}:"
            f"\n  Status: "
            f"{result['status']}"
            f"\n  Accepted: "
            f"{accepted_count}"
            f"\n  Rejected: "
            f"{rejected_count}"
        )

    print(
        f"\nOverall:"
        f"\n  Accepted: "
        f"{total_accepted}"
        f"\n  Rejected: "
        f"{total_rejected}"
        f"\n  Errors: "
        f"{errors}"
    )

    print(
        "\nThis is a pipeline smoke test, "
        "not a formal model accuracy evaluation."
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print(
        "\n" + "=" * 70
    )

    print(
        "CYBERSECLM VALIDATED "
        "TEMPORAL FORECASTING PIPELINE"
    )

    print(
        "=" * 70
    )

    tokenizer, model = (
        load_cybersec_model()
    )

    mitre_metadata = (
        load_mitre_metadata()
    )

    edges = (
        load_temporal_dataset()
    )

    probabilities = (
        build_markov_model(
            edges
        )
    )

    markov_vocabulary = (
        get_markov_vocabulary(
            edges
        )
    )

    print(
        f"\nMarkov transitions: "
        f"{len(probabilities)} "
        "unique transitions."
    )

    print(
        f"Markov vocabulary: "
        f"{len(markov_vocabulary)} "
        "ATT&CK techniques."
    )

    results = []

    for index, report in enumerate(
        TEST_REPORTS,
        start=1,
    ):

        results.append(
            run_single_report(
                report,
                tokenizer,
                model,
                probabilities,
                mitre_metadata,
                markov_vocabulary,
                index,
            )
        )

    print_test_summary(
        results
    )
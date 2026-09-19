import json
from inference import generate_response


with open("data/cti_baseline.json", "r") as file:
    data = json.load(file)


for i in data:
    prompt = f"""
You are a cybersecurity information extraction system.

Extract only information explicitly stated in the CTI text.

For techniques, use MITRE ATT&CK technique IDs when they can be identified
from the text. Do not invent a technique ID.

For every extracted item, use only information explicitly supported by the
CTI text. If a field is not present or cannot be determined, use an empty
string or empty list.

Return ONLY valid JSON using this exact schema:

{{
    "entities": [
        {{
            "type": "threat_actor | malware | campaign | product",
            "name": "..."
        }}
    ],
    "techniques": [
        {{
            "id": "...",
            "name": "...",
            "evidence": "..."
        }}
    ],
    "vulnerabilities": [
        {{
            "cve_id": "...",
            "product": "...",
            "version": "...",
            "type": "...",
            "evidence": "..."
        }}
    ],
    "iocs": [
        {{
            "type": "ip | domain | hash | url",
            "value": "..."
        }}
    ],
    "evidence": [
        {{
            "claim": "...",
            "text": "..."
        }}
    ]
}}

CTI text:
{i["text"]}
"""

    gen = generate_response(prompt)

    print(f"CTI: {i['text']}")
    print(f"Answer: {gen}\n")
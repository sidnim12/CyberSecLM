import torch

from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
)

from peft import PeftModel


# -------------------------
# Configuration
# -------------------------

MODEL_NAME = "Qwen/Qwen3-4B-Instruct-2507"

ADAPTER_PATH = "experiments/cyberseclm-qlora"


# -------------------------
# 4-bit configuration
# -------------------------

quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_use_double_quant=True,
)


# -------------------------
# Load tokenizer
# -------------------------

tokenizer = AutoTokenizer.from_pretrained(
    MODEL_NAME
)


# -------------------------
# Load base model
# -------------------------

model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    quantization_config=quantization_config,
    device_map="auto",
)


# -------------------------
# Load LoRA adapter
# -------------------------

model = PeftModel.from_pretrained(
    model,
    ADAPTER_PATH,
)


# -------------------------
# Test prompt
# -------------------------

messages = [
    {
        "role": "system",
        "content": (
            "You are a cybersecurity information extraction system. "
            "Extract only information explicitly supported by the CTI text. "
            "Do not invent information or ATT&CK technique IDs."
        ),
    },
    {
        "role": "user",
        "content": (
            "The group used PowerShell to download and execute "
            "a malicious payload from hxxp://malicious-example.com/update.ps1. "
            "The activity was associated with the deployment of Cobalt Strike."
        ),
    },
]


# -------------------------
# Tokenize
# -------------------------

inputs = tokenizer.apply_chat_template(
    messages,
    tokenize=True,
    add_generation_prompt=True,
    return_tensors="pt",
).to(model.device)


# -------------------------
# Generate
# -------------------------

with torch.no_grad():

    output = model.generate(
        **inputs,
        max_new_tokens=300,
    )


generated_ids = output[0][
    inputs["input_ids"].shape[-1]:
]


response = tokenizer.decode(
    generated_ids,
    skip_special_tokens=True,
)


# -------------------------
# Output
# -------------------------

print("\n===== ADAPTER TEST =====")
print(response)

print("\nAdapter loaded successfully!")
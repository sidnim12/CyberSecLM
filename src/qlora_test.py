import torch
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
)


# -------------------------
# Model
# -------------------------

MODEL_NAME = "Qwen/Qwen3-4B-Instruct-2507"


# -------------------------
# 4-bit QLoRA configuration
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

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)


# -------------------------
# Load 4-bit model
# -------------------------

model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    quantization_config=quantization_config,
    device_map="auto",
)


# -------------------------
# GPU information
# -------------------------

print("\n===== QLoRA MODEL TEST =====")

print("Model loaded successfully!")

print(
    "GPU:",
    torch.cuda.get_device_name(0)
)

print(
    "Allocated VRAM:",
    round(torch.cuda.memory_allocated() / 1024**3, 2),
    "GB"
)

print(
    "Reserved VRAM:",
    round(torch.cuda.memory_reserved() / 1024**3, 2),
    "GB"
)


# -------------------------
# Simple inference test
# -------------------------

messages = [
    {
        "role": "system",
        "content": "You are a cybersecurity assistant."
    },
    {
        "role": "user",
        "content": "What is CVE-2021-44228?"
    }
]


inputs = tokenizer.apply_chat_template(
    messages,
    tokenize=True,
    add_generation_prompt=True,
    return_tensors="pt"
).to(model.device)


with torch.no_grad():

    output = model.generate(
        **inputs,
        max_new_tokens=100
    )


generated_ids = output[0][
    inputs["input_ids"].shape[-1]:
]

response = tokenizer.decode(
    generated_ids,
    skip_special_tokens=True
)


print("\n===== RESPONSE =====")
print(response)


# -------------------------
# Final VRAM usage
# -------------------------

print("\n===== FINAL VRAM =====")

print(
    "Allocated VRAM:",
    round(torch.cuda.memory_allocated() / 1024**3, 2),
    "GB"
)

print(
    "Reserved VRAM:",
    round(torch.cuda.memory_reserved() / 1024**3, 2),
    "GB"
)
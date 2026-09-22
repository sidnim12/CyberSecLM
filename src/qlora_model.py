import torch

from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
)

from peft import (
    LoraConfig,
    prepare_model_for_kbit_training,
    get_peft_model,
)


# -------------------------
# Model
# -------------------------

MODEL_NAME = "Qwen/Qwen3-4B-Instruct-2507"


# -------------------------
# 4-bit quantization
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
# Load quantized model
# -------------------------

model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    quantization_config=quantization_config,
    device_map="auto",
)


# -------------------------
# Prepare model for k-bit training
# -------------------------

model = prepare_model_for_kbit_training(model)


# -------------------------
# LoRA configuration
# -------------------------

lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
    target_modules=[
        "q_proj",
        "k_proj",
        "v_proj",
        "o_proj",
    ],
)


# -------------------------
# Attach LoRA adapters
# -------------------------

model = get_peft_model(
    model,
    lora_config
)


# -------------------------
# Print trainable parameters
# -------------------------

model.print_trainable_parameters()


# -------------------------
# GPU information
# -------------------------

print("\n===== QLoRA MODEL =====")

print(
    "GPU:",
    torch.cuda.get_device_name(0)
)

print(
    "Allocated VRAM:",
    round(
        torch.cuda.memory_allocated() / 1024**3,
        2
    ),
    "GB"
)
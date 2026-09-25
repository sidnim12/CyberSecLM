import torch

from datasets import load_dataset

from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
    TrainingArguments,
)

from peft import (
    LoraConfig,
    prepare_model_for_kbit_training,
)

from trl import SFTTrainer


# -------------------------
# Configuration
# -------------------------

MODEL_NAME = "Qwen/Qwen3-4B-Instruct-2507"

TRAIN_DATASET_PATH = "data/tram/prepared/train.json"
VALIDATION_DATASET_PATH = "data/tram/prepared/validation.json"

OUTPUT_DIR = "experiments/cyberseclm-tram-qlora"


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
# Load model
# -------------------------

model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    quantization_config=quantization_config,
    device_map="auto",
)


# -------------------------
# Prepare model
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
# Load datasets
# -------------------------

dataset = load_dataset(
    "json",
    data_files={
        "train": TRAIN_DATASET_PATH,
        "validation": VALIDATION_DATASET_PATH,
    },
)

train_dataset = dataset["train"]
validation_dataset = dataset["validation"]

print("\n===== DATASET =====")
print("Training examples:", len(train_dataset))
print("Validation examples:", len(validation_dataset))


# -------------------------
# Training arguments
# -------------------------

training_args = TrainingArguments(
    output_dir=OUTPUT_DIR,

    num_train_epochs=3,

    per_device_train_batch_size=1,

    gradient_accumulation_steps=4,

    learning_rate=2e-4,

    logging_steps=25,

    save_strategy="epoch",

    eval_strategy="epoch",

    bf16=True,

    optim="paged_adamw_8bit",

    report_to="none",

    gradient_checkpointing=True,

    remove_unused_columns=False,
)

# -------------------------
# Trainer
# -------------------------

trainer = SFTTrainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=validation_dataset,
    processing_class=tokenizer,
    peft_config=lora_config,
)

# -------------------------
# Start training
# -------------------------

print("\n===== STARTING TRAINING =====")

trainer.train()


# -------------------------
# Save adapter
# -------------------------

print("\n===== SAVING MODEL =====")

trainer.save_model(OUTPUT_DIR)

tokenizer.save_pretrained(OUTPUT_DIR)

print("Training complete!")
print(f"Adapter saved to: {OUTPUT_DIR}")
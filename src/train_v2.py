"""Train a fresh v2 QLoRA adapter. Use --smoke for a two-step GPU check."""
import argparse
import hashlib
import importlib.metadata
import json

from inspect_training import ROOT, DATA, MAX_LENGTH, inspect, load_tokenizer


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    import torch
    from datasets import Dataset
    from transformers import AutoModelForCausalLM, BitsAndBytesConfig, set_seed
    from peft import LoraConfig, prepare_model_for_kbit_training
    from trl import SFTConfig, SFTTrainer

    output = ROOT / "experiments" / ("cyberseclm-v2-smoke" if args.smoke else "cyberseclm-tram-qlora-v2")
    if output.exists() and any(output.iterdir()):
        raise ValueError(f"Output already contains files: {output}. Choose a new run directory in this script.")
    if not torch.cuda.is_available() or not torch.cuda.is_bf16_supported():
        raise RuntimeError("This configuration requires a CUDA GPU with bfloat16 support.")
    set_seed(42)
    tokenizer = load_tokenizer()
    inspection = inspect(tokenizer)
    datasets = {s: Dataset.from_list(json.loads((DATA / f"{s}.json").read_text(encoding="utf-8")))
                for s in ("train", "validation")}
    if args.smoke:
        datasets = {s: d.select(range(min(8, len(d)))) for s, d in datasets.items()}
    model_id = "Qwen/Qwen3-4B-Instruct-2507"
    model = AutoModelForCausalLM.from_pretrained(model_id, local_files_only=True,
        device_map={"": 0}, quantization_config=BitsAndBytesConfig(load_in_4bit=True,
            bnb_4bit_quant_type="nf4", bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_use_double_quant=True))
    model = prepare_model_for_kbit_training(model)
    model.config.use_cache = False
    config = SFTConfig(output_dir=str(output), num_train_epochs=3,
        max_steps=2 if args.smoke else -1, per_device_train_batch_size=1,
        per_device_eval_batch_size=1, gradient_accumulation_steps=4,
        learning_rate=2e-4, logging_steps=1 if args.smoke else 25,
        save_strategy="steps" if args.smoke else "epoch",
        eval_strategy="steps" if args.smoke else "epoch", save_steps=2, eval_steps=2,
        load_best_model_at_end=True, metric_for_best_model="eval_loss", greater_is_better=False,
        save_total_limit=2, bf16=True, optim="paged_adamw_8bit", report_to="none",
        gradient_checkpointing=True, max_length=MAX_LENGTH, packing=False,
        assistant_only_loss=True, seed=42, data_seed=42)
    trainer = SFTTrainer(model=model, args=config, train_dataset=datasets["train"],
        eval_dataset=datasets["validation"], processing_class=tokenizer,
        peft_config=LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05, bias="none",
            task_type="CAUSAL_LM", target_modules=["q_proj", "k_proj", "v_proj", "o_proj"]))
    # Verify the actual collated batch, not only the tokenizer's proposed mask.
    batch = trainer.data_collator([trainer.train_dataset[0]])
    messages = datasets["train"][0]["messages"]
    prompt = tokenizer.apply_chat_template(messages[:2], tokenize=True,
        add_generation_prompt=True, return_dict=True)["input_ids"]
    labels = batch["labels"][0].tolist()
    selected = [t for t in labels if t != -100]
    if any(t != -100 for t in labels[:len(prompt)]) or tokenizer.decode(selected).rstrip("\n") != messages[2]["content"] + tokenizer.eos_token:
        raise ValueError("Actual trainer batch did not preserve assistant-only supervision")
    output.mkdir(parents=True, exist_ok=True)
    metadata = {"model": model_id, "smoke": args.smoke, "training_config": config.to_dict(),
        "versions": {p: importlib.metadata.version(p) for p in ("torch", "transformers", "trl", "peft", "datasets", "bitsandbytes")},
        "data_sha256": {s: hashlib.sha256((DATA / f"{s}.json").read_bytes()).hexdigest() for s in datasets},
        "inspection": inspection["splits"], "model_revision": getattr(model.config, "_commit_hash", None)}
    (output / "run_config.json").write_text(json.dumps(metadata, indent=2, default=str), encoding="utf-8")
    trainer.train()
    trainer.save_model(str(output))
    tokenizer.save_pretrained(output)
    trainer.save_state()
    print(f"Finished. Best validation-loss checkpoint: {trainer.state.best_model_checkpoint}")
    print(f"Adapter: {output}")
    print("Validation loss selects the checkpoint; extraction F1 still needs separate evaluation.")


if __name__ == "__main__":
    main()

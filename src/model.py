from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

MODEL_NAME= "Qwen/Qwen3-4B-Instruct-2507"

def load_model(model_id: str):
    tokenizer= AutoTokenizer.from_pretrained(MODEL_NAME)
    model= AutoModelForCausalLM.from_pretrained(MODEL_NAME, device_map="auto")

    return tokenizer, model

if __name__== "__main__":
    tokenizer, model= load_model(MODEL_NAME)
    print("model loaded successfully!")



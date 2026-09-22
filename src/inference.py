from model import load_model, MODEL_NAME

tokenizer, model = load_model(MODEL_NAME)


def generate_response(prompt: str):
    mes= [
    {"role": "system", "content": "You are a helpful and concise AI assistant."},
    {"role": "user", "content": prompt}
    ]

    input_ids = tokenizer.apply_chat_template(
        mes,
        tokenize=True,
        add_generation_prompt=True,
        return_tensors="pt"
    ).to(model.device)

    output = model.generate(
        **input_ids,
        max_new_tokens=500
    )

    generate_ids = output[0][input_ids["input_ids"].shape[-1]:]

    decoded_output = tokenizer.decode(
        generate_ids,
        skip_special_tokens=True
    )

    return decoded_output


if __name__ == "__main__":
    q= "what is a CVE?"
    answer = generate_response(q)
    print(answer)


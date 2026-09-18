from model import load_model, MODEL_NAME

tokenizer, model = load_model(MODEL_NAME)


def generate_response(prompt: str):
    inputs = tokenizer(
        prompt,
        return_tensors="pt"
    ).to(model.device)

    output = model.generate(
        **inputs,
        max_new_tokens=200
    )

    decoded_output = tokenizer.decode(
        output[0],
        skip_special_tokens=True
    )

    return decoded_output


if __name__ == "__main__":
    question = "Explain BFS in simple terms"
    answer = generate_response(question)
    print(answer)


# CyberSecLM

CyberSecLM currently provides a local setup for loading a pretrained language model and running basic text generation. The implementation uses **Qwen/Qwen3-4B-Instruct-2507** through Hugging Face Transformers.

The work completed so far covers the Python environment, GPU verification, model loading code, and a basic inference script. Cybersecurity datasets, fine-tuning, and evaluation have not been implemented.

## Project structure

```text
CyberSecLM/
├── data/               # Empty; no datasets added yet
├── experiments/        # Empty; no experiments added yet
├── src/
│   ├── model.py        # Loads the tokenizer and pretrained model
│   ├── inference.py    # Generates text from a prompt
│   ├── test_gpu.py     # Reports PyTorch version and CUDA availability
│   └── utils.py        # Empty utility placeholder
├── requirements.txt    # Python dependencies
└── README.md
```

## Environment setup

Run the following commands in PowerShell from the project root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

The dependencies are `torch`, `transformers`, `accelerate`, and `huggingface_hub`.

For the CUDA 12.8 build used in the current environment, replace CPU-only PyTorch if necessary:

```powershell
.\.venv\Scripts\python.exe -m pip uninstall -y torch
.\.venv\Scripts\python.exe -m pip install torch --index-url https://download.pytorch.org/whl/cu128
```

These commands use the environment's Python directly, so activation is optional. To activate it in PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
```

The execution policy change applies only to the current terminal session. In VS Code, select `.venv\Scripts\python.exe` as the Python interpreter.

## GPU verification

```powershell
.\.venv\Scripts\python.exe src/test_gpu.py
```

The current local setup was verified with Python 3.13.14 and produced:

```text
torch version: 2.11.0+cu128
CUDA available: True
GPU: NVIDIA GeForce RTX 5070 Ti Laptop GPU
VRAM: 11.94 GB
```

Installed package versions at verification were:

| Package | Version |
| --- | --- |
| torch | 2.11.0+cu128 |
| transformers | 5.17.0 |
| accelerate | 1.15.0 |
| huggingface_hub | 1.32.0 |

`requirements.txt` does not pin these versions.

## Model loading

`src/model.py` loads the tokenizer and causal language model with `from_pretrained`. The model uses `device_map="auto"` for device placement.

```powershell
.\.venv\Scripts\python.exe src/model.py
```

The first load requires internet access to download the model files. Later loads can reuse the local Hugging Face cache. The current loader uses the `MODEL_NAME` constant internally; its `model_id` argument does not yet change the selected model.

## Basic inference

```powershell
.\.venv\Scripts\python.exe src/inference.py
```

The script loads the model, tokenizes a prompt, and generates up to 200 new tokens. Its current example prompt is:

```text
Explain BFS in simple terms
```

To try another prompt, edit the `question` value in `src/inference.py`.

The current implementation passes plain text directly to the tokenizer without applying a chat template. It decodes the full generated sequence, so the printed output includes the input prompt as well as the generated text.

GPU availability has been verified. Model loading and inference have not been verified end to end as part of this review.

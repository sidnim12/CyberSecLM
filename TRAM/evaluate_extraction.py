import json
import re
from collections import Counter

import pandas as pd
import torch

from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig
)

from peft import PeftModel


BASE_MODEL = "Qwen/Qwen3-4B-Instruct-2507"

ADAPTER_PATH = (
    r"C:\Siddu\LLMs\CyberSecLM"
    r"\experiments\cyberseclm-tram-qlora"
)

# We'll fill this with the actual TRAM dataset path
DATASET_PATH = r""

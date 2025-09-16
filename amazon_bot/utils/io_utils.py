import os, json
from typing import Any
from amazon_bot.config import DATA_DIR, STATE_DIR

def ensure_dirs():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(STATE_DIR, exist_ok=True)

def write_json(path: str, data: Any):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)

def read_json(path: str, default: Any):
    if not os.path.exists(path):
        write_json(path, default)
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
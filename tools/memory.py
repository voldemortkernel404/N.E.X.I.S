"""
NEXIS - Persistent Memory
"""

import json
from pathlib import Path


MEMORY_FILE = Path(__file__).resolve().parent.parent / "data" / "memory.json"

MAX_MESSAGES = 20


def _load_memory():
    if not MEMORY_FILE.exists():
        return []

    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        return data if isinstance(data, list) else []

    except (json.JSONDecodeError, OSError):
        return []


def _save_memory(memory):
    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(MEMORY_FILE, "w", encoding="utf-8") as file:
        json.dump(memory, file, indent=2, ensure_ascii=False)


def add_message(role, content):
    memory = _load_memory()

    memory.append({
        "role": role,
        "content": content
    })

    memory = memory[-MAX_MESSAGES:]

    _save_memory(memory)


def get_history():
    return _load_memory()


def clear_memory():
    _save_memory([])
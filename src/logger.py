"""
ORBIT RUSH — Logger
Structured JSONL logging to file + colored terminal output.
Logs are written to the logs/ directory.
"""

import json
import os
import time
from datetime import datetime

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
LOG_FILE = os.path.join(LOG_DIR, "game_log.jsonl")

_start_time = time.time()

# Ensure log directory exists
os.makedirs(LOG_DIR, exist_ok=True)

# Terminal colour codes by category
_COLOR_MAP = {
    "SYSTEM": "\033[36m",
    "GAME": "\033[32m",
    "MENU": "\033[33m",
    "COLLISION": "\033[31m",
    "ORB": "\033[35m",
    "STATS": "\033[34m",
    "INPUT": "\033[37m",
    "UI": "\033[90m",
}
_RESET = "\033[0m"


def _timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


def _elapsed() -> float:
    return round(time.time() - _start_time, 3)


def log(category: str, message: str, data: dict = None):
    """
    Log an event to terminal and JSONL file.

    Args:
        category: Event category (GAME, MENU, COLLISION, ORB, SYSTEM, etc.)
        message:  Human-readable message
        data:     Optional dict of structured data
    """
    entry = {
        "timestamp": _timestamp(),
        "elapsed_s": _elapsed(),
        "category": category,
        "message": message,
    }
    if data:
        entry["data"] = data

    # Terminal output
    clr = _COLOR_MAP.get(category, _RESET)
    prefix = f"{clr}[{entry['timestamp']}] [{category}]{_RESET}"
    detail = f" | {json.dumps(data)}" if data else ""
    print(f"{prefix} {message}{detail}")

    # Append to JSONL file
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"\033[31m[LOG ERROR] Could not write to {LOG_FILE}: {e}\033[0m")


def clear_log():
    """Clear the log file (called on fresh launch)."""
    try:
        if os.path.exists(LOG_FILE):
            os.remove(LOG_FILE)
        log("SYSTEM", "Log file cleared for new session")
    except Exception:
        pass

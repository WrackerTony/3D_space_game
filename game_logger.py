"""
Game Logger Module
Logs events to both terminal and a JSONL (JSON Lines) structured file.
"""

import json
import os
import time
from datetime import datetime

LOG_FILE = "game_log.jsonl"

_start_time = time.time()


def _timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


def _elapsed():
    return round(time.time() - _start_time, 3)


def log(category: str, message: str, data: dict = None):
    """
    Log an event to terminal and JSONL file.

    Args:
        category: Event category (e.g. 'GAME', 'MENU', 'COLLISION', 'ORB', 'SYSTEM')
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

    # Terminal output (colored by category)
    color_map = {
        "SYSTEM": "\033[36m",  # cyan
        "GAME": "\033[32m",  # green
        "MENU": "\033[33m",  # yellow
        "COLLISION": "\033[31m",  # red
        "ORB": "\033[35m",  # magenta
        "STATS": "\033[34m",  # blue
        "INPUT": "\033[37m",  # white
        "UI": "\033[90m",  # gray
    }
    reset = "\033[0m"
    clr = color_map.get(category, "\033[0m")
    prefix = f"{clr}[{entry['timestamp']}] [{category}]{reset}"
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

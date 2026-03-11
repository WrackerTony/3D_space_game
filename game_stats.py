"""
Game Stats Module
Tracks and persists player statistics across sessions.
"""

import json
import os
from datetime import datetime

STATS_FILE = "game_stats.json"

DEFAULT_STATS = {
    "total_games_played": 0,
    "max_score_orbs": 0,
    "max_distance": 0,
    "total_orbs_collected": 0,
    "total_distance_traveled": 0,
    "last_games": [],  # list of dicts, most recent first, max 3
}


def load_stats() -> dict:
    """Load stats from file, returning defaults if missing/corrupt."""
    if not os.path.exists(STATS_FILE):
        return dict(DEFAULT_STATS)
    try:
        with open(STATS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Ensure all keys exist
        for k, v in DEFAULT_STATS.items():
            if k not in data:
                data[k] = v
        return data
    except Exception:
        return dict(DEFAULT_STATS)


def save_stats(stats: dict):
    """Save stats to file."""
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)


def record_game(orbs_collected: int, distance: int):
    """
    Record the result of a finished game.
    Returns the updated stats dict.
    """
    stats = load_stats()
    stats["total_games_played"] += 1
    stats["total_orbs_collected"] += orbs_collected
    stats["total_distance_traveled"] += distance
    if orbs_collected > stats["max_score_orbs"]:
        stats["max_score_orbs"] = orbs_collected
    if distance > stats["max_distance"]:
        stats["max_distance"] = distance

    game_entry = {
        "game_number": stats["total_games_played"],
        "orbs_collected": orbs_collected,
        "distance": distance,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    stats["last_games"].insert(0, game_entry)
    stats["last_games"] = stats["last_games"][:3]  # keep only last 3

    save_stats(stats)
    return stats

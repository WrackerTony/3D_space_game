<div align="center">

![Typing SVG](https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=42&letterSpacing=6px&pause=2000&color=1E90FF&center=true&vCenter=true&width=700&height=90&lines=ORBIT+RUSH)

<br/>

![Python](https://img.shields.io/badge/Python-3.x-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Ursina](https://img.shields.io/badge/Ursina-Engine-6A0DAD?style=for-the-badge&logo=gamepad&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20Windows%20%7C%20macOS-0078D4?style=for-the-badge&logo=linux&logoColor=white)
![Version](https://img.shields.io/badge/Version-v2.0-success?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Active-brightgreen?style=for-the-badge)

<br/>

> **🚀 A fast-paced 3D space survival runner — dodge meteorites, collect orbs, and survive as long as you can!**

</div>

---

## 🎬 Game Preview

<div align="center">

![Game Preview](media/preview.gif)

</div>

---

## 🌌 About the Game

**ORBIT RUSH** is a high-speed 3D arcade survival game built entirely in **Python** using the [**Ursina Engine**](https://www.ursinaengine.org/). You pilot a custom spaceship hurtling through an endless asteroid field. The longer you survive, the faster it gets — and the harder it becomes.

The game features a full **loading screen**, **main menu**, **in-game HUD**, **stats tracking**, **help screen**, **pause menu**, and a **game-over screen** with your final score.

### ✨ Features

- 🎮 **Full controller / gamepad support** — analog stick movement, button navigation, and haptic feedback (vibration)
- 🌌 **Dynamic 3D space background** — multi-layered parallax star field with nebula effects
- 🔫 **Shooting mode** — destroy meteorites with projectiles when you grab a red orb
- ⏸️ **Pause menu** — pause mid-game with access to help & controls
- 📊 **Persistent stats** — your best scores are tracked across sessions
- 🖥️ **Cross-platform** — runs on Linux, Windows, and macOS

---

## 🎮 How to Play

### 🕹️ Keyboard Controls

| Key       | Action                                         |
| --------- | ---------------------------------------------- |
| `W` / `S` | Move ship **Up / Down**                        |
| `A` / `D` | Move ship **Left / Right**                     |
| `Space`   | **Fire** a projectile _(requires Shooter Orb)_ |
| `Esc`     | Pause / Return to menu                         |

### 🎮 Controller Controls

| Input      | Action                     |
| ---------- | -------------------------- |
| Left Stick | Move ship (analog, smooth) |
| RB (R1)    | Shoot                      |
| B (B1)     | Pause Menu                 |
| A          | Select / Confirm           |
| B          | Back / Cancel              |

<br/>

### 🛸 Objective

You are flying forward automatically at ever-increasing speed. Your goal is to:

- ✅ **Avoid meteorites** — a single collision ends the run
- ✅ **Collect energy orbs** — each type has a unique effect
- ✅ **Keep your power bar full** — it drains passively every second
- ✅ **Survive as long as possible** — your score is based on distance + orbs collected

---

## ⚡ Orb Types

Each orb that appears in your path has a different effect when collected:

| Orb                | Color  | Effect                                                |
| ------------------ | ------ | ----------------------------------------------------- |
| 🟢 **Power Orb**   | Green  | Restores **+25%** energy to your power bar            |
| 🟣 **Speed Boost** | Purple | Temporarily **increases** your forward speed          |
| 🔵 **Slow Down**   | Azure  | Temporarily **reduces** your forward speed — breathe! |
| 🔴 **Shooter Orb** | Red    | Enables **shooting mode** for 10 seconds              |
| 🟠 **Drain Orb**   | Orange | **Removes 20%** of your power — avoid these!          |

> 💡 A guaranteed **Shooter Orb** appears every **1000 units** of distance traveled.

---

## 🚀 Difficulty & Progression

The game gets harder the further you travel:

- **Speed** starts at `12` and ramps up to a max of `28` units/sec
- **Meteorite spawn rate** starts at every `1.2 s` and accelerates down to `0.35 s`
- **Power bar** drains continuously at `0.06/sec` — collect green orbs to stay alive

---

## 🏆 Stats & Logging

The game automatically tracks your performance across sessions:

- 📊 **`data/game_stats.json`** — stores your all-time best distance, orbs collected, and total runs
- 📝 **`logs/game_log.jsonl`** — a detailed event log for every game session (spawns, hits, orbs, etc.)

---

## 🛠️ Tech Stack

| Component   | Technology                 |
| ----------- | -------------------------- |
| Language    | **Python 3.x**             |
| Game Engine | **Ursina Engine**          |
| Controller  | **pygame** _(optional)_    |
| 3D Models   | Custom `.obj` assets       |
| Rendering   | **Panda3D** _(via Ursina)_ |
| Platform    | Linux, Windows, macOS      |

---

## Installation & Running

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd 3D_space_game

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the game
python main.py
```

> **Requirements:** Python 3.8+ and `ursina` (see `requirements.txt`)

---

## 📁 Project Structure

```
3D_space_game/
├── main.py                          # Game entry point
├── requirements.txt                 # Python dependencies
├── src/
│   ├── config.py                    # All game constants & settings
│   ├── controller.py                # Gamepad input & haptics
│   ├── entities.py                  # Player, Obstacle, Orb, Projectile
│   ├── logger.py                    # Structured JSONL logging
│   ├── space_background.py          # Dynamic 3D star field
│   ├── stats.py                     # Stats persistence
│   └── ui.py                        # Menu screens, HUD, navigation
├── assets/
│   ├── models/player/               # Player ship (.obj, .png, .mtl)
│   ├── models/meteorite/            # Meteorite (.obj, .png, .mtl)
│   └── textures/                    # Title logo & UI textures
├── media/                           # Screenshots & clips
│   ├── clip.mkv                     # Full gameplay clip
│   └── preview.gif                  # Animated preview for README
├── logs/                            # Runtime logs (git-ignored)
└── data/                            # Runtime stats (git-ignored)
```

---

## 🏅 Can You Beat My Record?

<div align="center">

My current best distance is **1 561** — good luck beating it! 🚀

Let me know if you manage to top that score.

</div>

---

<div align="center">

Made with ❤️ by **Wracker** &nbsp;|&nbsp; **ORBIT RUSH v2.0**

![forthebadge](https://img.shields.io/badge/BUILT%20WITH-Python-blue?style=for-the-badge&logo=python)
![forthebadge](https://img.shields.io/badge/POWERED%20BY-Ursina%20Engine-purple?style=for-the-badge)

</div>

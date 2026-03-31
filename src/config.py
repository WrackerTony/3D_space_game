"""
ORBIT RUSH — Configuration Constants
All tuneable game values live here for easy tweaking.
"""

from ursina import Color, Vec3, color

# ── Window ───────────────────────────────────────────────────────────────────
WINDOW_TITLE = "ORBIT RUSH"
WINDOW_BORDERLESS = False
WINDOW_FULLSCREEN = False
SHOW_FPS = True

# ── Player ───────────────────────────────────────────────────────────────────
PLAYER_MODEL = "assets/models/player/Cool_Space_ship__0623175827_texture.obj"
PLAYER_TEXTURE = "assets/models/player/Cool_Space_ship__0623175827_texture.png"
PLAYER_SCALE = (0.5, 0.2, 1)
PLAYER_SPEED = 3.5
PLAYER_INERTIA = 4
PLAYER_MAX_PITCH = 5
PLAYER_MAX_ROLL = 5
PLAYER_ROTATION_SMOOTHING = 6

# ── Forward movement / difficulty ────────────────────────────────────────────
BASE_FORWARD_SPEED = 12
MAX_FORWARD_SPEED = 28
SPEED_INCREASE_RATE = 0.01

# ── Boundaries ───────────────────────────────────────────────────────────────
BOUNDARY_X = 4
BOUNDARY_Y = 3

# ── Obstacles ────────────────────────────────────────────────────────────────
METEORITE_MODELS = [
    {
        "model": "assets/models/meteorite/meteorit.obj",
        "texture": "assets/models/meteorite/meteorit.png",
    },
]
OBSTACLE_SCALE_MIN = 0.3
OBSTACLE_SCALE_MAX = 1.2
BASE_SPAWN_INTERVAL = 1.2
MIN_SPAWN_INTERVAL = 0.35
SPAWN_RATE_INCREASE = 0.0015

# ── Orbs ─────────────────────────────────────────────────────────────────────
ORB_SPAWN_INTERVAL = 1.8
ORB_SCALE = 0.4
ORB_COLLISION_DIST = 0.6
POWER_ORB_VALUE = 0.25
SPEED_BOOST_AMOUNT = 8
SPEED_BOOST_DURATION = 3
SLOW_AMOUNT = 6
SLOW_DURATION = 3
SHOOTER_DURATION = 10
SHOOTER_GUARANTEE_DIST = 1000
DRAIN_ORB_VALUE = 0.20

# ── Power bar ────────────────────────────────────────────────────────────────
INITIAL_POWER = 1.0
POWER_DEPLETION = 0.06
POWER_BAR_WIDTH = 0.39
POWER_BAR_HEIGHT = 0.025
POWER_BAR_SMOOTH = 5

# ── Projectile ───────────────────────────────────────────────────────────────
PROJECTILE_SPEED = 60
PROJECTILE_RANGE = 100

# ── Camera ───────────────────────────────────────────────────────────────────
CAMERA_OFFSET = Vec3(0, 2, -10)
CAMERA_PITCH = 10

# ── UI Colors ────────────────────────────────────────────────────────────────
COLOR_BG_DARK = Color(8 / 255, 8 / 255, 20 / 255, 240 / 255)
COLOR_ACCENT = Color(30 / 255, 144 / 255, 1.0, 1.0)
COLOR_ACCENT_HOVER = Color(60 / 255, 170 / 255, 1.0, 1.0)
COLOR_ORANGE = Color(1.0, 140 / 255, 0, 1.0)
COLOR_ORANGE_HOVER = Color(1.0, 170 / 255, 50 / 255, 1.0)
COLOR_PURPLE = Color(80 / 255, 60 / 255, 160 / 255, 1.0)
COLOR_PURPLE_HOVER = Color(110 / 255, 80 / 255, 200 / 255, 1.0)
COLOR_TEXT = color.white
COLOR_TEXT_DIM = Color(180 / 255, 180 / 255, 200 / 255, 1.0)

# ── Version / Credits ────────────────────────────────────────────────────────
GAME_VERSION = "v2.0"
CREDITS = "Created by Wracker"

# ── Game States ──────────────────────────────────────────────────────────────
STATE_LOADING = "loading"
STATE_MAIN_MENU = "main_menu"
STATE_PLAYING = "playing"
STATE_PAUSED = "paused"
STATE_GAME_OVER = "gameover"
STATE_HELP = "help"
STATE_STATS = "stats"

# ── Title Logo ───────────────────────────────────────────────────────────────
TITLE_TEXTURE = "assets/textures/title.png"

"""
ORBIT RUSH - Main Game File
A 3D space survival game built with Ursina Engine.
Cross-platform compatible (Linux, Windows, macOS).
"""

from ursina import *
from random import uniform, choice, random
import sys
import math

from game_logger import log, clear_log
from game_stats import load_stats, record_game
from controller import (
    GameController,
    get_controller_mappings,
    BUTTON_SHOOT,
    BUTTON_PAUSE,
    BUTTON_CONFIRM,
    BUTTON_BACK,
)
from space_background import SpaceBackground

# =============================================================================
#  CONFIGURATION  -  Edit these values to tweak the game easily
# =============================================================================

# --- Window ---
WINDOW_TITLE = "ORBIT RUSH"
WINDOW_BORDERLESS = False
WINDOW_FULLSCREEN = False
SHOW_FPS = True

# --- Player ---
PLAYER_MODEL = "Cool_Space_ship__0623175827_texture.obj"
PLAYER_TEXTURE = "Cool_Space_ship__0623175827_texture.png"
PLAYER_SCALE = (0.5, 0.2, 1)
PLAYER_SPEED = 3.5
PLAYER_INERTIA = 4  # smoothing factor for input
PLAYER_MAX_PITCH = 5  # degrees – tilt on vertical input
PLAYER_MAX_ROLL = 5  # degrees – tilt on horizontal input
PLAYER_ROTATION_SMOOTHING = 6

# --- Forward movement / difficulty ---
BASE_FORWARD_SPEED = 12
MAX_FORWARD_SPEED = 28
SPEED_INCREASE_RATE = 0.01  # speed gained per unit distance

# --- Boundaries ---
BOUNDARY_X = 4
BOUNDARY_Y = 3

# --- Obstacles ---
METEORITE_MODELS = [
    {"model": "meteorit_style/meteorit.obj", "texture": "meteorit_style/meteorit.png"},
]
OBSTACLE_SCALE_MIN = 0.3
OBSTACLE_SCALE_MAX = 1.2
BASE_SPAWN_INTERVAL = 1.2  # seconds between spawns at start
MIN_SPAWN_INTERVAL = 0.35
SPAWN_RATE_INCREASE = 0.0015  # how fast spawns get faster per distance

# --- Orbs ---
ORB_SPAWN_INTERVAL = 1.8
ORB_SCALE = 0.4
ORB_COLLISION_DIST = 0.6
POWER_ORB_VALUE = 0.25
SPEED_BOOST_AMOUNT = 8
SPEED_BOOST_DURATION = 3
SLOW_AMOUNT = 6
SLOW_DURATION = 3
SHOOTER_DURATION = 10
SHOOTER_GUARANTEE_DIST = 1000  # guaranteed red orb every N distance
DRAIN_ORB_VALUE = 0.20  # energy removed by drain orb

# --- Power bar ---
INITIAL_POWER = 1.0
POWER_DEPLETION = 0.06  # per second
POWER_BAR_WIDTH = 0.39
POWER_BAR_HEIGHT = 0.025
POWER_BAR_SMOOTH = 5  # lerp speed for smooth bar updates

# --- Projectile ---
PROJECTILE_SPEED = 60
PROJECTILE_RANGE = 100

# --- Camera ---
CAMERA_OFFSET = Vec3(0, 2, -10)
CAMERA_PITCH = 10

# --- UI Colors (menu theme) ---
# NOTE: Ursina Color() uses 0-1 float range, NOT 0-255!
COLOR_BG_DARK = Color(8 / 255, 8 / 255, 20 / 255, 240 / 255)
COLOR_ACCENT = Color(30 / 255, 144 / 255, 1.0, 1.0)  # Dodger blue
COLOR_ACCENT_HOVER = Color(60 / 255, 170 / 255, 1.0, 1.0)
COLOR_ORANGE = Color(1.0, 140 / 255, 0, 1.0)
COLOR_ORANGE_HOVER = Color(1.0, 170 / 255, 50 / 255, 1.0)
COLOR_PURPLE = Color(80 / 255, 60 / 255, 160 / 255, 1.0)
COLOR_PURPLE_HOVER = Color(110 / 255, 80 / 255, 200 / 255, 1.0)
COLOR_TEXT = color.white
COLOR_TEXT_DIM = Color(180 / 255, 180 / 255, 200 / 255, 1.0)

# --- Version / Credits ---
GAME_VERSION = "v2.0"
CREDITS = "Created by Wracker"

# --- Game States ---
STATE_LOADING = "loading"
STATE_MAIN_MENU = "main_menu"
STATE_PLAYING = "playing"
STATE_PAUSED = "paused"
STATE_GAME_OVER = "gameover"
STATE_HELP = "help"
STATE_STATS = "stats"

# =============================================================================
#  LOGO (ASCII-style rendered in the menu)
# =============================================================================

LOGO_TEXT = (
    "______  ____     ____  ____   __    ___  ____\n"
    "|___ / |  _ \\   / ___||  _ \\ / _\\  / __|| ___|\n"
    "  |_ \\ | | | |  \\___ \\| |_) | |_| || |   |  _|\n"
    " ___) || |_| |   ___) ||  __/|  _  || |___| |___\n"
    "|____/ |____/   |____/ |_|   |_| |_| \\____||_____|\n"
    "\n"
    "        R  U  N  N  E  R\n"
)

# =============================================================================
#  APPLICATION SETUP
# =============================================================================

clear_log()
log(
    "SYSTEM",
    "Application starting",
    {
        "os": sys.platform,
        "python": sys.version.split()[0],
    },
)

app = Ursina(
    title=WINDOW_TITLE, borderless=WINDOW_BORDERLESS, fullscreen=WINDOW_FULLSCREEN
)
window.exit_button.visible = False
window.fps_counter.enabled = SHOW_FPS
window.color = color.black

# -- Dynamic 3D space background (replaces old flat quad) --
space_bg = SpaceBackground()
log("SYSTEM", "Dynamic 3D space background created")

log("SYSTEM", "Ursina engine initialized", {"platform": sys.platform})

# -- Controller setup (optional, game works without one) --
gamepad = GameController()
if gamepad.connected:
    log("SYSTEM", "Controller detected", {"name": gamepad.joystick.get_name()})
else:
    log("SYSTEM", "No controller detected — keyboard mode")

# =============================================================================
#  LOADING SCREEN   (shown while preloading assets)
# =============================================================================

loading_panel = Entity(
    parent=camera.ui, model="quad", color=COLOR_BG_DARK, scale=(2, 2), z=10
)

loading_title = Text(
    parent=loading_panel,
    text="ORBIT RUSH",
    y=0.15,
    scale=3.0,
    origin=(0, 0),
    color=COLOR_ACCENT,
)

loading_msg = Text(
    parent=loading_panel,
    text="Loading assets...",
    y=0.03,
    scale=1.3,
    origin=(0, 0),
    color=COLOR_TEXT_DIM,
)

# Spinner dots
_spinner_dots = []
for _i in range(8):
    _angle = _i * (360 / 8)
    _rad = math.radians(_angle)
    _dot = Entity(
        parent=loading_panel,
        model="quad",
        color=Color(30 / 255, 144 / 255, 1.0, (1 - _i / 8)),
        scale=(0.012, 0.012),
        position=(math.sin(_rad) * 0.05, -0.06 + math.cos(_rad) * 0.05),
    )
    _spinner_dots.append(_dot)

_loading_angle = 0


def _update_spinner():
    """Rotate the loading spinner (called each frame during loading)."""
    global _loading_angle
    _loading_angle += time.dt * 300
    for i, dot in enumerate(_spinner_dots):
        angle = _loading_angle + i * (360 / 8)
        rad = math.radians(angle)
        dot.x = math.sin(rad) * 0.05
        dot.y = -0.06 + math.cos(rad) * 0.05
        alpha = int(255 * (1 - i / 8))
        dot.color = Color(30 / 255, 144 / 255, 1.0, alpha / 255)


def _hide_loading():
    """Remove loading screen."""
    global loading_panel
    if loading_panel:
        destroy(loading_panel)
        loading_panel = None
    log("UI", "Loading screen hidden")


# =============================================================================
#  PRELOAD ASSETS (fix first-time lag)
# =============================================================================

log("SYSTEM", "Preloading assets...")

_assets_ready = False


def _do_preload():
    """Preload all models and textures so first game start is instant."""
    global _assets_ready
    try:
        load_model(PLAYER_MODEL)
        log("SYSTEM", "Preloaded player model", {"model": PLAYER_MODEL})

        load_texture(PLAYER_TEXTURE)
        log("SYSTEM", "Preloaded player texture", {"texture": PLAYER_TEXTURE})

        for i, met in enumerate(METEORITE_MODELS):
            load_model(met["model"])
            log("SYSTEM", f"Preloaded meteorite model {i}", {"model": met["model"]})
            if met.get("texture"):
                load_texture(met["texture"])
                log("SYSTEM", f"Preloaded meteorite texture {i}")

        _assets_ready = True
        log("SYSTEM", "All assets preloaded successfully")
    except Exception as e:
        _assets_ready = True
        log("SYSTEM", f"Asset preload warning: {e}")


# =============================================================================
#  GAME ENTITIES
#  NOTE: Entity subclasses intentionally do NOT define update() to avoid
#  Ursina's auto-update calling into destroyed NodePaths (segfault on Linux).
#  Instead we use tick() which is called only from the main game loop.
# =============================================================================


class Player(Entity):
    def __init__(self, **kwargs):
        super().__init__(
            model=PLAYER_MODEL,
            texture=PLAYER_TEXTURE,
            color=color.white,
            scale=PLAYER_SCALE,
            position=(0, 0, 0),
            **kwargs,
        )
        self.speed = PLAYER_SPEED
        self.forward_speed = BASE_FORWARD_SPEED
        self.velocity = Vec3(0, 0, 0)
        self.target_rotation_x = 0
        self.target_rotation_z = 0
        log("GAME", "Player entity created")


class Obstacle(Entity):
    def __init__(self, **kwargs):
        meteorite = choice(METEORITE_MODELS)
        base_scale = uniform(OBSTACLE_SCALE_MIN, OBSTACLE_SCALE_MAX)
        s = (base_scale, base_scale, base_scale)
        self.collision_radius = base_scale * 0.5
        self._dead = False

        tex = meteorite.get("texture")
        super().__init__(
            model=meteorite["model"],
            texture=tex if tex else None,
            color=color.white if tex else color.gray,
            scale=s,
            position=(
                uniform(-BOUNDARY_X, BOUNDARY_X),
                uniform(-BOUNDARY_Y, BOUNDARY_Y),
                player.z + uniform(50, 80),
            ),
            **kwargs,
        )

    def tick(self):
        """Manual per-frame update. Returns True when this entity should be removed."""
        if self._dead:
            return True
        try:
            if self.z < player.z - 5:
                self._dead = True
                destroy(self)
                return True
        except Exception:
            self._dead = True
            return True
        return False


class EnergyOrb(Entity):
    ORB_COLORS = {
        "power": color.lime,
        "speed_up": Color(128 / 255, 0, 1.0, 1.0),
        "slow_down": color.azure,
        "shooter": color.red,
        "drain": Color(1.0, 100 / 255, 0, 1.0),  # dark orange
    }

    def __init__(self, orb_type="power", **kwargs):
        self.orb_type = orb_type
        self._dead = False
        orb_color = self.ORB_COLORS.get(orb_type, color.lime)
        if "position" not in kwargs:
            kwargs["position"] = (
                uniform(-BOUNDARY_X, BOUNDARY_X),
                uniform(-BOUNDARY_Y, BOUNDARY_Y),
                player.z + uniform(50, 80),
            )
        super().__init__(model="sphere", color=orb_color, scale=ORB_SCALE, **kwargs)

    def tick(self):
        """Manual per-frame update. Returns True when this entity should be removed."""
        if self._dead:
            return True
        try:
            if self.z < player.z - 20:
                self._dead = True
                destroy(self)
                return True
        except Exception:
            self._dead = True
            return True
        return False


class Projectile(Entity):
    def __init__(self, **kwargs):
        super().__init__(
            model="cube",
            color=color.orange,
            scale=(0.1, 0.1, 0.6),
            position=player.position + Vec3(0, 0, 1.5),
            rotation=player.rotation,
            **kwargs,
        )
        self.speed = PROJECTILE_SPEED
        self._dead = False
        log("GAME", "Projectile fired", {"pos": str(self.position)})

    def tick(self):
        """Manual per-frame update. Returns True when this entity should be removed."""
        if self._dead:
            return True
        try:
            self.z += self.speed * time.dt
            if self.z > player.z + PROJECTILE_RANGE:
                self._dead = True
                destroy(self)
                return True
            for obstacle in obstacles[:]:
                if obstacle._dead:
                    continue
                if (self.position - obstacle.position).length() < (
                    obstacle.collision_radius + 0.2
                ):
                    shatter_meteorite(obstacle)
                    if obstacle in obstacles:
                        obstacles.remove(obstacle)
                    self._dead = True
                    destroy(self)
                    log("GAME", "Projectile hit meteorite")
                    return True
        except Exception:
            self._dead = True
            return True
        return False


# =============================================================================
#  GAME STATE
# =============================================================================

player = Player()
player.visible = False  # hide until game starts
log("GAME", "Player spawned")

camera.position = CAMERA_OFFSET
camera.rotation = (CAMERA_PITCH, 0, 0)

obstacles = []
energy_orbs = []
projectiles = []

spawn_timer = 0
spawn_interval = BASE_SPAWN_INTERVAL
orb_spawn_timer = 0
orbs_collected = 0
power = INITIAL_POWER
_displayed_power = INITIAL_POWER  # for smooth bar animation

game_running = True
game_state = STATE_LOADING

shooting_mode = False
shooting_timer = 0

last_special_orb_distance = 0

menu_panel = None
help_panel = None
game_over_panel = None
stats_panel = None
pause_panel = None

# -- Menu navigation state (for controller support) --
_menu_buttons = []
_menu_selected = 0
_menu_back_fn = None

# =============================================================================
#  UI ELEMENTS  (HUD shown during gameplay)
# =============================================================================

# -- Top-left info panel background --
hud_panel = Entity(
    parent=camera.ui,
    model="quad",
    color=Color(10 / 255, 10 / 255, 28 / 255, 180 / 255),
    scale=(0.19, 0.08),
    position=(-0.76, 0.435),
    z=2,
)
# Accent stripe on left edge of panel
Entity(
    parent=hud_panel,
    model="quad",
    color=COLOR_ACCENT,
    scale=(0.015, 1),
    origin=(-0.5, 0),
    x=-0.5,
    z=-0.1,
)

score_text = Text(
    text="Orbs: 0",
    position=(-0.84, 0.455),
    scale=1.0,
    color=color.white,
    background=False,
)
distance_text = Text(
    text="Distance: 0",
    position=(-0.84, 0.43),
    scale=1.0,
    color=COLOR_TEXT_DIM,
    background=False,
)

# -- Power bar (centered at top) --
power_bar_bg = Entity(
    parent=camera.ui,
    model="quad",
    color=Color(40 / 255, 40 / 255, 40 / 255, 200 / 255),
    scale=(POWER_BAR_WIDTH + 0.02, POWER_BAR_HEIGHT + 0.01),
    position=(0, 0.46),
    z=1,
)
power_bar = Entity(
    parent=camera.ui,
    model="quad",
    color=color.green,
    scale=(POWER_BAR_WIDTH, POWER_BAR_HEIGHT),
    position=(0, 0.46),
    z=0,
)

# -- Shooting indicator (top-right) --
shooting_indicator = Text(
    text="", position=(0.60, 0.455), scale=1.0, color=color.red, background=False
)


def hide_hud():
    hud_panel.visible = False
    score_text.visible = False
    distance_text.visible = False
    power_bar_bg.visible = False
    power_bar.visible = False
    shooting_indicator.visible = False


def show_hud():
    hud_panel.visible = True
    score_text.visible = True
    distance_text.visible = True
    power_bar_bg.visible = True
    power_bar.visible = True
    shooting_indicator.visible = True


hide_hud()


# =============================================================================
#  MENU NAVIGATION  (controller stick + button support for menus)
# =============================================================================


def _clear_menu_navigation():
    """Reset menu button tracking."""
    global _menu_buttons, _menu_selected, _menu_back_fn
    # Restore original colours before clearing
    for btn in _menu_buttons:
        if hasattr(btn, "_base_color"):
            try:
                btn.color = btn._base_color
            except Exception:
                pass
    _menu_buttons = []
    _menu_selected = 0
    _menu_back_fn = None


def _register_menu_buttons(buttons, back_fn=None):
    """Register a list of Button entities for controller navigation."""
    global _menu_buttons, _menu_selected, _menu_back_fn
    _clear_menu_navigation()
    _menu_buttons = list(buttons)
    _menu_selected = 0
    _menu_back_fn = back_fn
    _highlight_selected()


def _highlight_selected():
    """Visually indicate which menu button is currently selected."""
    for i, btn in enumerate(_menu_buttons):
        if not hasattr(btn, "_base_color"):
            btn._base_color = btn.color
        try:
            if i == _menu_selected:
                btn.color = btn.highlight_color
            else:
                btn.color = btn._base_color
        except Exception:
            pass


def _navigate_menu(direction):
    """Move menu selection.  direction: -1 (up) or +1 (down)."""
    global _menu_selected
    if not _menu_buttons:
        return
    _menu_selected = (_menu_selected + direction) % len(_menu_buttons)
    _highlight_selected()


def _confirm_menu():
    """Activate the currently highlighted menu button."""
    if _menu_buttons and 0 <= _menu_selected < len(_menu_buttons):
        btn = _menu_buttons[_menu_selected]
        if btn.on_click:
            btn.on_click()


def _back_menu():
    """Trigger the back/cancel action for the current menu."""
    if _menu_back_fn:
        _menu_back_fn()


def _handle_controller_menu_nav():
    """Process controller input while a menu is active."""
    if not gamepad.connected:
        return
    # In help screen, use stick for scrolling instead of menu navigation
    if game_state == STATE_HELP and _help_content is not None:
        _, stick_y = gamepad.get_stick()
        if abs(stick_y) > 0.3:
            _scroll_help(-stick_y * HELP_SCROLL_STICK_SPEED * time.dt)
    else:
        nav = gamepad.get_menu_nav(time.dt)
        if nav != 0:
            _navigate_menu(nav)
    if gamepad.is_button_just_pressed(BUTTON_CONFIRM):
        _confirm_menu()
    if gamepad.is_button_just_pressed(BUTTON_BACK):
        _back_menu()


# =============================================================================
#  STYLED BUTTON HELPER
# =============================================================================


def make_button(
    parent,
    text,
    y,
    on_click,
    btn_color=None,
    hover_color=None,
    width=0.3,
    height=0.035,
    text_scale=0.55,
):
    """Create a compact, clean menu button. Works on all platforms."""
    if btn_color is None:
        btn_color = COLOR_ACCENT
    if hover_color is None:
        hover_color = COLOR_ACCENT_HOVER

    btn = Button(
        text=text,
        parent=parent,
        y=y,
        z=-1,
        scale=(width, height),
        text_scale=text_scale,
        on_click=on_click,
        color=btn_color,
        highlight_color=hover_color,
        pressed_color=btn_color.tint(-0.15),
    )
    # Force text color to white so it's always readable
    if btn.text_entity:
        btn.text_entity.color = COLOR_TEXT
    return btn


# =============================================================================
#  MENU SCREENS
# =============================================================================


def clear_all_ui():
    """Destroy all menu/overlay panels."""
    global menu_panel, help_panel, game_over_panel, stats_panel, pause_panel
    global _help_content
    for panel in (menu_panel, help_panel, game_over_panel, stats_panel, pause_panel):
        if panel:
            destroy(panel)
    menu_panel = help_panel = game_over_panel = stats_panel = pause_panel = None
    _help_content = None
    _clear_menu_navigation()
    log("UI", "Cleared all UI panels")


# -------- START MENU --------


def show_start_menu():
    global menu_panel, game_state
    clear_all_ui()
    hide_hud()
    player.visible = False
    game_state = STATE_MAIN_MENU
    log("MENU", "Showing start menu")

    menu_panel = Entity(
        parent=camera.ui, model="quad", color=COLOR_BG_DARK, scale=(2, 2), z=5
    )

    # Logo image
    Entity(
        parent=menu_panel,
        model="quad",
        texture="title.png",
        scale=(0.4, 0.30),
        y=0.16,
        z=-1,
        unlit=True,
        color=color.white,
    )

    # Separator line
    Entity(
        parent=menu_panel,
        model="quad",
        color=Color(1, 1, 1, 0.1),
        scale=(0.4, 0.001),
        y=0.12,
    )

    _btns = []
    _btns.append(make_button(menu_panel, "START GAME", y=-0.02, on_click=start_game))
    _btns.append(
        make_button(
            menu_panel,
            "STATS",
            y=-0.07,
            on_click=show_stats_menu,
            btn_color=COLOR_PURPLE,
            hover_color=COLOR_PURPLE_HOVER,
        )
    )
    _btns.append(
        make_button(
            menu_panel,
            "HELP & CONTROLS",
            y=-0.12,
            on_click=show_help,
            btn_color=COLOR_ORANGE,
            hover_color=COLOR_ORANGE_HOVER,
        )
    )
    _register_menu_buttons(_btns)

    # Footer
    Entity(
        parent=menu_panel,
        model="quad",
        color=Color(1, 1, 1, 0.06),
        scale=(0.4, 0.001),
        y=-0.20,
    )
    Text(
        parent=menu_panel,
        text=CREDITS,
        y=-0.24,
        scale=0.7,
        origin=(0, 0),
        color=COLOR_TEXT_DIM,
    )
    Text(
        parent=menu_panel,
        text=f"{GAME_VERSION}",
        y=-0.27,
        scale=0.6,
        origin=(0, 0),
        color=Color(100 / 255, 100 / 255, 120 / 255, 1.0),
    )


# -------- HELP SCREEN --------


# -- Scrollable help screen state --
_help_content = None  # Entity holding all scrollable content
_help_scroll_y = 0.0  # Current scroll offset
HELP_SCROLL_SPEED = 0.05  # Scroll increment per mouse wheel tick
HELP_SCROLL_STICK_SPEED = 0.35  # Scroll speed for controller stick (units/sec)
HELP_SCROLL_MIN = 0.0  # Top (no scroll up past start)
HELP_SCROLL_MAX = 0.65  # Maximum scroll down distance


def show_help(back_fn=None):
    """Show help/controls screen.  *back_fn* overrides the back button target."""
    global help_panel, game_state, _help_content, _help_scroll_y
    clear_all_ui()
    game_state = STATE_HELP
    log("MENU", "Showing help screen")
    if back_fn is None:
        back_fn = back_to_menu
    _help_scroll_y = 0.0

    # Solid opaque full-screen background
    help_panel = Entity(
        parent=camera.ui,
        model="quad",
        color=Color(12 / 255, 12 / 255, 28 / 255, 1.0),
        scale=(2, 2),
        z=5,
    )

    # --- Fixed header (stays on screen) ---
    Text(
        parent=help_panel,
        text="CONTROLS & HELP",
        y=0.44,
        scale=0.9,
        origin=(0, 0),
        color=color.yellow,
        z=-0.5,
    )
    Entity(
        parent=help_panel,
        model="quad",
        color=color.yellow,
        scale=(0.50, 0.002),
        y=0.415,
        z=-0.1,
    )

    # Scroll hint
    Text(
        parent=help_panel,
        text="Scroll: Mouse wheel / Controller stick",
        y=0.395,
        scale=0.35,
        origin=(0, 0),
        color=COLOR_TEXT_DIM,
        z=-0.5,
    )

    # --- Scrollable content container ---
    _help_content = Entity(parent=help_panel, z=-0.2)

    # -- Build content starting just above screen center --
    cy = 0.05  # cursor y position inside _help_content

    Text(
        parent=_help_content,
        text="Survive as long as you can!",
        y=cy,
        scale=0.5,
        origin=(0, 0),
        color=COLOR_TEXT_DIM,
        z=-0.5,
    )
    cy -= 0.035

    Entity(
        parent=_help_content,
        model="quad",
        color=Color(1, 1, 1, 0.15),
        scale=(0.35, 0.001),
        y=cy,
        z=-0.1,
    )
    cy -= 0.03

    # ── Keyboard Controls ──
    Text(
        parent=_help_content,
        text="KEYBOARD CONTROLS",
        y=cy,
        scale=0.6,
        origin=(0, 0),
        color=COLOR_ACCENT,
        z=-0.5,
    )
    cy -= 0.03
    kb_lines = [
        "W / S       :  Up / Down",
        "A / D       :  Left / Right",
        "Space       :  Shoot (when active)",
        "ESC         :  Pause Menu",
    ]
    for line in kb_lines:
        Text(
            parent=_help_content,
            text=line,
            y=cy,
            scale=0.45,
            origin=(0, 0),
            color=COLOR_TEXT,
            z=-0.5,
        )
        cy -= 0.025

    cy -= 0.01
    Entity(
        parent=_help_content,
        model="quad",
        color=Color(1, 1, 1, 0.15),
        scale=(0.35, 0.001),
        y=cy,
        z=-0.1,
    )
    cy -= 0.03

    # ── Controller Controls (auto-generated from mapping) ──
    Text(
        parent=_help_content,
        text="CONTROLLER CONTROLS",
        y=cy,
        scale=0.6,
        origin=(0, 0),
        color=Color(0.2, 0.8, 1.0, 1.0),
        z=-0.5,
    )
    cy -= 0.03
    ctrl_mappings = get_controller_mappings()
    for btn_label, action in ctrl_mappings:
        Text(
            parent=_help_content,
            text=f"{btn_label:<12s}:  {action}",
            y=cy,
            scale=0.45,
            origin=(0, 0),
            color=COLOR_TEXT,
            z=-0.5,
        )
        cy -= 0.025

    cy -= 0.01
    Entity(
        parent=_help_content,
        model="quad",
        color=Color(1, 1, 1, 0.15),
        scale=(0.35, 0.001),
        y=cy,
        z=-0.1,
    )
    cy -= 0.03

    # ── Orb Types ──
    Text(
        parent=_help_content,
        text="ORB TYPES",
        y=cy,
        scale=0.6,
        origin=(0, 0),
        color=COLOR_ORANGE,
        z=-0.5,
    )
    cy -= 0.03
    orb_info = [
        ("Green   - Power    : Restores energy", color.lime),
        ("Orange  - Drain    : Removes energy", Color(1.0, 100 / 255, 0, 1.0)),
        ("Purple  - Speed Up : Faster for 3s", Color(180 / 255, 100 / 255, 1.0, 1.0)),
        ("Blue    - Slow     : Slower for 3s", color.azure),
        ("Red     - Shooter  : Shoot for 10s", color.red),
    ]
    for txt, clr in orb_info:
        Text(
            parent=_help_content,
            text=txt,
            y=cy,
            scale=0.42,
            origin=(0, 0),
            color=clr,
            z=-0.5,
        )
        cy -= 0.025

    cy -= 0.01
    Entity(
        parent=_help_content,
        model="quad",
        color=Color(1, 1, 1, 0.15),
        scale=(0.35, 0.001),
        y=cy,
        z=-0.1,
    )
    cy -= 0.03

    # ── Gameplay Tips ──
    Text(
        parent=_help_content,
        text="GAMEPLAY",
        y=cy,
        scale=0.6,
        origin=(0, 0),
        color=color.lime,
        z=-0.5,
    )
    cy -= 0.03
    Text(
        parent=_help_content,
        text="- Avoid meteorites\n- Collect orbs to stay alive\n- Keep power bar up\n- Space / RB to shoot (red orb)",
        y=cy,
        scale=0.42,
        origin=(0, 0),
        color=COLOR_TEXT,
        z=-0.5,
    )

    # --- Fixed footer with BACK button ---
    # Dark gradient strip at bottom so button is always readable
    Entity(
        parent=help_panel,
        model="quad",
        color=Color(12 / 255, 12 / 255, 28 / 255, 1.0),
        scale=(2, 0.12),
        y=-0.44,
        z=-0.3,
    )
    _btns = []
    _btns.append(make_button(help_panel, "BACK", y=-0.44, on_click=back_fn))
    _register_menu_buttons(_btns, back_fn=back_fn)


def _scroll_help(amount):
    """Scroll the help content by *amount* (positive = scroll down to see more)."""
    global _help_scroll_y
    if _help_content is None:
        return
    _help_scroll_y = clamp(_help_scroll_y + amount, HELP_SCROLL_MIN, HELP_SCROLL_MAX)
    _help_content.y = _help_scroll_y


# -------- STATS SCREEN --------


def show_stats_menu():
    global stats_panel, game_state
    clear_all_ui()
    game_state = STATE_STATS
    log("MENU", "Showing stats screen")

    stats = load_stats()
    log("STATS", "Stats loaded", stats)

    # Solid opaque full-screen background
    stats_panel = Entity(
        parent=camera.ui,
        model="quad",
        color=Color(12 / 255, 12 / 255, 28 / 255, 1.0),
        scale=(2, 2),
        z=5,
    )

    # Accent line
    Entity(
        parent=stats_panel,
        model="quad",
        color=COLOR_ACCENT,
        scale=(0.40, 0.002),
        y=0.18,
        z=-0.1,
    )

    # Title
    Text(
        parent=stats_panel,
        text="YOUR STATS",
        y=0.15,
        scale=0.9,
        origin=(0, 0),
        color=COLOR_ACCENT,
        z=-0.5,
    )

    Entity(
        parent=stats_panel,
        model="quad",
        color=Color(1, 1, 1, 0.15),
        scale=(0.30, 0.001),
        y=0.12,
        z=-0.1,
    )

    # Key stats only
    stat_items = [
        ("Games Played", str(stats["total_games_played"])),
        ("Best Score", str(stats["max_score_orbs"])),
        ("Best Distance", str(stats["max_distance"])),
    ]
    for i, (label, val) in enumerate(stat_items):
        row_y = 0.08 - i * 0.045
        Text(
            parent=stats_panel,
            text=label,
            y=row_y,
            x=-0.04,
            scale=0.5,
            origin=(1, 0),
            color=COLOR_TEXT_DIM,
            z=-0.5,
        )
        Text(
            parent=stats_panel,
            text=val,
            y=row_y,
            x=0.04,
            scale=0.55,
            origin=(-1, 0),
            color=COLOR_TEXT,
            z=-0.5,
        )

    Entity(
        parent=stats_panel,
        model="quad",
        color=Color(1, 1, 1, 0.15),
        scale=(0.30, 0.001),
        y=-0.065,
        z=-0.1,
    )

    # Last game (just one, simple)
    last = stats.get("last_games", [])
    if last:
        g = last[0]
        Text(
            parent=stats_panel,
            text="LAST GAME",
            y=-0.09,
            scale=0.55,
            origin=(0, 0),
            color=COLOR_ORANGE,
            z=-0.5,
        )
        Text(
            parent=stats_panel,
            text=f"Orbs: {g.get('orbs_collected',0)}   Dist: {g.get('distance',0)}",
            y=-0.125,
            scale=0.45,
            origin=(0, 0),
            color=COLOR_TEXT,
            z=-0.5,
        )
    else:
        Text(
            parent=stats_panel,
            text="No games played yet.",
            y=-0.09,
            scale=0.5,
            origin=(0, 0),
            color=COLOR_TEXT_DIM,
            z=-0.5,
        )

    _btns = []
    _btns.append(
        make_button(
            stats_panel,
            "BACK TO MENU",
            y=-0.20,
            on_click=back_to_menu,
        )
    )
    _register_menu_buttons(_btns, back_fn=back_to_menu)


# -------- GAME OVER SCREEN --------


def show_game_over():
    global game_over_panel, game_state
    clear_all_ui()
    game_state = STATE_GAME_OVER
    log(
        "MENU",
        "Showing game over screen",
        {"orbs": orbs_collected, "distance": int(player.z)},
    )

    # Record the game
    stats = record_game(orbs_collected, int(player.z))
    log("STATS", "Game recorded", stats)

    is_best = (
        orbs_collected >= stats["max_score_orbs"]
        or int(player.z) >= stats["max_distance"]
    )

    # Solid opaque full-screen background
    game_over_panel = Entity(
        parent=camera.ui,
        model="quad",
        color=Color(12 / 255, 12 / 255, 28 / 255, 1.0),
        scale=(2, 2),
        z=5,
    )

    # Card background (lighter panel for contrast)
    card_h = 0.42 if is_best else 0.38
    Entity(
        parent=game_over_panel,
        model="quad",
        color=Color(22 / 255, 22 / 255, 50 / 255, 1.0),
        scale=(0.40, card_h),
        y=0.0,
        z=-0.1,
    )
    # Red accent line at top of card
    Entity(
        parent=game_over_panel,
        model="quad",
        color=color.red,
        scale=(0.40, 0.003),
        y=card_h / 2,
        z=-0.2,
    )

    # Title
    Text(
        parent=game_over_panel,
        text="GAME OVER",
        y=card_h / 2 - 0.04,
        scale=1.1,
        origin=(0, 0),
        color=color.red,
        z=-0.5,
    )

    # Separator
    Entity(
        parent=game_over_panel,
        model="quad",
        color=Color(1, 1, 1, 0.12),
        scale=(0.26, 0.001),
        y=card_h / 2 - 0.07,
        z=-0.2,
    )

    # Score info
    info_top = card_h / 2 - 0.10
    Text(
        parent=game_over_panel,
        text=f"Orbs Collected :  {orbs_collected}",
        y=info_top,
        scale=0.6,
        origin=(0, 0),
        color=color.lime,
        z=-0.5,
    )
    Text(
        parent=game_over_panel,
        text=f"Distance :  {int(player.z)}",
        y=info_top - 0.03,
        scale=0.6,
        origin=(0, 0),
        color=color.cyan,
        z=-0.5,
    )

    best_offset = 0.0
    if is_best:
        Text(
            parent=game_over_panel,
            text="NEW PERSONAL BEST!",
            y=info_top - 0.07,
            scale=0.55,
            origin=(0, 0),
            color=color.yellow,
            z=-0.5,
        )
        best_offset = 0.035

    # Separator before buttons
    sep_y = info_top - 0.085 - best_offset
    Entity(
        parent=game_over_panel,
        model="quad",
        color=Color(1, 1, 1, 0.12),
        scale=(0.26, 0.001),
        y=sep_y,
        z=-0.2,
    )

    btn_y = sep_y - 0.035
    _btns = []
    _btns.append(
        make_button(
            game_over_panel,
            "PLAY AGAIN",
            y=btn_y,
            on_click=start_game,
        )
    )
    _btns.append(
        make_button(
            game_over_panel,
            "VIEW STATS",
            y=btn_y - 0.045,
            on_click=show_stats_menu,
            btn_color=COLOR_PURPLE,
            hover_color=COLOR_PURPLE_HOVER,
        )
    )
    _btns.append(
        make_button(
            game_over_panel,
            "MAIN MENU",
            y=btn_y - 0.09,
            on_click=back_to_menu,
            btn_color=COLOR_ORANGE,
            hover_color=COLOR_ORANGE_HOVER,
        )
    )
    _register_menu_buttons(_btns)


# -------- PAUSE MENU --------


def toggle_pause():
    """Toggle between PLAYING and PAUSED states."""
    global game_state
    if game_state == STATE_PLAYING:
        game_state = STATE_PAUSED
        show_pause_menu()
        log("GAME", "Game paused")
    elif game_state == STATE_PAUSED:
        game_state = STATE_PLAYING
        hide_pause_menu()
        show_hud()
        log("GAME", "Game resumed")


def show_pause_menu():
    """Display the pause overlay with menu buttons."""
    global pause_panel
    hide_pause_menu()
    hide_hud()
    _clear_menu_navigation()

    # Semi-transparent overlay so the game world is still visible behind
    pause_panel = Entity(
        parent=camera.ui,
        model="quad",
        color=Color(0, 0, 0, 0.75),
        scale=(2, 2),
        z=5,
    )

    Text(
        parent=pause_panel,
        text="PAUSED",
        y=0.15,
        scale=1.8,
        origin=(0, 0),
        color=COLOR_ACCENT,
        z=-0.5,
    )

    Entity(
        parent=pause_panel,
        model="quad",
        color=Color(1, 1, 1, 0.15),
        scale=(0.3, 0.001),
        y=0.09,
        z=-0.1,
    )

    _btns = []
    _btns.append(
        make_button(
            pause_panel,
            "RESUME GAME",
            y=0.04,
            on_click=_resume_from_pause,
        )
    )
    _btns.append(
        make_button(
            pause_panel,
            "HELP & CONTROLS",
            y=-0.01,
            on_click=_pause_show_help,
            btn_color=COLOR_ORANGE,
            hover_color=COLOR_ORANGE_HOVER,
        )
    )
    _btns.append(
        make_button(
            pause_panel,
            "RETURN TO MAIN MENU",
            y=-0.06,
            on_click=_pause_return_to_menu,
            btn_color=COLOR_PURPLE,
            hover_color=COLOR_PURPLE_HOVER,
        )
    )
    _btns.append(
        make_button(
            pause_panel,
            "QUIT GAME",
            y=-0.11,
            on_click=application.quit,
            btn_color=color.red,
            hover_color=Color(1, 0.3, 0.3, 1),
        )
    )
    _register_menu_buttons(_btns, back_fn=_resume_from_pause)


def hide_pause_menu():
    """Remove the pause menu overlay."""
    global pause_panel
    if pause_panel:
        destroy(pause_panel)
        pause_panel = None


def _resume_from_pause():
    """Resume gameplay from the pause menu."""
    toggle_pause()


def _pause_return_to_menu():
    """Return to main menu from pause — resets game state properly."""
    global game_state
    hide_pause_menu()
    hide_hud()
    player.visible = False
    _cleanup_game_entities()
    game_state = STATE_MAIN_MENU
    show_start_menu()
    log("MENU", "Returned to main menu from pause")


def _pause_show_help():
    """Open help screen from the pause menu, with back → pause."""
    hide_pause_menu()
    show_help(back_fn=_back_to_pause)


def _back_to_pause():
    """Return from help screen to the pause overlay."""
    global game_state
    clear_all_ui()
    game_state = STATE_PAUSED
    show_pause_menu()


# -------- NAVIGATION --------


def back_to_menu():
    log("MENU", "Navigating back to main menu")
    show_start_menu()


def start_game():
    global game_state
    clear_all_ui()
    restart_game()
    player.visible = True
    show_hud()
    game_state = STATE_PLAYING
    log("GAME", "Game started")


# =============================================================================
#  GAME LOGIC HELPERS
# =============================================================================


def choose_orb_type(force_shooter=False):
    if force_shooter:
        return "shooter"
    r = random()
    if r < 0.55:
        return "power"
    elif r < 0.70:
        return "drain"
    elif r < 0.82:
        return "speed_up"
    elif r < 0.94:
        return "slow_down"
    else:
        return "shooter"


def spawn_obstacle():
    obstacle = Obstacle()
    obstacles.append(obstacle)


def spawn_energy_orb():
    global last_special_orb_distance
    force_shooter = False
    if int(player.z // SHOOTER_GUARANTEE_DIST) > int(
        last_special_orb_distance // SHOOTER_GUARANTEE_DIST
    ):
        force_shooter = True
        last_special_orb_distance = player.z
    orb_type = choose_orb_type(force_shooter=force_shooter)
    orb = EnergyOrb(orb_type=orb_type)
    energy_orbs.append(orb)
    log("ORB", f"Spawned {orb_type} orb", {"z": round(orb.z, 1)})


def check_collision(p, obstacle):
    """Safe collision check that handles destroyed entities."""
    if obstacle._dead:
        return False
    try:
        distance = (p.position - obstacle.position).length()
        return distance < (obstacle.collision_radius + 0.3)
    except Exception:
        return False


def check_orb_collision(p, orb):
    """Safe orb collision check."""
    if orb._dead:
        return False
    try:
        return (p.position - orb.position).length() < ORB_COLLISION_DIST
    except Exception:
        return False


def shatter_meteorite(meteorite):
    """Animate meteorite destruction."""
    if meteorite._dead:
        return
    meteorite._dead = True
    try:
        meteorite.animate_scale(Vec3(0, 0, 0), duration=0.4, curve=curve.in_expo)
        meteorite.animate_color(color.clear, duration=0.4)
        invoke(destroy, meteorite, delay=0.45)
    except Exception:
        try:
            destroy(meteorite)
        except Exception:
            pass
    gamepad.rumble_meteor_destroy()  # Haptic feedback: light vibration
    log("GAME", "Meteorite shattered")


# =============================================================================
#  INPUT
# =============================================================================


def input(key):
    global game_running, game_state, shooting_mode, projectiles
    # -- Escape key: pause toggle or back navigation --
    if key == "escape":
        if game_state == STATE_PLAYING:
            toggle_pause()
            return
        elif game_state == STATE_PAUSED:
            toggle_pause()
            return
        elif game_state in (STATE_HELP, STATE_STATS):
            log("INPUT", "Escape key pressed, returning")
            if _menu_back_fn:
                _menu_back_fn()
            else:
                back_to_menu()
            return

    if game_state == STATE_GAME_OVER and key == "r":
        log("INPUT", "Restart key pressed")
        start_game()
    if game_state == STATE_MAIN_MENU and key == "enter":
        log("INPUT", "Enter key pressed on start menu")
        start_game()
    if game_state == STATE_PLAYING and shooting_mode and key == "space":
        proj = Projectile()
        projectiles.append(proj)

    # -- Mouse scroll wheel for help screen --
    if game_state == STATE_HELP:
        if key == "scroll up":
            _scroll_help(-HELP_SCROLL_SPEED)
        elif key == "scroll down":
            _scroll_help(HELP_SCROLL_SPEED)


# =============================================================================
#  RESTART
# =============================================================================


def _cleanup_game_entities():
    """Destroy all game world entities (obstacles, orbs, projectiles)."""
    global obstacles, energy_orbs, projectiles
    for lst in (obstacles, energy_orbs, projectiles):
        for e in lst[:]:
            if not getattr(e, "_dead", True):
                e._dead = True
                try:
                    destroy(e)
                except Exception:
                    pass
        lst.clear()
    log("GAME", "Cleaned up game entities")


def restart_game():
    global game_running, obstacles, energy_orbs, orbs_collected, power
    global spawn_timer, orb_spawn_timer, _displayed_power
    global shooting_mode, shooting_timer, projectiles, last_special_orb_distance

    clear_all_ui()
    _cleanup_game_entities()

    player.x = 0
    player.y = 0
    player.z = 0
    player.velocity = Vec3(0, 0, 0)
    player.rotation = (0, 0, 0)
    player.forward_speed = BASE_FORWARD_SPEED

    orbs_collected = 0
    power = INITIAL_POWER
    _displayed_power = INITIAL_POWER
    spawn_timer = 0
    orb_spawn_timer = 0
    shooting_mode = False
    shooting_timer = 0
    last_special_orb_distance = 0
    game_running = True

    # Spawn a starter red orb
    shooter_orb = EnergyOrb(orb_type="shooter", position=(0, 0, 15))
    energy_orbs.append(shooter_orb)
    log("GAME", "Game reset complete")


# =============================================================================
#  MAIN UPDATE LOOP
# =============================================================================


def update():
    global spawn_timer, game_running, obstacles, orb_spawn_timer, energy_orbs
    global orbs_collected, power, spawn_interval, game_state, _displayed_power
    global shooting_mode, shooting_timer, projectiles

    # -- Always poll controller --
    gamepad.poll(time.dt)

    # -- Loading screen animation --
    if game_state == STATE_LOADING:
        _update_spinner()
        gamepad.update_button_states()
        return

    # -- Controller menu navigation for non-playing states --
    if game_state not in (STATE_PLAYING,):
        _handle_controller_menu_nav()
        gamepad.update_button_states()
        return

    # -- Controller: check pause/shoot buttons during gameplay --
    if gamepad.connected:
        if gamepad.is_button_just_pressed(BUTTON_PAUSE):
            toggle_pause()
            gamepad.update_button_states()
            return
        if shooting_mode and gamepad.is_button_just_pressed(BUTTON_SHOOT):
            proj = Projectile()
            projectiles.append(proj)

    # -- Difficulty scaling --
    player.forward_speed = min(
        BASE_FORWARD_SPEED + player.z * SPEED_INCREASE_RATE, MAX_FORWARD_SPEED
    )
    spawn_interval = max(
        BASE_SPAWN_INTERVAL - player.z * SPAWN_RATE_INCREASE, MIN_SPAWN_INTERVAL
    )

    # -- Player movement: combine keyboard + controller analog stick --
    stick_x, stick_y = gamepad.get_stick() if gamepad.connected else (0.0, 0.0)
    input_dir = Vec3(
        (held_keys["d"] - held_keys["a"]) + stick_x,
        (held_keys["w"] - held_keys["s"]) + stick_y,
        0,
    )
    if input_dir.length() > 1:
        input_dir = input_dir.normalized()

    player.velocity = lerp(
        player.velocity, input_dir * player.speed, PLAYER_INERTIA * time.dt
    )
    player.x += player.velocity.x * time.dt
    player.y += player.velocity.y * time.dt
    player.x = clamp(player.x, -BOUNDARY_X, BOUNDARY_X)
    player.y = clamp(player.y, -BOUNDARY_Y, BOUNDARY_Y)
    player.z += player.forward_speed * time.dt

    # Camera follow
    camera.position = (
        player.x + CAMERA_OFFSET.x,
        player.y + CAMERA_OFFSET.y,
        player.z + CAMERA_OFFSET.z,
    )
    camera.rotation = (CAMERA_PITCH, 0, 0)

    # Update 3D space background (parallax offsets, nebula rotation)
    space_bg.update(player, player.velocity, time.dt)

    # Ship tilt
    player.target_rotation_x = clamp(
        -PLAYER_MAX_PITCH * player.velocity.y / player.speed,
        -PLAYER_MAX_PITCH,
        PLAYER_MAX_PITCH,
    )
    player.target_rotation_z = clamp(
        -PLAYER_MAX_ROLL * player.velocity.x / player.speed,
        -PLAYER_MAX_ROLL,
        PLAYER_MAX_ROLL,
    )
    player.rotation_x = lerp(
        player.rotation_x, player.target_rotation_x, PLAYER_ROTATION_SMOOTHING * time.dt
    )
    player.rotation_z = lerp(
        player.rotation_z, player.target_rotation_z, PLAYER_ROTATION_SMOOTHING * time.dt
    )

    # -- Power depletion --
    power -= POWER_DEPLETION * time.dt
    if power <= 0:
        power = 0
        log(
            "GAME",
            "Game over - out of power",
            {"distance": int(player.z), "orbs": orbs_collected},
        )
        game_running = False
        player.visible = False
        hide_hud()
        _cleanup_game_entities()
        gamepad.rumble_player_death()  # Haptic feedback: strong vibration
        show_game_over()
        return

    # -- Spawn obstacles --
    spawn_timer -= time.dt
    if spawn_timer <= 0:
        spawn_obstacle()
        spawn_timer = spawn_interval

    # -- Spawn orbs --
    orb_spawn_timer -= time.dt
    if orb_spawn_timer <= 0:
        spawn_energy_orb()
        orb_spawn_timer = ORB_SPAWN_INTERVAL

    # -- Update obstacles & collision --
    obstacles_to_remove = []
    hit = False
    for obstacle in obstacles[:]:
        if obstacle._dead:
            obstacles_to_remove.append(obstacle)
            continue
        if obstacle.tick():
            obstacles_to_remove.append(obstacle)
            continue
        if not hit and check_collision(player, obstacle):
            log(
                "COLLISION",
                "Player hit meteorite",
                {"distance": int(player.z), "orbs": orbs_collected},
            )
            game_running = False
            player.visible = False
            hide_hud()
            _cleanup_game_entities()
            gamepad.rumble_player_death()  # Haptic feedback: strong vibration
            show_game_over()
            hit = True
    for obs in obstacles_to_remove:
        if obs in obstacles:
            obstacles.remove(obs)
    if hit:
        return

    # -- Shooting timer --
    if shooting_mode:
        shooting_timer -= time.dt
        if shooting_timer <= 0:
            shooting_mode = False
            log("GAME", "Shooting mode expired")

    # -- Update projectiles --
    projs_to_remove = []
    for proj in projectiles[:]:
        if proj._dead:
            projs_to_remove.append(proj)
            continue
        if proj.tick():
            projs_to_remove.append(proj)
    for p in projs_to_remove:
        if p in projectiles:
            projectiles.remove(p)

    # -- Update orbs --
    orbs_to_remove = []
    for orb in energy_orbs[:]:
        if orb._dead:
            orbs_to_remove.append(orb)
            continue
        if orb.tick():
            orbs_to_remove.append(orb)
            continue
        if check_orb_collision(player, orb):
            if orb.orb_type == "power":
                power = min(1.0, power + POWER_ORB_VALUE)
            elif orb.orb_type == "drain":
                power = max(0.0, power - DRAIN_ORB_VALUE)
                log("ORB", "Drain orb hit! Energy reduced", {"power": round(power, 2)})
            elif orb.orb_type == "speed_up":
                player.forward_speed += SPEED_BOOST_AMOUNT
                invoke(
                    setattr,
                    player,
                    "forward_speed",
                    BASE_FORWARD_SPEED,
                    delay=SPEED_BOOST_DURATION,
                )
            elif orb.orb_type == "slow_down":
                player.forward_speed = max(6, player.forward_speed - SLOW_AMOUNT)
                invoke(
                    setattr,
                    player,
                    "forward_speed",
                    BASE_FORWARD_SPEED,
                    delay=SLOW_DURATION,
                )
            elif orb.orb_type == "shooter":
                shooting_mode = True
                shooting_timer = SHOOTER_DURATION

            orbs_collected += 1
            log(
                "ORB",
                f"Collected {orb.orb_type} orb",
                {"total": orbs_collected, "power": round(power, 2)},
            )
            orb._dead = True
            destroy(orb)
            orbs_to_remove.append(orb)
    for orb in orbs_to_remove:
        if orb in energy_orbs:
            energy_orbs.remove(orb)

    # -- Update HUD (smooth power bar) --
    score_text.text = f"Orbs: {orbs_collected}"
    distance_text.text = f"Distance: {int(player.z)}"

    # Smoothly animate the displayed power bar width
    _displayed_power = lerp(_displayed_power, power, POWER_BAR_SMOOTH * time.dt)
    power_bar.scale_x = POWER_BAR_WIDTH * _displayed_power
    # Smoothly shift color via lerp
    if power > 0.5:
        target_color = color.green
    elif power > 0.2:
        target_color = color.yellow
    else:
        target_color = color.red
    power_bar.color = lerp(power_bar.color, target_color, 3 * time.dt)

    # Shooting indicator
    if shooting_mode:
        shooting_indicator.text = f"SHOOT [{int(shooting_timer)}s]"
    else:
        shooting_indicator.text = ""

    # -- Snapshot controller button states for edge detection next frame --
    gamepad.update_button_states()


# =============================================================================
#  LAUNCH  -  Show loading screen, preload assets, then transition to menu
# =============================================================================


def _finish_loading():
    """Called after assets are preloaded. Transition to start menu."""
    global game_state
    _hide_loading()
    game_state = STATE_MAIN_MENU
    show_start_menu()
    log("SYSTEM", "Application ready - showing start menu")


def _run_preload():
    """Run preloading then schedule menu display."""
    _do_preload()
    invoke(_finish_loading, delay=0.1)


# Schedule preload to run after the first frame so loading screen renders first
game_state = STATE_LOADING
invoke(_run_preload, delay=0.3)

app.run()

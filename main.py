"""
ORBIT RUSH — Main Game File
A 3D space survival game built with Ursina Engine.
Cross-platform compatible (Linux, Windows, macOS).
"""

from ursina import (
    Ursina, Entity, Vec3, Text, Color,
    camera, window, color, application,
    held_keys, time, invoke, destroy,
    clamp, lerp, curve,
    load_model, load_texture,
)
from random import random
import sys
import math

from src.config import (
    # Window
    WINDOW_TITLE, WINDOW_BORDERLESS, WINDOW_FULLSCREEN, SHOW_FPS,
    # Player / movement
    PLAYER_MODEL, PLAYER_TEXTURE,
    PLAYER_SPEED, PLAYER_INERTIA,
    PLAYER_MAX_PITCH, PLAYER_MAX_ROLL, PLAYER_ROTATION_SMOOTHING,
    BASE_FORWARD_SPEED, MAX_FORWARD_SPEED, SPEED_INCREASE_RATE,
    # Boundaries
    BOUNDARY_X, BOUNDARY_Y,
    # Obstacles / spawning
    METEORITE_MODELS,
    BASE_SPAWN_INTERVAL, MIN_SPAWN_INTERVAL, SPAWN_RATE_INCREASE,
    # Orbs
    ORB_SPAWN_INTERVAL, POWER_ORB_VALUE, DRAIN_ORB_VALUE,
    SPEED_BOOST_AMOUNT, SPEED_BOOST_DURATION,
    SLOW_AMOUNT, SLOW_DURATION,
    SHOOTER_DURATION, SHOOTER_GUARANTEE_DIST,
    # Power
    INITIAL_POWER, POWER_DEPLETION,
    # Camera
    CAMERA_OFFSET, CAMERA_PITCH,
    # UI colors
    COLOR_ACCENT, COLOR_BG_DARK,
    # States
    STATE_LOADING, STATE_MAIN_MENU, STATE_PLAYING,
    STATE_PAUSED, STATE_GAME_OVER, STATE_HELP, STATE_STATS,
)
from src.logger import log, clear_log
from src.stats import record_game
from src.controller import GameController, BUTTON_SHOOT, BUTTON_PAUSE
from src.space_background import SpaceBackground
from src.entities import (
    Player, Obstacle, EnergyOrb, Projectile,
    check_collision, check_orb_collision,
)
from src.ui import MenuManager, HELP_SCROLL_SPEED


# ─────────────────────────────────────────────────────────────────────────────
#  APPLICATION SETUP
# ─────────────────────────────────────────────────────────────────────────────

clear_log()
log("SYSTEM", "Application starting", {"os": sys.platform, "python": sys.version.split()[0]})

app = Ursina(title=WINDOW_TITLE, borderless=WINDOW_BORDERLESS, fullscreen=WINDOW_FULLSCREEN)
window.exit_button.visible = False
window.fps_counter.enabled = SHOW_FPS
window.color = color.black

# Dynamic 3D space background
space_bg = SpaceBackground()
log("SYSTEM", "Dynamic 3D space background created")

log("SYSTEM", "Ursina engine initialized", {"platform": sys.platform})

# Controller (optional — game works without one)
gamepad = GameController()
if gamepad.connected:
    log("SYSTEM", "Controller detected", {"name": gamepad.joystick.get_name()})
else:
    log("SYSTEM", "No controller detected — keyboard mode")

# UI manager
ui = MenuManager(gamepad)


# ─────────────────────────────────────────────────────────────────────────────
#  LOADING SCREEN
# ─────────────────────────────────────────────────────────────────────────────

loading_panel = Entity(parent=camera.ui, model="quad", color=COLOR_BG_DARK, scale=(2, 2), z=10)
loading_title = Text(
    parent=loading_panel, text="ORBIT RUSH",
    y=0.15, scale=3.0, origin=(0, 0), color=COLOR_ACCENT,
)
loading_msg = Text(
    parent=loading_panel, text="Loading assets...",
    y=0.03, scale=1.3, origin=(0, 0),
    color=Color(180 / 255, 180 / 255, 200 / 255, 1.0),
)

# Spinner dots
_spinner_dots = []
for _i in range(8):
    _angle = _i * (360 / 8)
    _rad = math.radians(_angle)
    _dot = Entity(
        parent=loading_panel, model="quad",
        color=Color(30 / 255, 144 / 255, 1.0, (1 - _i / 8)),
        scale=(0.012, 0.012),
        position=(math.sin(_rad) * 0.05, -0.06 + math.cos(_rad) * 0.05),
    )
    _spinner_dots.append(_dot)

_loading_angle = 0


def _update_spinner():
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
    global loading_panel
    if loading_panel:
        destroy(loading_panel)
        loading_panel = None
    log("UI", "Loading screen hidden")


# ─────────────────────────────────────────────────────────────────────────────
#  ASSET PRELOADING
# ─────────────────────────────────────────────────────────────────────────────

log("SYSTEM", "Preloading assets...")
_assets_ready = False


def _do_preload():
    global _assets_ready
    try:
        load_model(PLAYER_MODEL)
        log("SYSTEM", "Preloaded player model")
        load_texture(PLAYER_TEXTURE)
        log("SYSTEM", "Preloaded player texture")
        for i, met in enumerate(METEORITE_MODELS):
            load_model(met["model"])
            if met.get("texture"):
                load_texture(met["texture"])
            log("SYSTEM", f"Preloaded meteorite {i}")
        _assets_ready = True
        log("SYSTEM", "All assets preloaded successfully")
    except Exception as e:
        _assets_ready = True
        log("SYSTEM", f"Asset preload warning: {e}")


# ─────────────────────────────────────────────────────────────────────────────
#  GAME STATE
# ─────────────────────────────────────────────────────────────────────────────

player = Player()
player.visible = False
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
_displayed_power = INITIAL_POWER

game_running = True
game_state = STATE_LOADING

shooting_mode = False
shooting_timer = 0
last_special_orb_distance = 0

# Create HUD (hidden until gameplay)
ui.create_hud()


# ─────────────────────────────────────────────────────────────────────────────
#  GAME LOGIC HELPERS
# ─────────────────────────────────────────────────────────────────────────────

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
    obstacles.append(Obstacle(player_z=player.z))


def spawn_energy_orb():
    global last_special_orb_distance
    force_shooter = False
    if int(player.z // SHOOTER_GUARANTEE_DIST) > int(
        last_special_orb_distance // SHOOTER_GUARANTEE_DIST
    ):
        force_shooter = True
        last_special_orb_distance = player.z
    orb_type = choose_orb_type(force_shooter=force_shooter)
    orb = EnergyOrb(orb_type=orb_type, player_z=player.z)
    energy_orbs.append(orb)
    log("ORB", f"Spawned {orb_type} orb", {"z": round(orb.z, 1)})


def shatter_meteorite(meteorite):
    """Animate meteorite destruction with haptic feedback."""
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
    gamepad.rumble_meteor_destroy()
    log("GAME", "Meteorite shattered")


def _cleanup_game_entities():
    """Destroy all game world entities."""
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


# ─────────────────────────────────────────────────────────────────────────────
#  MENU CALLBACKS
# ─────────────────────────────────────────────────────────────────────────────

def _show_main_menu():
    global game_state
    game_state = STATE_MAIN_MENU
    player.visible = False
    ui.show_start_menu(
        on_start=start_game,
        on_stats=_show_stats,
        on_help=lambda: _show_help(back_fn=_show_main_menu),
    )


def _show_stats():
    global game_state
    game_state = STATE_STATS
    ui.show_stats_menu(back_fn=_show_main_menu)


def _show_help(back_fn=None):
    global game_state
    game_state = STATE_HELP
    ui.show_help(back_fn=back_fn or _show_main_menu)


def toggle_pause():
    global game_state
    if game_state == STATE_PLAYING:
        game_state = STATE_PAUSED
        ui.show_pause_menu(
            on_resume=_resume_from_pause,
            on_help=_pause_show_help,
            on_main_menu=_pause_return_to_menu,
            on_quit=application.quit,
        )
        log("GAME", "Game paused")
    elif game_state == STATE_PAUSED:
        game_state = STATE_PLAYING
        ui.hide_pause_menu()
        ui.show_hud()
        log("GAME", "Game resumed")


def _resume_from_pause():
    toggle_pause()


def _pause_return_to_menu():
    global game_state
    ui.hide_pause_menu()
    ui.hide_hud()
    player.visible = False
    _cleanup_game_entities()
    game_state = STATE_MAIN_MENU
    _show_main_menu()
    log("MENU", "Returned to main menu from pause")


def _pause_show_help():
    ui.hide_pause_menu()
    _show_help(back_fn=_back_to_pause)


def _back_to_pause():
    global game_state
    ui.clear_all()
    game_state = STATE_PAUSED
    ui.show_pause_menu(
        on_resume=_resume_from_pause,
        on_help=_pause_show_help,
        on_main_menu=_pause_return_to_menu,
        on_quit=application.quit,
    )


def _show_game_over():
    global game_state
    game_state = STATE_GAME_OVER
    stats = record_game(orbs_collected, int(player.z))
    log("STATS", "Game recorded", stats)
    is_best = (
        orbs_collected >= stats["max_score_orbs"]
        or int(player.z) >= stats["max_distance"]
    )
    ui.show_game_over(
        orbs=orbs_collected,
        distance=int(player.z),
        is_best=is_best,
        on_play_again=start_game,
        on_stats=_show_stats,
        on_main_menu=_show_main_menu,
    )


# ─────────────────────────────────────────────────────────────────────────────
#  START / RESTART
# ─────────────────────────────────────────────────────────────────────────────

def start_game():
    global game_state
    ui.clear_all()
    restart_game()
    player.visible = True
    ui.show_hud()
    game_state = STATE_PLAYING
    log("GAME", "Game started")


def restart_game():
    global game_running, orbs_collected, power, _displayed_power
    global spawn_timer, orb_spawn_timer
    global shooting_mode, shooting_timer, last_special_orb_distance

    ui.clear_all()
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

    energy_orbs.append(EnergyOrb(orb_type="shooter", position=(0, 0, 15)))
    log("GAME", "Game reset complete")


# ─────────────────────────────────────────────────────────────────────────────
#  INPUT
# ─────────────────────────────────────────────────────────────────────────────

def input(key):
    global game_state, shooting_mode

    # Escape: pause toggle or back navigation
    if key == "escape":
        if game_state in (STATE_PLAYING, STATE_PAUSED):
            toggle_pause()
            return
        if game_state in (STATE_HELP, STATE_STATS):
            if ui.back_fn:
                ui.back_fn()
            else:
                _show_main_menu()
            return

    if game_state == STATE_GAME_OVER and key == "r":
        start_game()
    if game_state == STATE_MAIN_MENU and key == "enter":
        start_game()
    if game_state == STATE_PLAYING and shooting_mode and key == "space":
        projectiles.append(Projectile(player.position, player.rotation))

    # Mouse scroll for help screen
    if game_state == STATE_HELP:
        if key == "scroll up":
            ui.scroll_help(-HELP_SCROLL_SPEED)
        elif key == "scroll down":
            ui.scroll_help(HELP_SCROLL_SPEED)


# ─────────────────────────────────────────────────────────────────────────────
#  MAIN UPDATE LOOP
# ─────────────────────────────────────────────────────────────────────────────

def update():
    global spawn_timer, game_running, orb_spawn_timer
    global orbs_collected, power, spawn_interval, game_state, _displayed_power
    global shooting_mode, shooting_timer

    # Always poll controller
    gamepad.poll(time.dt)

    # Loading screen animation
    if game_state == STATE_LOADING:
        _update_spinner()
        gamepad.update_button_states()
        return

    # Controller menu navigation for non-playing states
    if game_state != STATE_PLAYING:
        ui.handle_controller_menu(game_state, time.dt)
        gamepad.update_button_states()
        return

    # ── GAMEPLAY ─────────────────────────────────────────────────────────

    # Controller: pause / shoot buttons
    if gamepad.connected:
        if gamepad.is_button_just_pressed(BUTTON_PAUSE):
            toggle_pause()
            gamepad.update_button_states()
            return
        if shooting_mode and gamepad.is_button_just_pressed(BUTTON_SHOOT):
            projectiles.append(Projectile(player.position, player.rotation))

    # Difficulty scaling
    player.forward_speed = min(
        BASE_FORWARD_SPEED + player.z * SPEED_INCREASE_RATE, MAX_FORWARD_SPEED
    )
    spawn_interval = max(
        BASE_SPAWN_INTERVAL - player.z * SPAWN_RATE_INCREASE, MIN_SPAWN_INTERVAL
    )

    # Player movement (keyboard + controller)
    stick_x, stick_y = gamepad.get_stick() if gamepad.connected else (0.0, 0.0)
    input_dir = Vec3(
        (held_keys["d"] - held_keys["a"]) + stick_x,
        (held_keys["w"] - held_keys["s"]) + stick_y,
        0,
    )
    if input_dir.length() > 1:
        input_dir = input_dir.normalized()

    player.velocity = lerp(
        player.velocity, input_dir * player.speed, PLAYER_INERTIA * time.dt,
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

    # Background parallax
    space_bg.update(player, player.velocity, time.dt)

    # Ship tilt
    player.target_rotation_x = clamp(
        -PLAYER_MAX_PITCH * player.velocity.y / player.speed,
        -PLAYER_MAX_PITCH, PLAYER_MAX_PITCH,
    )
    player.target_rotation_z = clamp(
        -PLAYER_MAX_ROLL * player.velocity.x / player.speed,
        -PLAYER_MAX_ROLL, PLAYER_MAX_ROLL,
    )
    player.rotation_x = lerp(
        player.rotation_x, player.target_rotation_x, PLAYER_ROTATION_SMOOTHING * time.dt,
    )
    player.rotation_z = lerp(
        player.rotation_z, player.target_rotation_z, PLAYER_ROTATION_SMOOTHING * time.dt,
    )

    # Power depletion
    power -= POWER_DEPLETION * time.dt
    if power <= 0:
        power = 0
        log("GAME", "Game over — out of power",
            {"distance": int(player.z), "orbs": orbs_collected})
        game_running = False
        player.visible = False
        ui.hide_hud()
        _cleanup_game_entities()
        gamepad.rumble_player_death()
        _show_game_over()
        return

    # Spawn obstacles
    spawn_timer -= time.dt
    if spawn_timer <= 0:
        spawn_obstacle()
        spawn_timer = spawn_interval

    # Spawn orbs
    orb_spawn_timer -= time.dt
    if orb_spawn_timer <= 0:
        spawn_energy_orb()
        orb_spawn_timer = ORB_SPAWN_INTERVAL

    # Update obstacles & collision
    obstacles_to_remove = []
    hit = False
    for obstacle in obstacles[:]:
        if obstacle._dead:
            obstacles_to_remove.append(obstacle)
            continue
        if obstacle.tick(player.z):
            obstacles_to_remove.append(obstacle)
            continue
        if not hit and check_collision(player, obstacle):
            log("COLLISION", "Player hit meteorite",
                {"distance": int(player.z), "orbs": orbs_collected})
            game_running = False
            player.visible = False
            ui.hide_hud()
            _cleanup_game_entities()
            gamepad.rumble_player_death()
            _show_game_over()
            hit = True
    for obs in obstacles_to_remove:
        if obs in obstacles:
            obstacles.remove(obs)
    if hit:
        return

    # Shooting timer
    if shooting_mode:
        shooting_timer -= time.dt
        if shooting_timer <= 0:
            shooting_mode = False
            log("GAME", "Shooting mode expired")

    # Update projectiles
    projs_to_remove = []
    for proj in projectiles[:]:
        if proj._dead:
            projs_to_remove.append(proj)
            continue
        if proj.tick(player.z, obstacles, shatter_meteorite):
            projs_to_remove.append(proj)
    for p in projs_to_remove:
        if p in projectiles:
            projectiles.remove(p)

    # Update orbs & collection
    orbs_to_remove = []
    for orb in energy_orbs[:]:
        if orb._dead:
            orbs_to_remove.append(orb)
            continue
        if orb.tick(player.z):
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
                invoke(setattr, player, "forward_speed", BASE_FORWARD_SPEED,
                       delay=SPEED_BOOST_DURATION)
            elif orb.orb_type == "slow_down":
                player.forward_speed = max(6, player.forward_speed - SLOW_AMOUNT)
                invoke(setattr, player, "forward_speed", BASE_FORWARD_SPEED,
                       delay=SLOW_DURATION)
            elif orb.orb_type == "shooter":
                shooting_mode = True
                shooting_timer = SHOOTER_DURATION

            orbs_collected += 1
            log("ORB", f"Collected {orb.orb_type} orb",
                {"total": orbs_collected, "power": round(power, 2)})
            orb._dead = True
            destroy(orb)
            orbs_to_remove.append(orb)
    for orb in orbs_to_remove:
        if orb in energy_orbs:
            energy_orbs.remove(orb)

    # Update HUD
    _displayed_power = ui.update_hud(
        orbs_collected, player.z, power, _displayed_power,
        shooting_mode, shooting_timer, time.dt,
    )

    # Snapshot controller buttons for edge detection
    gamepad.update_button_states()


# ─────────────────────────────────────────────────────────────────────────────
#  LAUNCH
# ─────────────────────────────────────────────────────────────────────────────

def _finish_loading():
    global game_state
    _hide_loading()
    game_state = STATE_MAIN_MENU
    _show_main_menu()
    log("SYSTEM", "Application ready — showing start menu")


def _run_preload():
    _do_preload()
    invoke(_finish_loading, delay=0.1)


game_state = STATE_LOADING
invoke(_run_preload, delay=0.3)

app.run()

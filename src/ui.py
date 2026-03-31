"""
ORBIT RUSH — UI & Menu System
HUD elements, menu screens, button helpers, and controller navigation.
"""

from ursina import (
    Entity,
    Text,
    Button,
    camera,
    color,
    Color,
    destroy,
    time,
    clamp,
    application,
)
from random import uniform, random as _rnd

from src.config import (
    COLOR_BG_DARK,
    COLOR_ACCENT,
    COLOR_ACCENT_HOVER,
    COLOR_ORANGE,
    COLOR_ORANGE_HOVER,
    COLOR_PURPLE,
    COLOR_PURPLE_HOVER,
    COLOR_TEXT,
    COLOR_TEXT_DIM,
    GAME_VERSION,
    CREDITS,
    TITLE_TEXTURE,
    POWER_BAR_WIDTH,
    POWER_BAR_HEIGHT,
    STATE_HELP,
)
from src.stats import load_stats
from src.logger import log
from src.controller import get_controller_mappings, BUTTON_CONFIRM, BUTTON_BACK

# ── Help screen scroll settings ──────────────────────────────────────────────
HELP_SCROLL_SPEED = 0.05
HELP_SCROLL_STICK_SPEED = 0.35
HELP_SCROLL_MIN = 0.0
HELP_SCROLL_MAX = 0.65


# ─────────────────────────────────────────────────────────────────────────────
#  STYLED BUTTON HELPER
# ─────────────────────────────────────────────────────────────────────────────


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
    """Create a compact, clean menu button."""
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
    if btn.text_entity:
        btn.text_entity.color = COLOR_TEXT
    return btn


# ─────────────────────────────────────────────────────────────────────────────
#  MENU MANAGER  (owns all UI panels, HUD, and controller navigation)
# ─────────────────────────────────────────────────────────────────────────────


class MenuManager:
    """Centralised UI manager for menus, HUD, and controller navigation."""

    def __init__(self, gamepad):
        self.gamepad = gamepad

        # Panels
        self.menu_panel = None
        self.help_panel = None
        self.game_over_panel = None
        self.stats_panel = None
        self.pause_panel = None

        # Menu navigation state
        self._menu_buttons = []
        self._menu_selected = 0
        self._menu_back_fn = None

        # Help scroll state
        self._help_content = None
        self._help_scroll_y = 0.0

        # HUD elements (created lazily)
        self.hud_panel = None
        self.score_text = None
        self.distance_text = None
        self.power_bar_bg = None
        self.power_bar = None
        self.shooting_indicator = None
        self._hud_created = False

    # ── HUD ──────────────────────────────────────────────────────────────

    def create_hud(self):
        """Create the in-game heads-up display elements."""
        if self._hud_created:
            return

        self.hud_panel = Entity(
            parent=camera.ui,
            model="quad",
            color=Color(10 / 255, 10 / 255, 28 / 255, 180 / 255),
            scale=(0.19, 0.08),
            position=(-0.76, 0.435),
            z=2,
        )
        Entity(
            parent=self.hud_panel,
            model="quad",
            color=COLOR_ACCENT,
            scale=(0.015, 1),
            origin=(-0.5, 0),
            x=-0.5,
            z=-0.1,
        )
        self.score_text = Text(
            text="Orbs: 0",
            position=(-0.84, 0.455),
            scale=1.0,
            color=color.white,
            background=False,
        )
        self.distance_text = Text(
            text="Distance: 0",
            position=(-0.84, 0.43),
            scale=1.0,
            color=COLOR_TEXT_DIM,
            background=False,
        )
        self.power_bar_bg = Entity(
            parent=camera.ui,
            model="quad",
            color=Color(40 / 255, 40 / 255, 40 / 255, 200 / 255),
            scale=(POWER_BAR_WIDTH + 0.02, POWER_BAR_HEIGHT + 0.01),
            position=(0, 0.46),
            z=1,
        )
        self.power_bar = Entity(
            parent=camera.ui,
            model="quad",
            color=color.green,
            scale=(POWER_BAR_WIDTH, POWER_BAR_HEIGHT),
            position=(0, 0.46),
            z=0,
        )
        self.shooting_indicator = Text(
            text="",
            position=(0.60, 0.455),
            scale=1.0,
            color=color.red,
            background=False,
        )
        self._hud_created = True
        self.hide_hud()

    def hide_hud(self):
        if not self._hud_created:
            return
        for el in (
            self.hud_panel,
            self.score_text,
            self.distance_text,
            self.power_bar_bg,
            self.power_bar,
            self.shooting_indicator,
        ):
            el.visible = False

    def show_hud(self):
        if not self._hud_created:
            self.create_hud()
        for el in (
            self.hud_panel,
            self.score_text,
            self.distance_text,
            self.power_bar_bg,
            self.power_bar,
            self.shooting_indicator,
        ):
            el.visible = True

    def update_hud(
        self, orbs, distance, power, displayed_power, shooting_mode, shooting_timer, dt
    ):
        """Update HUD values each frame. Returns the new displayed_power."""
        from ursina import lerp
        from src.config import POWER_BAR_WIDTH, POWER_BAR_SMOOTH

        self.score_text.text = f"Orbs: {orbs}"
        self.distance_text.text = f"Distance: {int(distance)}"

        displayed_power = lerp(displayed_power, power, POWER_BAR_SMOOTH * dt)
        self.power_bar.scale_x = POWER_BAR_WIDTH * displayed_power

        if power > 0.5:
            target_color = color.green
        elif power > 0.2:
            target_color = color.yellow
        else:
            target_color = color.red
        self.power_bar.color = lerp(self.power_bar.color, target_color, 3 * dt)

        if shooting_mode:
            self.shooting_indicator.text = f"SHOOT [{int(shooting_timer)}s]"
        else:
            self.shooting_indicator.text = ""

        return displayed_power

    # ── Menu Navigation (controller) ─────────────────────────────────────

    def _clear_nav(self):
        for btn in self._menu_buttons:
            if hasattr(btn, "_base_color"):
                try:
                    btn.color = btn._base_color
                except Exception:
                    pass
        self._menu_buttons = []
        self._menu_selected = 0
        self._menu_back_fn = None

    def _register_buttons(self, buttons, back_fn=None):
        self._clear_nav()
        self._menu_buttons = list(buttons)
        self._menu_selected = 0
        self._menu_back_fn = back_fn
        self._highlight_selected()

    def _highlight_selected(self):
        for i, btn in enumerate(self._menu_buttons):
            if not hasattr(btn, "_base_color"):
                btn._base_color = btn.color
            try:
                btn.color = (
                    btn.highlight_color if i == self._menu_selected else btn._base_color
                )
            except Exception:
                pass

    def _navigate(self, direction):
        if not self._menu_buttons:
            return
        self._menu_selected = (self._menu_selected + direction) % len(
            self._menu_buttons
        )
        self._highlight_selected()

    def _confirm(self):
        if self._menu_buttons and 0 <= self._menu_selected < len(self._menu_buttons):
            btn = self._menu_buttons[self._menu_selected]
            if btn.on_click:
                btn.on_click()

    def handle_controller_menu(self, game_state, dt):
        """Process controller input for menus. Call each frame when not playing."""
        if not self.gamepad.connected:
            return
        if game_state == STATE_HELP and self._help_content is not None:
            _, stick_y = self.gamepad.get_stick()
            if abs(stick_y) > 0.3:
                self._scroll_help(-stick_y * HELP_SCROLL_STICK_SPEED * dt)
        else:
            nav = self.gamepad.get_menu_nav(dt)
            if nav != 0:
                self._navigate(nav)
        if self.gamepad.is_button_just_pressed(BUTTON_CONFIRM):
            self._confirm()
        if self.gamepad.is_button_just_pressed(BUTTON_BACK):
            if self._menu_back_fn:
                self._menu_back_fn()

    @property
    def back_fn(self):
        return self._menu_back_fn

    # ── Panel management ─────────────────────────────────────────────────

    def clear_all(self):
        """Destroy all menu/overlay panels."""
        for panel in (
            self.menu_panel,
            self.help_panel,
            self.game_over_panel,
            self.stats_panel,
            self.pause_panel,
        ):
            if panel:
                destroy(panel)
        self.menu_panel = None
        self.help_panel = None
        self.game_over_panel = None
        self.stats_panel = None
        self.pause_panel = None
        self._help_content = None
        self._clear_nav()
        log("UI", "Cleared all UI panels")

    # ── Start Menu ───────────────────────────────────────────────────────

    def show_start_menu(self, on_start, on_stats, on_help):
        """Display the main menu."""
        self.clear_all()
        self.hide_hud()
        log("MENU", "Showing start menu")

        # Pure black background to match the title image
        self.menu_panel = Entity(
            parent=camera.ui,
            model="quad",
            color=color.black,
            scale=(2, 2),
            z=5,
        )

        # Decorative stars scattered on the sides
        self._spawn_menu_stars()

        # Logo
        Entity(
            parent=self.menu_panel,
            model="quad",
            texture=TITLE_TEXTURE,
            scale=(0.4, 0.30),
            y=0.15,
            z=-1,
            unlit=True,
            color=color.white,
        )
        Entity(
            parent=self.menu_panel,
            model="quad",
            color=Color(1, 1, 1, 0.1),
            scale=(0.4, 0.001),
            y=0.08,
        )

        btns = []
        btns.append(
            make_button(self.menu_panel, "START GAME", y=-0.02, on_click=on_start)
        )
        btns.append(
            make_button(
                self.menu_panel,
                "STATS",
                y=-0.07,
                on_click=on_stats,
                btn_color=COLOR_PURPLE,
                hover_color=COLOR_PURPLE_HOVER,
            )
        )
        btns.append(
            make_button(
                self.menu_panel,
                "HELP & CONTROLS",
                y=-0.12,
                on_click=on_help,
                btn_color=COLOR_ORANGE,
                hover_color=COLOR_ORANGE_HOVER,
            )
        )
        self._register_buttons(btns)

        # Footer
        Entity(
            parent=self.menu_panel,
            model="quad",
            color=Color(1, 1, 1, 0.06),
            scale=(0.4, 0.001),
            y=-0.20,
        )
        Text(
            parent=self.menu_panel,
            text=CREDITS,
            y=-0.24,
            scale=0.7,
            origin=(0, 0),
            color=COLOR_TEXT_DIM,
        )
        Text(
            parent=self.menu_panel,
            text=GAME_VERSION,
            y=-0.27,
            scale=0.6,
            origin=(0, 0),
            color=Color(100 / 255, 100 / 255, 120 / 255, 1.0),
        )

    # ── Menu Stars ────────────────────────────────────────────────────────

    def _spawn_menu_stars(self):
        """Add small decorative star dots to the left and right sides of the menu."""
        # Star colours: mostly white/blue to complement the blue title text
        _star_colors = [
            Color(1.0, 1.0, 1.0, 1.0),  # white
            Color(0.85, 0.90, 1.0, 1.0),  # cool white
            Color(0.5, 0.7, 1.0, 1.0),  # soft blue
            Color(0.3, 0.55, 1.0, 1.0),  # vivid blue
            Color(0.25, 0.80, 1.0, 1.0),  # cyan
        ]
        for _ in range(60):
            # Place stars on the LEFT and RIGHT margins (avoid center where logo/buttons sit)
            side = 1 if _rnd() > 0.5 else -1
            sx = side * uniform(0.22, 0.48)  # x: outside the center content area
            sy = uniform(-0.46, 0.46)  # y: full vertical range
            size = uniform(0.002, 0.006)
            brightness = uniform(0.3, 1.0)
            sc = _star_colors[int(_rnd() * len(_star_colors)) % len(_star_colors)]
            Entity(
                parent=self.menu_panel,
                model="quad",
                color=Color(
                    sc.r * brightness, sc.g * brightness, sc.b * brightness, brightness
                ),
                scale=(size, size),
                position=(sx, sy),
                z=-0.05,
            )
        # A few slightly larger "glow" stars for depth
        for _ in range(8):
            side = 1 if _rnd() > 0.5 else -1
            sx = side * uniform(0.25, 0.45)
            sy = uniform(-0.40, 0.40)
            size = uniform(0.008, 0.015)
            brightness = uniform(0.15, 0.35)
            Entity(
                parent=self.menu_panel,
                model="quad",
                color=Color(
                    0.4 * brightness,
                    0.6 * brightness,
                    1.0 * brightness,
                    brightness * 0.6,
                ),
                scale=(size, size),
                position=(sx, sy),
                z=-0.04,
            )

    # ── Help Screen ──────────────────────────────────────────────────────

    def show_help(self, back_fn):
        """Display the scrollable help/controls screen."""
        self.clear_all()
        self._help_scroll_y = 0.0
        log("MENU", "Showing help screen")

        self.help_panel = Entity(
            parent=camera.ui,
            model="quad",
            color=Color(12 / 255, 12 / 255, 28 / 255, 1.0),
            scale=(2, 2),
            z=5,
        )

        # Fixed header
        Text(
            parent=self.help_panel,
            text="CONTROLS & HELP",
            y=0.44,
            scale=0.9,
            origin=(0, 0),
            color=color.yellow,
            z=-0.5,
        )
        Entity(
            parent=self.help_panel,
            model="quad",
            color=color.yellow,
            scale=(0.50, 0.002),
            y=0.415,
            z=-0.1,
        )
        Text(
            parent=self.help_panel,
            text="Scroll: Mouse wheel / Controller stick",
            y=0.395,
            scale=0.35,
            origin=(0, 0),
            color=COLOR_TEXT_DIM,
            z=-0.5,
        )

        # Scrollable content container
        self._help_content = Entity(parent=self.help_panel, z=-0.2)
        cy = 0.05

        Text(
            parent=self._help_content,
            text="Survive as long as you can!",
            y=cy,
            scale=0.5,
            origin=(0, 0),
            color=COLOR_TEXT_DIM,
            z=-0.5,
        )
        cy -= 0.035
        Entity(
            parent=self._help_content,
            model="quad",
            color=Color(1, 1, 1, 0.15),
            scale=(0.35, 0.001),
            y=cy,
            z=-0.1,
        )
        cy -= 0.03

        # Keyboard controls
        Text(
            parent=self._help_content,
            text="KEYBOARD CONTROLS",
            y=cy,
            scale=0.6,
            origin=(0, 0),
            color=COLOR_ACCENT,
            z=-0.5,
        )
        cy -= 0.03
        for line in [
            "W / S       :  Up / Down",
            "A / D       :  Left / Right",
            "Space       :  Shoot (when active)",
            "ESC         :  Pause Menu",
        ]:
            Text(
                parent=self._help_content,
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
            parent=self._help_content,
            model="quad",
            color=Color(1, 1, 1, 0.15),
            scale=(0.35, 0.001),
            y=cy,
            z=-0.1,
        )
        cy -= 0.03

        # Controller controls
        Text(
            parent=self._help_content,
            text="CONTROLLER CONTROLS",
            y=cy,
            scale=0.6,
            origin=(0, 0),
            color=Color(0.2, 0.8, 1.0, 1.0),
            z=-0.5,
        )
        cy -= 0.03
        for btn_label, action in get_controller_mappings():
            Text(
                parent=self._help_content,
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
            parent=self._help_content,
            model="quad",
            color=Color(1, 1, 1, 0.15),
            scale=(0.35, 0.001),
            y=cy,
            z=-0.1,
        )
        cy -= 0.03

        # Orb types
        Text(
            parent=self._help_content,
            text="ORB TYPES",
            y=cy,
            scale=0.6,
            origin=(0, 0),
            color=COLOR_ORANGE,
            z=-0.5,
        )
        cy -= 0.03
        for txt, clr in [
            ("Green   - Power    : Restores energy", color.lime),
            ("Orange  - Drain    : Removes energy", Color(1.0, 100 / 255, 0, 1.0)),
            (
                "Purple  - Speed Up : Faster for 3s",
                Color(180 / 255, 100 / 255, 1.0, 1.0),
            ),
            ("Blue    - Slow     : Slower for 3s", color.azure),
            ("Red     - Shooter  : Shoot for 10s", color.red),
        ]:
            Text(
                parent=self._help_content,
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
            parent=self._help_content,
            model="quad",
            color=Color(1, 1, 1, 0.15),
            scale=(0.35, 0.001),
            y=cy,
            z=-0.1,
        )
        cy -= 0.03

        # Gameplay tips
        Text(
            parent=self._help_content,
            text="GAMEPLAY",
            y=cy,
            scale=0.6,
            origin=(0, 0),
            color=color.lime,
            z=-0.5,
        )
        cy -= 0.03
        Text(
            parent=self._help_content,
            text="- Avoid meteorites\n- Collect orbs to stay alive\n"
            "- Keep power bar up\n- Space / RB to shoot (red orb)",
            y=cy,
            scale=0.42,
            origin=(0, 0),
            color=COLOR_TEXT,
            z=-0.5,
        )

        # Fixed footer
        Entity(
            parent=self.help_panel,
            model="quad",
            color=Color(12 / 255, 12 / 255, 28 / 255, 1.0),
            scale=(2, 0.12),
            y=-0.44,
            z=-0.3,
        )
        btns = [make_button(self.help_panel, "BACK", y=-0.44, on_click=back_fn)]
        self._register_buttons(btns, back_fn=back_fn)

    def scroll_help(self, amount):
        """Scroll the help content."""
        if self._help_content is None:
            return
        self._help_scroll_y = clamp(
            self._help_scroll_y + amount,
            HELP_SCROLL_MIN,
            HELP_SCROLL_MAX,
        )
        self._help_content.y = self._help_scroll_y

    def _scroll_help(self, amount):
        self.scroll_help(amount)

    # ── Stats Screen ─────────────────────────────────────────────────────

    def show_stats_menu(self, back_fn):
        """Display the player statistics screen."""
        self.clear_all()
        log("MENU", "Showing stats screen")

        stats = load_stats()
        log("STATS", "Stats loaded", stats)

        self.stats_panel = Entity(
            parent=camera.ui,
            model="quad",
            color=Color(12 / 255, 12 / 255, 28 / 255, 1.0),
            scale=(2, 2),
            z=5,
        )

        Entity(
            parent=self.stats_panel,
            model="quad",
            color=COLOR_ACCENT,
            scale=(0.40, 0.002),
            y=0.18,
            z=-0.1,
        )
        Text(
            parent=self.stats_panel,
            text="YOUR STATS",
            y=0.15,
            scale=0.9,
            origin=(0, 0),
            color=COLOR_ACCENT,
            z=-0.5,
        )
        Entity(
            parent=self.stats_panel,
            model="quad",
            color=Color(1, 1, 1, 0.15),
            scale=(0.30, 0.001),
            y=0.12,
            z=-0.1,
        )

        stat_items = [
            ("Games Played", str(stats["total_games_played"])),
            ("Best Score", str(stats["max_score_orbs"])),
            ("Best Distance", str(stats["max_distance"])),
        ]
        for i, (label, val) in enumerate(stat_items):
            row_y = 0.08 - i * 0.045
            Text(
                parent=self.stats_panel,
                text=label,
                y=row_y,
                x=-0.04,
                scale=0.5,
                origin=(1, 0),
                color=COLOR_TEXT_DIM,
                z=-0.5,
            )
            Text(
                parent=self.stats_panel,
                text=val,
                y=row_y,
                x=0.04,
                scale=0.55,
                origin=(-1, 0),
                color=COLOR_TEXT,
                z=-0.5,
            )

        Entity(
            parent=self.stats_panel,
            model="quad",
            color=Color(1, 1, 1, 0.15),
            scale=(0.30, 0.001),
            y=-0.065,
            z=-0.1,
        )

        last = stats.get("last_games", [])
        if last:
            g = last[0]
            Text(
                parent=self.stats_panel,
                text="LAST GAME",
                y=-0.09,
                scale=0.55,
                origin=(0, 0),
                color=COLOR_ORANGE,
                z=-0.5,
            )
            Text(
                parent=self.stats_panel,
                text=f"Orbs: {g.get('orbs_collected', 0)}   Dist: {g.get('distance', 0)}",
                y=-0.125,
                scale=0.45,
                origin=(0, 0),
                color=COLOR_TEXT,
                z=-0.5,
            )
        else:
            Text(
                parent=self.stats_panel,
                text="No games played yet.",
                y=-0.09,
                scale=0.5,
                origin=(0, 0),
                color=COLOR_TEXT_DIM,
                z=-0.5,
            )

        btns = [
            make_button(self.stats_panel, "BACK TO MENU", y=-0.20, on_click=back_fn)
        ]
        self._register_buttons(btns, back_fn=back_fn)

    # ── Game Over Screen ─────────────────────────────────────────────────

    def show_game_over(
        self, orbs, distance, is_best, on_play_again, on_stats, on_main_menu
    ):
        """Display the game-over screen with final scores."""
        self.clear_all()
        log("MENU", "Showing game over screen", {"orbs": orbs, "distance": distance})

        self.game_over_panel = Entity(
            parent=camera.ui,
            model="quad",
            color=Color(12 / 255, 12 / 255, 28 / 255, 1.0),
            scale=(2, 2),
            z=5,
        )

        card_h = 0.42 if is_best else 0.38
        Entity(
            parent=self.game_over_panel,
            model="quad",
            color=Color(22 / 255, 22 / 255, 50 / 255, 1.0),
            scale=(0.40, card_h),
            y=0.0,
            z=-0.1,
        )
        Entity(
            parent=self.game_over_panel,
            model="quad",
            color=color.red,
            scale=(0.40, 0.003),
            y=card_h / 2,
            z=-0.2,
        )

        Text(
            parent=self.game_over_panel,
            text="GAME OVER",
            y=card_h / 2 - 0.04,
            scale=1.1,
            origin=(0, 0),
            color=color.red,
            z=-0.5,
        )
        Entity(
            parent=self.game_over_panel,
            model="quad",
            color=Color(1, 1, 1, 0.12),
            scale=(0.26, 0.001),
            y=card_h / 2 - 0.07,
            z=-0.2,
        )

        info_top = card_h / 2 - 0.10
        Text(
            parent=self.game_over_panel,
            text=f"Orbs Collected :  {orbs}",
            y=info_top,
            scale=0.6,
            origin=(0, 0),
            color=color.lime,
            z=-0.5,
        )
        Text(
            parent=self.game_over_panel,
            text=f"Distance :  {distance}",
            y=info_top - 0.03,
            scale=0.6,
            origin=(0, 0),
            color=color.cyan,
            z=-0.5,
        )

        best_offset = 0.0
        if is_best:
            Text(
                parent=self.game_over_panel,
                text="NEW PERSONAL BEST!",
                y=info_top - 0.07,
                scale=0.55,
                origin=(0, 0),
                color=color.yellow,
                z=-0.5,
            )
            best_offset = 0.035

        sep_y = info_top - 0.085 - best_offset
        Entity(
            parent=self.game_over_panel,
            model="quad",
            color=Color(1, 1, 1, 0.12),
            scale=(0.26, 0.001),
            y=sep_y,
            z=-0.2,
        )

        btn_y = sep_y - 0.035
        btns = []
        btns.append(
            make_button(
                self.game_over_panel, "PLAY AGAIN", y=btn_y, on_click=on_play_again
            )
        )
        btns.append(
            make_button(
                self.game_over_panel,
                "VIEW STATS",
                y=btn_y - 0.045,
                on_click=on_stats,
                btn_color=COLOR_PURPLE,
                hover_color=COLOR_PURPLE_HOVER,
            )
        )
        btns.append(
            make_button(
                self.game_over_panel,
                "MAIN MENU",
                y=btn_y - 0.09,
                on_click=on_main_menu,
                btn_color=COLOR_ORANGE,
                hover_color=COLOR_ORANGE_HOVER,
            )
        )
        self._register_buttons(btns)

    # ── Pause Menu ───────────────────────────────────────────────────────

    def show_pause_menu(self, on_resume, on_help, on_main_menu, on_quit):
        """Display the pause overlay."""
        self.hide_pause_menu()
        self.hide_hud()
        self._clear_nav()

        self.pause_panel = Entity(
            parent=camera.ui,
            model="quad",
            color=Color(0, 0, 0, 0.75),
            scale=(2, 2),
            z=5,
        )

        Text(
            parent=self.pause_panel,
            text="PAUSED",
            y=0.15,
            scale=1.8,
            origin=(0, 0),
            color=COLOR_ACCENT,
            z=-0.5,
        )
        Entity(
            parent=self.pause_panel,
            model="quad",
            color=Color(1, 1, 1, 0.15),
            scale=(0.3, 0.001),
            y=0.09,
            z=-0.1,
        )

        btns = []
        btns.append(
            make_button(self.pause_panel, "RESUME GAME", y=0.04, on_click=on_resume)
        )
        btns.append(
            make_button(
                self.pause_panel,
                "HELP & CONTROLS",
                y=-0.01,
                on_click=on_help,
                btn_color=COLOR_ORANGE,
                hover_color=COLOR_ORANGE_HOVER,
            )
        )
        btns.append(
            make_button(
                self.pause_panel,
                "RETURN TO MAIN MENU",
                y=-0.06,
                on_click=on_main_menu,
                btn_color=COLOR_PURPLE,
                hover_color=COLOR_PURPLE_HOVER,
            )
        )
        btns.append(
            make_button(
                self.pause_panel,
                "QUIT GAME",
                y=-0.11,
                on_click=on_quit,
                btn_color=color.red,
                hover_color=Color(1, 0.3, 0.3, 1),
            )
        )
        self._register_buttons(btns, back_fn=on_resume)

    def hide_pause_menu(self):
        if self.pause_panel:
            destroy(self.pause_panel)
            self.pause_panel = None

"""
Controller Input Module
Handles gamepad/joystick input using pygame.
Supports analog movement, button mapping, deadzone handling, and haptic feedback.

Usage:
    from controller import GameController, get_controller_mappings
    gamepad = GameController()
    # In update loop:
    gamepad.poll()
    x, y = gamepad.get_stick()
    if gamepad.is_button_just_pressed(BUTTON_SHOOT): ...
    gamepad.update_button_states()  # Call at end of frame
"""

# pygame is optional — game works with keyboard alone if not installed
try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

# =============================================================================
#  BUTTON MAPPING CONSTANTS
# =============================================================================

BUTTON_SHOOT = 5        # RB  – right bumper / shoulder
BUTTON_PAUSE = 1        # B1  – pause / menu toggle
BUTTON_CONFIRM = 0      # A   – confirm / select
BUTTON_BACK = 1         # B   – back / cancel (same as pause; contexts don't overlap)

# =============================================================================
#  ANALOG STICK CONSTANTS
# =============================================================================

STICK_DEADZONE = 0.2    # Ignore input below this threshold
AXIS_X = 0              # Left stick horizontal axis index
AXIS_Y = 1              # Left stick vertical axis index

# =============================================================================
#  VIBRATION / HAPTIC PRESETS  (low_freq, high_freq, duration_ms)
# =============================================================================

VIBRATION_METEOR_DESTROY = (0.3, 0.3, 150)   # Short, light
VIBRATION_PLAYER_DEATH   = (0.8, 0.8, 400)   # Longer, stronger

# =============================================================================
#  MENU NAVIGATION
# =============================================================================

MENU_NAV_COOLDOWN = 0.22  # Seconds between stick-driven menu ticks


# =============================================================================
#  GAMECONTROLLER CLASS
# =============================================================================

class GameController:
    """Manages a single gamepad via the pygame joystick subsystem."""

    def __init__(self):
        self.joystick = None
        self.connected = False
        self._last_buttons = {}
        self._menu_nav_timer = 0.0
        self._initialized = False
        self._reconnect_timer = 0.0

        if not PYGAME_AVAILABLE:
            return

        try:
            # Only init the subsystems we need (avoid opening a pygame window)
            if not pygame.get_init():
                pygame.init()
            pygame.joystick.init()
            self._initialized = True
            self._detect_controller()
        except Exception as e:
            print(f"[CONTROLLER] pygame init warning: {e}")

    # ── Connection management ──────────────────────────────────────────────

    def _detect_controller(self):
        """Detect and initialise the first available controller."""
        if not self._initialized:
            return
        try:
            pygame.joystick.quit()
            pygame.joystick.init()
            if pygame.joystick.get_count() > 0:
                self.joystick = pygame.joystick.Joystick(0)
                self.joystick.init()
                self.connected = True
                self._last_buttons = {}
                print(f"[CONTROLLER] Connected: {self.joystick.get_name()}")
            else:
                self.joystick = None
                self.connected = False
        except Exception as e:
            self.joystick = None
            self.connected = False
            print(f"[CONTROLLER] Detection error: {e}")

    def poll(self, dt=0):
        """
        Pump pygame events.  Must be called once per frame.
        Handles automatic reconnection when a controller is plugged in.
        """
        if not self._initialized:
            return
        try:
            pygame.event.pump()
        except Exception:
            return

        # Periodically retry connection if not connected
        if not self.connected:
            self._reconnect_timer -= dt
            if self._reconnect_timer <= 0:
                self._reconnect_timer = 2.0  # check every 2 seconds
                try:
                    if pygame.joystick.get_count() > 0:
                        self._detect_controller()
                except Exception:
                    pass

    # ── Analog stick ───────────────────────────────────────────────────────

    def get_stick(self):
        """
        Return left-stick input with deadzone applied.
        Returns (x, y) in [-1.0, 1.0].  Y is inverted so UP = positive.
        """
        if not self.connected or not self.joystick:
            return (0.0, 0.0)
        try:
            raw_x = self.joystick.get_axis(AXIS_X)
            raw_y = self.joystick.get_axis(AXIS_Y)
            return (self._apply_deadzone(raw_x), self._apply_deadzone(-raw_y))
        except Exception:
            return (0.0, 0.0)

    @staticmethod
    def _apply_deadzone(value):
        """Apply deadzone with smooth scaling of the remaining range."""
        if abs(value) < STICK_DEADZONE:
            return 0.0
        sign = 1.0 if value > 0 else -1.0
        scaled = (abs(value) - STICK_DEADZONE) / (1.0 - STICK_DEADZONE)
        return sign * min(scaled, 1.0)

    # ── Buttons ────────────────────────────────────────────────────────────

    def is_button_pressed(self, button_id):
        """Check if a button is currently held down."""
        if not self.connected or not self.joystick:
            return False
        try:
            if button_id < self.joystick.get_numbuttons():
                return self.joystick.get_button(button_id) == 1
        except Exception:
            pass
        return False

    def is_button_just_pressed(self, button_id):
        """
        Rising-edge detection — True only on the frame the button goes down.
        Call ``update_button_states()`` at the END of each frame.
        """
        current = self.is_button_pressed(button_id)
        previous = self._last_buttons.get(button_id, False)
        return current and not previous

    def update_button_states(self):
        """Snapshot all button states for next-frame edge detection."""
        if not self.connected or not self.joystick:
            self._last_buttons = {}
            return
        try:
            for i in range(self.joystick.get_numbuttons()):
                self._last_buttons[i] = (self.joystick.get_button(i) == 1)
        except Exception:
            self._last_buttons = {}

    # ── Menu navigation helper ─────────────────────────────────────────────

    def get_menu_nav(self, dt):
        """
        Return menu navigation direction from the analog stick.
        -1 = up, +1 = down, 0 = neutral.
        Applies a cooldown so menus don't scroll too fast.
        """
        self._menu_nav_timer -= dt
        if self._menu_nav_timer > 0:
            return 0
        _, y = self.get_stick()
        if y > 0.5:
            self._menu_nav_timer = MENU_NAV_COOLDOWN
            return -1   # stick up  → selection moves up
        elif y < -0.5:
            self._menu_nav_timer = MENU_NAV_COOLDOWN
            return 1    # stick down → selection moves down
        return 0

    # ── Haptic feedback ────────────────────────────────────────────────────

    def rumble(self, low_frequency, high_frequency, duration_ms):
        """
        Trigger controller vibration (non-blocking).
        Intensities are 0.0–1.0.  Silently ignored if unsupported.
        """
        if not self.connected or not self.joystick:
            return
        try:
            self.joystick.rumble(low_frequency, high_frequency, duration_ms)
        except Exception:
            pass  # Not all controllers support rumble

    def rumble_meteor_destroy(self):
        """Short, light vibration — meteor destroyed by shooting."""
        lo, hi, ms = VIBRATION_METEOR_DESTROY
        self.rumble(lo, hi, ms)

    def rumble_player_death(self):
        """Longer, stronger vibration — player crash / death."""
        lo, hi, ms = VIBRATION_PLAYER_DEATH
        self.rumble(lo, hi, ms)

    # ── Cleanup ────────────────────────────────────────────────────────────

    def cleanup(self):
        """Release pygame joystick resources."""
        if self._initialized:
            try:
                pygame.joystick.quit()
            except Exception:
                pass


# =============================================================================
#  MAPPING DICTIONARY  (auto-generates help-menu content)
# =============================================================================

def get_controller_mappings():
    """Return an ordered dict of controller mappings for the help menu."""
    return [
        ("Left Stick", "Move ship (analog, smooth)"),
        ("RB (R1)", "Shoot"),
        ("B (B1)", "Pause Menu"),
        ("A", "Select / Confirm"),
        ("B", "Back / Cancel"),
    ]

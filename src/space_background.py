"""
Dynamic 3D Space Background Module  —  HIGH PERFORMANCE edition
================================================================
Uses **batched meshes**: each star layer is ONE Entity with ONE draw call,
so even thousands of stars cost almost nothing to render.

All layers are parented to ``camera`` — no world-space repositioning needed.
Parallax is achieved by tiny X/Y offsets based on the player's position.

Total entities: ~6   |   Total draw calls: ~6   |   Zero flicker.

Usage:
    from space_background import SpaceBackground
    bg = SpaceBackground()
    # In update loop:
    bg.update(player_position, player_velocity, dt)
"""

from ursina import *
from random import uniform, random
import math

# =============================================================================
#  CONFIGURATION
# =============================================================================

# Each layer: (star_count, z_depth, parallax_factor, size_min, size_max)
# parallax_factor multiplied by (player_pos * depth) gives the offset.
STAR_LAYERS = [
    (350, 950, 0.0004, 0.05, 0.18),  # Far — tiny pinpoints
    (200, 700, 0.0015, 0.08, 0.25),  # Mid — small dots
    (90, 400, 0.005, 0.10, 0.35),  # Near — still small but slightly brighter
]

STAR_FIELD_W = 500  # Horizontal spread
STAR_FIELD_H = 350  # Vertical spread

# Weighted star colour table  (colour, weight)
_STAR_PALETTE = [
    (Color(1.0, 1.0, 1.0, 1.0), 30),  # Pure white
    (Color(0.90, 0.93, 1.0, 1.0), 18),  # Cool white
    (Color(1.0, 0.96, 0.88, 1.0), 10),  # Warm white
    (Color(0.55, 0.75, 1.0, 1.0), 12),  # Soft blue
    (Color(0.40, 0.60, 1.0, 1.0), 8),  # Vivid blue
    (Color(0.30, 0.85, 1.0, 1.0), 6),  # Cyan / teal
    (Color(0.70, 0.50, 1.0, 1.0), 5),  # Purple
    (Color(1.0, 0.55, 0.70, 1.0), 4),  # Pink
    (Color(1.0, 0.80, 0.40, 1.0), 4),  # Gold / amber
    (Color(0.45, 1.0, 0.65, 1.0), 3),  # Green nebula glow
]
_PALETTE_TOTAL = sum(w for _, w in _STAR_PALETTE)

# Nebula settings
NEBULA_COUNT = 3
NEBULA_DEPTH = 985
NEBULA_ALPHA = 0.06
NEBULA_SCALE_RANGE = (120, 260)
# Parallax lerp speed — lower = smoother but slower response
PARALLAX_LERP_SPEED = 1.5
NEBULA_ROTATE_SPEED = 0.7  # degrees / second
NEBULA_COLORS = [
    Color(0.15, 0.05, 0.35, 1.0),  # Purple
    Color(0.05, 0.12, 0.35, 1.0),  # Blue
    Color(0.25, 0.03, 0.10, 1.0),  # Crimson
]


# =============================================================================
#  HELPERS
# =============================================================================


def _pick_color():
    """Weighted random star colour."""
    r = random() * _PALETTE_TOTAL
    acc = 0
    for clr, w in _STAR_PALETTE:
        acc += w
        if r <= acc:
            return clr
    return _STAR_PALETTE[0][0]


def _build_star_mesh(count, width, height, smin, smax):
    """
    Return a single Mesh containing *count* tiny quads.

    Every star = 4 vertices + 2 triangles, all baked into one mesh.
    Result: hundreds of stars → **one** draw call.
    """
    verts = []
    tris = []
    cols = []

    for i in range(count):
        cx = uniform(-width / 2, width / 2)
        cy = uniform(-height / 2, height / 2)
        # Each star gets a unique Z offset to prevent z-fighting flicker
        cz = uniform(-30, 30)
        s = uniform(smin, smax)
        brightness = uniform(0.55, 1.0)
        c = _pick_color()
        c = Color(c.r * brightness, c.g * brightness, c.b * brightness, brightness)

        b = i * 4
        verts += [
            Vec3(cx - s, cy - s, cz),
            Vec3(cx + s, cy - s, cz),
            Vec3(cx + s, cy + s, cz),
            Vec3(cx - s, cy + s, cz),
        ]
        cols += [c, c, c, c]
        tris += [(b, b + 1, b + 2), (b, b + 2, b + 3)]

    return Mesh(vertices=verts, triangles=tris, colors=cols, mode="triangle")


# =============================================================================
#  SPACE BACKGROUND CLASS
# =============================================================================


class SpaceBackground:
    """
    High-performance 3D space background.

    • 3 batched-mesh star layers (1 draw call each)
    • 3 nebula quads (1 draw call each)
    • All parented to camera — no per-frame world repositioning
    • Parallax via tiny X/Y offsets = smooth, jitter-free
    """

    def __init__(self):
        self._layers = []  # [(Entity, parallax_factor, current_x, current_y), ...]
        self._nebulas = []  # [(Entity, rot_speed), ...]

        self._build_star_layers()
        self._build_nebulas()

    # ── build ──────────────────────────────────────────────────────

    def _build_star_layers(self):
        for count, depth, pf, smin, smax in STAR_LAYERS:
            mesh = _build_star_mesh(count, STAR_FIELD_W, STAR_FIELD_H, smin, smax)
            ent = Entity(
                parent=camera,
                model=mesh,
                position=(0, 0, depth),
                unlit=True,
                color=color.white,
            )
            ent.collider = None
            self._layers.append([ent, pf, 0.0, 0.0])  # [entity, parallax, cur_x, cur_y]

    def _build_nebulas(self):
        for i in range(NEBULA_COUNT):
            nc = NEBULA_COLORS[i % len(NEBULA_COLORS)]
            sc = uniform(*NEBULA_SCALE_RANGE)
            ent = Entity(
                parent=camera,
                model="quad",
                color=Color(nc.r, nc.g, nc.b, NEBULA_ALPHA),
                scale=(sc, sc * uniform(0.4, 0.7)),
                position=(uniform(-70, 70), uniform(-40, 40), NEBULA_DEPTH + i * 8),
                rotation_z=uniform(0, 360),
                unlit=True,
            )
            ent.collider = None
            rot_dir = 1.0 if i % 2 == 0 else -1.0
            self._nebulas.append((ent, NEBULA_ROTATE_SPEED * rot_dir))

    # ── per-frame update (very cheap) ──────────────────────────────

    def update(self, player_pos, player_velocity, dt):
        """
        Smoothly lerp star layers toward parallax target positions.
        Lerping prevents the sub-pixel jitter that direct assignment caused.
        """
        if dt <= 0:
            return

        px = getattr(player_pos, "x", 0)
        py = getattr(player_pos, "y", 0)
        t = min(PARALLAX_LERP_SPEED * dt, 1.0)  # Lerp factor, capped at 1

        for layer in self._layers:
            ent, pf, cur_x, cur_y = layer
            # Target offset: small shift opposite to player position
            target_x = -px * pf * ent.z
            target_y = -py * pf * ent.z
            # Smooth interpolation toward target (no sudden jumps)
            new_x = cur_x + (target_x - cur_x) * t
            new_y = cur_y + (target_y - cur_y) * t
            ent.x = new_x
            ent.y = new_y
            layer[2] = new_x
            layer[3] = new_y

        for ent, rs in self._nebulas:
            ent.rotation_z += rs * dt

    # ── visibility / cleanup ───────────────────────────────────────

    def set_visible(self, visible):
        for layer in self._layers:
            layer[0].enabled = visible
        for ent, _ in self._nebulas:
            ent.enabled = visible

    def destroy(self):
        for layer in self._layers:
            try:
                destroy(layer[0])
            except Exception:
                pass
        for ent, _ in self._nebulas:
            try:
                destroy(ent)
            except Exception:
                pass
        self._layers.clear()
        self._nebulas.clear()

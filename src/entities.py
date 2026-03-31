"""
ORBIT RUSH — Game Entities
Player, Obstacle, EnergyOrb, and Projectile classes.

Entity subclasses intentionally avoid defining update() to prevent
Ursina's auto-update from calling into destroyed NodePaths (segfault on Linux).
Instead, tick() is called manually from the main game loop.
"""

from ursina import Entity, Vec3, destroy, color, Color, time
from random import uniform, choice

from src.config import (
    PLAYER_MODEL,
    PLAYER_TEXTURE,
    PLAYER_SCALE,
    PLAYER_SPEED,
    BASE_FORWARD_SPEED,
    METEORITE_MODELS,
    OBSTACLE_SCALE_MIN,
    OBSTACLE_SCALE_MAX,
    BOUNDARY_X,
    BOUNDARY_Y,
    ORB_SCALE,
    ORB_COLLISION_DIST,
    PROJECTILE_SPEED,
    PROJECTILE_RANGE,
)
from src.logger import log


# ─────────────────────────────────────────────────────────────────────────────
#  PLAYER
# ─────────────────────────────────────────────────────────────────────────────

class Player(Entity):
    """The player's spaceship."""

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


# ─────────────────────────────────────────────────────────────────────────────
#  OBSTACLE
# ─────────────────────────────────────────────────────────────────────────────

class Obstacle(Entity):
    """A meteorite obstacle that the player must avoid."""

    def __init__(self, player_z: float, **kwargs):
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
                player_z + uniform(50, 80),
            ),
            **kwargs,
        )

    def tick(self, player_z: float) -> bool:
        """Return True when this entity should be removed."""
        if self._dead:
            return True
        try:
            if self.z < player_z - 5:
                self._dead = True
                destroy(self)
                return True
        except Exception:
            self._dead = True
            return True
        return False


# ─────────────────────────────────────────────────────────────────────────────
#  ENERGY ORB
# ─────────────────────────────────────────────────────────────────────────────

ORB_COLORS = {
    "power": color.lime,
    "speed_up": Color(128 / 255, 0, 1.0, 1.0),
    "slow_down": color.azure,
    "shooter": color.red,
    "drain": Color(1.0, 100 / 255, 0, 1.0),
}


class EnergyOrb(Entity):
    """Collectible orb with various effects."""

    def __init__(self, orb_type: str = "power", player_z: float = 0, **kwargs):
        self.orb_type = orb_type
        self._dead = False
        orb_color = ORB_COLORS.get(orb_type, color.lime)
        if "position" not in kwargs:
            kwargs["position"] = (
                uniform(-BOUNDARY_X, BOUNDARY_X),
                uniform(-BOUNDARY_Y, BOUNDARY_Y),
                player_z + uniform(50, 80),
            )
        super().__init__(model="sphere", color=orb_color, scale=ORB_SCALE, **kwargs)

    def tick(self, player_z: float) -> bool:
        """Return True when this entity should be removed."""
        if self._dead:
            return True
        try:
            if self.z < player_z - 20:
                self._dead = True
                destroy(self)
                return True
        except Exception:
            self._dead = True
            return True
        return False


# ─────────────────────────────────────────────────────────────────────────────
#  PROJECTILE
# ─────────────────────────────────────────────────────────────────────────────

class Projectile(Entity):
    """A shot fired by the player during shooter mode."""

    def __init__(self, player_pos: Vec3, player_rot, **kwargs):
        super().__init__(
            model="cube",
            color=color.orange,
            scale=(0.1, 0.1, 0.6),
            position=player_pos + Vec3(0, 0, 1.5),
            rotation=player_rot,
            **kwargs,
        )
        self.speed = PROJECTILE_SPEED
        self._dead = False
        log("GAME", "Projectile fired", {"pos": str(self.position)})

    def tick(self, player_z: float, obstacles: list, shatter_fn) -> bool:
        """Return True when this entity should be removed."""
        if self._dead:
            return True
        try:
            self.z += self.speed * time.dt
            if self.z > player_z + PROJECTILE_RANGE:
                self._dead = True
                destroy(self)
                return True
            for obstacle in obstacles[:]:
                if obstacle._dead:
                    continue
                dist = (self.position - obstacle.position).length()
                if dist < (obstacle.collision_radius + 0.2):
                    shatter_fn(obstacle)
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


# ─────────────────────────────────────────────────────────────────────────────
#  COLLISION HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def check_collision(player: Entity, obstacle: Obstacle) -> bool:
    """Player–obstacle collision check (safe against destroyed entities)."""
    if obstacle._dead:
        return False
    try:
        return (player.position - obstacle.position).length() < (
            obstacle.collision_radius + 0.3
        )
    except Exception:
        return False


def check_orb_collision(player: Entity, orb: EnergyOrb) -> bool:
    """Player–orb collision check."""
    if orb._dead:
        return False
    try:
        return (player.position - orb.position).length() < ORB_COLLISION_DIST
    except Exception:
        return False

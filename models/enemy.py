import math
from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class Enemy:
    id: int
    enemy_type: str
    hp: int
    max_hp: int
    base_speed: float
    reward: int
    waypoints_px: List[Tuple[float, float]]
    x: float = 0.0
    y: float = 0.0
    current_wp_index: int = 0
    distance_traveled: float = 0.0
    alive: bool = True
    reached_base: bool = False
    reward_claimed: bool = False

    def __post_init__(self) -> None:
        if self.waypoints_px:
            self.x, self.y = self.waypoints_px[0]
            self.current_wp_index = 1

    def update(self, dt: float) -> None:
        if not self.alive or self.reached_base or dt <= 0.0:
            return

        remaining_move = self.base_speed * dt
        while remaining_move > 0.0 and self.current_wp_index < len(self.waypoints_px):
            tx, ty = self.waypoints_px[self.current_wp_index]
            dx = tx - self.x
            dy = ty - self.y
            dist = math.hypot(dx, dy)

            if dist <= remaining_move:
                self.x = tx
                self.y = ty
                self.distance_traveled += dist
                remaining_move -= dist
                self.current_wp_index += 1
            else:
                ratio = remaining_move / dist
                self.x += dx * ratio
                self.y += dy * ratio
                self.distance_traveled += remaining_move
                remaining_move = 0.0

        if self.current_wp_index >= len(self.waypoints_px):
            self.reached_base = True
            self.alive = False

    def take_damage(self, amount: int) -> bool:
        """Returnează True doar în momentul exact în care inamicul este eliminat prima dată."""
        if not self.alive:
            return False
        self.hp -= amount
        if self.hp <= 0:
            self.hp = 0
            self.alive = False
            return True
        return False

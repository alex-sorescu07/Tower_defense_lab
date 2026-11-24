import math
from dataclasses import dataclass
from typing import List, Optional
from models.enemy import Enemy


@dataclass
class Tower:
    id: int
    tower_type: str
    name: str
    behavior: str  # "direct" sau "sniper"
    col: int
    row: int
    x: float
    y: float
    cost: int
    range_px: float
    damage: int
    cooldown: float
    aim_delay: float
    upgrade_cost: int
    upgrade_bonus_damage: int
    upgrade_bonus_range: float
    upgraded: bool = False
    cooldown_timer: float = 0.0

    def update_cooldown(self, dt: float) -> None:
        if dt <= 0.0:
            return
        if self.cooldown_timer > 0.0:
            self.cooldown_timer = max(0.0, self.cooldown_timer - dt)

    def can_fire(self) -> bool:
        return self.cooldown_timer <= 0.0

    def select_target(self, enemies: List[Enemy]) -> Optional[Enemy]:
        """Selectează inamicul cel mai avansat în rază; departajare deterministă prin ID."""
        in_range: List[Enemy] = []
        for enemy in enemies:
            if not enemy.alive or enemy.reached_base:
                continue
            dist = math.hypot(enemy.x - self.x, enemy.y - self.y)
            if dist <= self.range_px:
                in_range.append(enemy)

        if not in_range:
            return None

        # Sortare după (-distance_traveled, id) -> cel mai avansat primul, apoi ID minim
        in_range.sort(key=lambda e: (-e.distance_traveled, e.id))
        return in_range[0]

    def apply_upgrade(self) -> bool:
        if self.upgraded:
            return False
        self.upgraded = True
        self.damage += self.upgrade_bonus_damage
        self.range_px += self.upgrade_bonus_range
        return True

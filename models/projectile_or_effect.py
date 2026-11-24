from dataclasses import dataclass
from models.enemy import Enemy
from services.economy import EconomyService


@dataclass
class SniperStrikeEffect:
    """
    Reprezintă un atac de tip Sniper / Direct:
    - Are o fază scurtă de achiziție/lock-on (aim_timer)
    - Aplică damage masiv instantaneu o singură dată (damage_applied)
    - Rămâne vizibil pe ecran pentru un scurt efect de urmă laser (visual_ttl)
    """
    source_x: float
    source_y: float
    target: Enemy
    damage: int
    aim_timer: float = 0.12
    visual_ttl: float = 0.15
    is_sniper: bool = True
    damage_applied: bool = False
    active: bool = True
    last_target_x: float = 0.0
    last_target_y: float = 0.0

    def __post_init__(self) -> None:
        self.last_target_x = self.target.x
        self.last_target_y = self.target.y

    def update(self, dt: float, economy: EconomyService) -> None:
        if not self.active or dt <= 0.0:
            return

        if self.target.alive and not self.target.reached_base:
            self.last_target_x = self.target.x
            self.last_target_y = self.target.y

        # Faza de lock-on înainte de descărcarea loviturii
        if not self.damage_applied:
            # Dacă ținta a dispărut sau a murit deja din altă sursă, anulăm în siguranță
            if not self.target.alive or self.target.reached_base:
                self.damage_applied = True
                self.active = False
                return

            self.aim_timer -= dt
            if self.aim_timer <= 0.0:
                self._apply_strike(economy)
        else:
            self.visual_ttl -= dt
            if self.visual_ttl <= 0.0:
                self.active = False

    def _apply_strike(self, economy: EconomyService) -> None:
        self.damage_applied = True
        if self.target.alive and not self.target.reached_base:
            killed = self.target.take_damage(self.damage)
            if killed:
                economy.claim_enemy_reward(self.target)

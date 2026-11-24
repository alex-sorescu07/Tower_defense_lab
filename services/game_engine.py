from pathlib import Path
from typing import Any, Dict, List, Optional
from models.enemy import Enemy
from models.map_grid import MapGrid
from models.projectile_or_effect import SniperStrikeEffect
from models.tower import Tower
from services.config_loader import load_and_validate_config, save_game_result
from services.economy import EconomyService


class GameEngine:
    def __init__(self, config_path: str | Path, results_path: str | Path = "data/results.json") -> None:
        self.config_path = Path(config_path)
        self.results_path = Path(results_path)
        self.config: Dict[str, Any] = load_and_validate_config(self.config_path)
        self.reset_game()

    def reset_game(self) -> None:
        map_cfg = self.config["map"]
        self.map_grid = MapGrid(
            cols=map_cfg["cols"],
            rows=map_cfg["rows"],
            cell_size=map_cfg["cell_size"],
            base_hp=map_cfg["base_hp"],
            start_coins=map_cfg["start_coins"],
            waypoints=[tuple(wp) for wp in map_cfg["waypoints"]],
        )
        self.waypoints_px = [self.map_grid.grid_to_pixel(c, r) for c, r in self.map_grid.waypoints]
        self.economy = EconomyService(self.map_grid.start_coins)
        self.base_hp: int = self.map_grid.base_hp

        self.towers: List[Tower] = []
        self.enemies: List[Enemy] = []
        self.effects: List[SniperStrikeEffect] = []

        self.next_enemy_id: int = 1
        self.next_tower_id: int = 1

        self.current_wave_index: int = 0
        self.wave_timer: float = 0.0
        self.pending_spawns: List[Dict[str, Any]] = []

        self.state: str = "MENU"  # MENU, PLAYING, PAUSED, VICTORY, DEFEAT
        self.result_saved: bool = False
        self.status_message: str = "Selectează o celulă liberă pentru a construi."
        self._load_wave(0)

    def start_game(self) -> None:
        self.reset_game()
        self.state = "PLAYING"

    def toggle_pause(self) -> None:
        if self.state == "PLAYING":
            self.state = "PAUSED"
            self.status_message = "Joc în PAUZĂ (timpul simulat este oprit)."
        elif self.state == "PAUSED":
            self.state = "PLAYING"
            self.status_message = "Joc reluat."

    def _load_wave(self, wave_idx: int) -> None:
        waves = self.config["waves"]
        if 0 <= wave_idx < len(waves):
            self.current_wave_index = wave_idx
            self.wave_timer = 0.0
            self.pending_spawns = [dict(s) for s in waves[wave_idx]["spawns"]]

    def place_tower(self, col: int, row: int, tower_type: str) -> bool:
        if tower_type not in self.config["towers"]:
            self.status_message = "Tip de turn necunoscut!"
            return False
        if not self.map_grid.is_valid_tower_cell(col, row):
            self.status_message = "Poziție invalidă (pe traseu, în afara hărții sau ocupată)!"
            return False

        t_cfg = self.config["towers"][tower_type]
        if not self.economy.spend(t_cfg["cost"]):
            self.status_message = "Fonduri insuficiente pentru construcție!"
            return False

        px, py = self.map_grid.grid_to_pixel(col, row)
        tower = Tower(
            id=self.next_tower_id,
            tower_type=tower_type,
            name=t_cfg["name"],
            behavior=t_cfg["behavior"],
            col=col,
            row=row,
            x=px,
            y=py,
            cost=t_cfg["cost"],
            range_px=float(t_cfg["range"]),
            damage=int(t_cfg["damage"]),
            cooldown=float(t_cfg["cooldown"]),
            aim_delay=float(t_cfg.get("aim_delay", 0.0)),
            upgrade_cost=int(t_cfg["upgrade_cost"]),
            upgrade_bonus_damage=int(t_cfg["upgrade_bonus_damage"]),
            upgrade_bonus_range=float(t_cfg["upgrade_bonus_range"]),
        )
        self.next_tower_id += 1
        self.towers.append(tower)
        self.map_grid.occupied_towers.add((col, row))
        self.status_message = f"{tower.name} construit la ({col}, {row})."
        return True

    def get_tower_at(self, col: int, row: int) -> Optional[Tower]:
        for t in self.towers:
            if t.col == col and t.row == row:
                return t
        return None

    def upgrade_tower_at(self, col: int, row: int) -> bool:
        tower = self.get_tower_at(col, row)
        if not tower:
            self.status_message = "Nu există niciun turn pe această celulă!"
            return False
        if tower.upgraded:
            self.status_message = "Turnul are deja unicul upgrade permis!"
            return False
        if not self.economy.upgrade_tower(tower):
            self.status_message = "Monede insuficiente pentru upgrade!"
            return False
        self.status_message = f"{tower.name} a fost îmbunătățit (Nivel MAX)!"
        return True

    def spawn_enemy(self, enemy_type: str) -> Enemy:
        e_cfg = self.config["enemies"][enemy_type]
        enemy = Enemy(
            id=self.next_enemy_id,
            enemy_type=enemy_type,
            hp=int(e_cfg["hp"]),
            max_hp=int(e_cfg["hp"]),
            base_speed=float(e_cfg["base_speed"]),
            reward=int(e_cfg["reward"]),
            waypoints_px=self.waypoints_px,
        )
        self.next_enemy_id += 1
        self.enemies.append(enemy)
        return enemy

    def update(self, dt: float) -> None:
        if self.state != "PLAYING" or dt <= 0.0:
            return

        # 1. Generare inamici din valul curent
        self.wave_timer += dt
        remaining_spawns = []
        for s in self.pending_spawns:
            if self.wave_timer >= float(s["spawn_time"]):
                self.spawn_enemy(s["type"])
            else:
                remaining_spawns.append(s)
        self.pending_spawns = remaining_spawns

        # 2. Deplasare inamici
        for enemy in self.enemies:
            if enemy.alive:
                enemy.update(dt)
                if enemy.reached_base:
                    self.base_hp = max(0, self.base_hp - 1)

        # Verificare înfrângere
        if self.base_hp <= 0:
            self.state = "DEFEAT"
            self._persist_result_once()
            return

        # 3. Actualizare turnuri și achiziție țintă
        for tower in self.towers:
            tower.update_cooldown(dt)
            if tower.can_fire():
                target = tower.select_target(self.enemies)
                if target is not None:
                    tower.cooldown_timer = tower.cooldown
                    is_sniper = tower.behavior == "sniper"
                    effect = SniperStrikeEffect(
                        source_x=tower.x,
                        source_y=tower.y,
                        target=target,
                        damage=tower.damage,
                        aim_timer=tower.aim_delay,
                        visual_ttl=0.22 if is_sniper else 0.08,
                        is_sniper=is_sniper,
                    )
                    # Dacă aim_delay este 0 (turn direct), lovește imediat în acest cadru
                    if tower.aim_delay <= 0.0:
                        effect.update(0.001, self.economy)
                    self.effects.append(effect)

        # 4. Actualizare efecte Sniper / lovituri
        for eff in self.effects:
            eff.update(dt, self.economy)
        self.effects = [eff for eff in self.effects if eff.active]

        # 5. Curățare inamici inactivi și tranziție valuri
        self.enemies = [e for e in self.enemies if e.alive]

        if not self.pending_spawns and not self.enemies and not self.effects:
            if self.current_wave_index + 1 < len(self.config["waves"]):
                self._load_wave(self.current_wave_index + 1)
                self.status_message = f"Valul {self.current_wave_index + 1} a început!"
            else:
                self.state = "VICTORY"
                self._persist_result_once()

    def _persist_result_once(self) -> None:
        if not self.result_saved:
            self.result_saved = True
            save_game_result(
                self.results_path,
                status=self.state,
                wave_reached=self.current_wave_index + 1,
                kills=self.economy.kills,
                coins_spent=self.economy.coins_spent,
            )

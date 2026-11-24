from typing import Optional, Tuple
import pygame
from services.game_engine import GameEngine


class GameRenderer:
    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.font_sm = pygame.font.SysFont("consolas", 15)
        self.font_md = pygame.font.SysFont("consolas", 18, bold=True)

    def draw_world(
        self,
        engine: GameEngine,
        selected_cell: Optional[Tuple[int, int]],
    ) -> None:
        grid = engine.map_grid
        cs = grid.cell_size

        # 1. Desenare celule și traseu
        for r in range(grid.rows):
            for c in range(grid.cols):
                rect = pygame.Rect(c * cs, r * cs, cs, cs)
                if (c, r) in grid.path_cells:
                    pygame.draw.rect(self.screen, (75, 70, 65), rect)
                else:
                    pygame.draw.rect(self.screen, (34, 45, 38), rect)
                pygame.draw.rect(self.screen, (25, 32, 28), rect, 1)

        # Marcaj Start și Bază
        start_c, start_r = grid.waypoints[0]
        end_c, end_r = grid.waypoints[-1]
        pygame.draw.rect(self.screen, (60, 140, 200), (start_c * cs + 8, start_r * cs + 8, cs - 16, cs - 16), border_radius=6)
        pygame.draw.rect(self.screen, (200, 60, 60), (end_c * cs + 8, end_r * cs + 8, cs - 16, cs - 16), border_radius=6)

        # 2. Evidențiere celulă selectată + rază turn (Nice-to-Have)
        if selected_cell is not None:
            sc, sr = selected_cell
            if 0 <= sc < grid.cols and 0 <= sr < grid.rows:
                sel_rect = pygame.Rect(sc * cs, sr * cs, cs, cs)
                pygame.draw.rect(self.screen, (240, 220, 90), sel_rect, 2)
                tower = engine.get_tower_at(sc, sr)
                if tower is not None:
                    pygame.draw.circle(
                        self.screen,
                        (240, 220, 90),
                        (int(tower.x), int(tower.y)),
                        int(tower.range_px),
                        1,
                    )

        # 3. Desenare turnuri
        for tower in engine.towers:
            center = (int(tower.x), int(tower.y))
            color = (70, 170, 255) if tower.behavior == "direct" else (235, 110, 50)
            pygame.draw.circle(self.screen, color, center, cs // 3)
            pygame.draw.circle(self.screen, (20, 20, 20), center, cs // 3, 2)

            # Țeavă / simbol Sniper vs Direct
            if tower.behavior == "sniper":
                pygame.draw.circle(self.screen, (255, 240, 200), center, 6)
            if tower.upgraded:
                upg_txt = self.font_sm.render("★MAX", True, (255, 230, 60))
                self.screen.blit(upg_txt, (tower.x - 18, tower.y - cs // 2 + 2))

        # 4. Desenare inamici + bară HP
        for enemy in engine.enemies:
            ex, ey = int(enemy.x), int(enemy.y)
            e_color = (220, 200, 70) if enemy.enemy_type == "scout" else (190, 70, 210)
            radius = 13 if enemy.enemy_type == "scout" else 18
            pygame.draw.circle(self.screen, e_color, (ex, ey), radius)
            pygame.draw.circle(self.screen, (15, 15, 15), (ex, ey), radius, 2)

            # Bară de viață
            bar_w = 32
            bar_h = 5
            hp_ratio = max(0.0, enemy.hp / enemy.max_hp)
            pygame.draw.rect(self.screen, (120, 30, 30), (ex - bar_w // 2, ey - radius - 9, bar_w, bar_h))
            pygame.draw.rect(self.screen, (60, 220, 80), (ex - bar_w // 2, ey - radius - 9, int(bar_w * hp_ratio), bar_h))

        # 5. Desenare efecte Sniper Lock-On & High-Damage Beam
        for eff in engine.effects:
            start_pos = (int(eff.source_x), int(eff.source_y))
            end_pos = (int(eff.last_target_x), int(eff.last_target_y))
            if not eff.damage_applied:
                # Faza de Lock-on: laser roșu subțire + reticul pe țintă
                pygame.draw.line(self.screen, (255, 60, 60), start_pos, end_pos, 1)
                pygame.draw.circle(self.screen, (255, 60, 60), end_pos, 16, 2)
            else:
                # Faza de Impact: fascicul luminos intens pentru Sniper, albastru scurt pentru Direct
                if eff.is_sniper:
                    pygame.draw.line(self.screen, (255, 140, 50), start_pos, end_pos, 6)
                    pygame.draw.line(self.screen, (255, 255, 220), start_pos, end_pos, 2)
                    pygame.draw.circle(self.screen, (255, 200, 90), end_pos, 14)
                else:
                    pygame.draw.line(self.screen, (100, 220, 255), start_pos, end_pos, 3)

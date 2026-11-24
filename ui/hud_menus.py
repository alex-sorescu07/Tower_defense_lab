from typing import Optional, Tuple
import pygame
from services.game_engine import GameEngine

class HudAndMenus:
    def __init__(self, screen: pygame.Surface, width: int, height: int, hud_height: int) -> None:
        self.screen = screen
        self.width = width
        self.height = height
        self.hud_height = hud_height
        self.font_sm = pygame.font.SysFont("consolas", 15)
        self.font_md = pygame.font.SysFont("consolas", 18, bold=True)
        self.font_lg = pygame.font.SysFont("consolas", 34, bold=True)

    def draw_hud(
        self,
        engine: GameEngine,
        selected_tower_type: str,
        selected_cell: Optional[Tuple[int, int]],
    ) -> None:
        hud_top = self.height - self.hud_height
        pygame.draw.rect(self.screen, (22, 25, 32), (0, hud_top, self.width, self.hud_height))
        pygame.draw.line(self.screen, (90, 100, 120), (0, hud_top), (self.width, hud_top), 2)

        total_waves = len(engine.config["waves"])
        stats_line = (
            f"Viață Bază: {engine.base_hp}   |   "
            f"Monede: {engine.economy.coins}   |   "
            f"Val: {engine.current_wave_index + 1}/{total_waves}   |   "
            f"Eliminări: {engine.economy.kills}"
        )
        self.screen.blit(self.font_md.render(stats_line, True, (240, 240, 240)), (16, hud_top + 10))

        rapid_cfg = engine.config["towers"]["rapid"]
        sniper_cfg = engine.config["towers"]["sniper"]
        controls_line = (
            f"[1] Pulse ({rapid_cfg['cost']}c)  "
            f"[2] Sniper ({sniper_cfg['cost']}c)  "
            f"[Click Stânga] Select/Plasează ({selected_tower_type.upper()})  "
            f"[U] Upgrade  [P] Pauză  [R] Restart"
        )
        self.screen.blit(self.font_sm.render(controls_line, True, (180, 210, 250)), (16, hud_top + 40))

        # Informații despre turnul selectat sau mesaj de stare
        info_text = engine.status_message
        if selected_cell is not None:
            tower = engine.get_tower_at(*selected_cell)
            if tower is not None:
                upg_state = "MAXIM" if tower.upgraded else f"Disponibil ({tower.upgrade_cost}c -> Apasă U)"
                info_text = (
                    f"Selectat: {tower.name} | DMG: {tower.damage} | Rază: {int(tower.range_px)} | "
                    f"Cooldown: {tower.cooldown}s | Upgrade: {upg_state}"
                )
        self.screen.blit(self.font_sm.render(info_text, True, (255, 220, 110)), (16, hud_top + 68))

    def draw_overlay(self, engine: GameEngine) -> None:
        if engine.state == "PLAYING":
            return

        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((10, 12, 18, 200))
        self.screen.blit(overlay, (0, 0))

        cx, cy = self.width // 2, self.height // 2
        if engine.state == "MENU":
            title = self.font_lg.render("TOWER DEFENSE LAB - 05A (SNIPER EDITION)", True, (255, 215, 80))
            sub = self.font_md.render("Apasă [ENTER] sau [SPACE] pentru a începe partida", True, (230, 230, 230))
            self.screen.blit(title, title.get_rect(center=(cx, cy - 30)))
            self.screen.blit(sub, sub.get_rect(center=(cx, cy + 20)))

        elif engine.state == "PAUSED":
            title = self.font_lg.render("PAUZĂ (TIMP SIMULAT OPRIT)", True, (120, 210, 255))
            sub = self.font_md.render("Apasă [P] pentru a continua sau [R] pentru Restart", True, (230, 230, 230))
            self.screen.blit(title, title.get_rect(center=(cx, cy - 20)))
            self.screen.blit(sub, sub.get_rect(center=(cx, cy + 25)))

        elif engine.state in ("VICTORY", "DEFEAT"):
            color = (90, 240, 120) if engine.state == "VICTORY" else (255, 90, 90)
            title_str = "VICTORIE! BAZA A FOST APĂRATĂ!" if engine.state == "VICTORY" else "ÎNFRÂNGERE! BAZA A CĂZUT!"
            title = self.font_lg.render(title_str, True, color)
            stats = self.font_md.render(
                f"Val atins: {engine.current_wave_index + 1} | Eliminări: {engine.economy.kills} | "
                f"Monede cheltuite: {engine.economy.coins_spent}",
                True,
                (240, 240, 240),
            )
            sub = self.font_sm.render(
                "Rezultatul a fost salvat în data/results.json. Apasă [R] pentru o nouă partidă.",
                True,
                (200, 200, 200),
            )
            self.screen.blit(title, title.get_rect(center=(cx, cy - 40)))
            self.screen.blit(stats, stats.get_rect(center=(cx, cy + 5)))
            self.screen.blit(sub, sub.get_rect(center=(cx, cy + 45)))

import sys
from typing import Optional, Tuple
import pygame
from services.config_loader import ConfigError
from services.game_engine import GameEngine
from ui.hud_menus import HudAndMenus
from ui.renderer import GameRenderer


def main() -> None:
    try:
        engine = GameEngine("data/config_level.json", "data/results.json")
    except ConfigError as exc:
        print(f"[EROARE CONFIGURARE]: {exc}")
        sys.exit(1)

    pygame.init()
    hud_height = 100
    map_w = engine.map_grid.cols * engine.map_grid.cell_size
    map_h = engine.map_grid.rows * engine.map_grid.cell_size
    screen = pygame.display.set_mode((map_w, map_h + hud_height))
    pygame.display.set_caption("Tower Defense Lab - Varianta 05A (Sniper)")

    clock = pygame.time.Clock()
    renderer = GameRenderer(screen)
    hud = HudAndMenus(screen, map_w, map_h + hud_height, hud_height)

    selected_tower_type = "sniper"
    selected_cell: Optional[Tuple[int, int]] = None

    running = True
    while running:
        raw_dt = clock.tick(60) / 1000.0
        # Dacă jocul este în pauză, pasul de timp simulat dt este 0.0
        dt = raw_dt if engine.state == "PLAYING" else 0.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if engine.state == "MENU" and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    engine.start_game()
                elif event.key == pygame.K_p:
                    engine.toggle_pause()
                elif event.key == pygame.K_r:
                    engine.start_game()
                elif event.key == pygame.K_1:
                    selected_tower_type = "rapid"
                    engine.status_message = "Selectat pentru construcție: Pulse Turret (Direct)."
                elif event.key == pygame.K_2:
                    selected_tower_type = "sniper"
                    engine.status_message = "Selectat pentru construcție: Railgun Sniper (High DMG)."
                elif event.key == pygame.K_u and selected_cell is not None and engine.state == "PLAYING":
                    engine.upgrade_tower_at(*selected_cell)

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if engine.state == "PLAYING":
                    mx, my = event.pos
                    if my < map_h:
                        col, row = engine.map_grid.pixel_to_grid(mx, my)
                        selected_cell = (col, row)
                        existing = engine.get_tower_at(col, row)
                        if existing is None:
                            engine.place_tower(col, row, selected_tower_type)

        engine.update(dt)

        renderer.draw_world(engine, selected_cell)
        hud.draw_hud(engine, selected_tower_type, selected_cell)
        hud.draw_overlay(engine)
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()

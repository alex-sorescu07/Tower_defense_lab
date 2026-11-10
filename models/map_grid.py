from dataclasses import dataclass, field
from typing import List, Set, Tuple


@dataclass
class MapGrid:
    cols: int
    rows: int
    cell_size: int
    base_hp: int
    start_coins: int
    waypoints: List[Tuple[int, int]]
    path_cells: Set[Tuple[int, int]] = field(init=False)
    occupied_towers: Set[Tuple[int, int]] = field(default_factory=set)

    def __post_init__(self) -> None:
        self.path_cells = self._compute_path_cells()

    def _compute_path_cells(self) -> Set[Tuple[int, int]]:
        cells: Set[Tuple[int, int]] = set()
        for i in range(len(self.waypoints) - 1):
            c1, r1 = self.waypoints[i]
            c2, r2 = self.waypoints[i + 1]
            if c1 == c2:
                step = 1 if r2 >= r1 else -1
                for r in range(r1, r2 + step, step):
                    cells.add((c1, r))
            elif r1 == r2:
                step = 1 if c2 >= c1 else -1
                for c in range(c1, c2 + step, step):
                    cells.add((c, r1))
        return cells

    def grid_to_pixel(self, col: int, row: int) -> Tuple[float, float]:
        return (
            col * self.cell_size + self.cell_size / 2.0,
            row * self.cell_size + self.cell_size / 2.0,
        )

    def pixel_to_grid(self, x: float, y: float) -> Tuple[int, int]:
        return int(x // self.cell_size), int(y // self.cell_size)

    def is_valid_tower_cell(self, col: int, row: int) -> bool:
        if not (0 <= col < self.cols and 0 <= row < self.rows):
            return False
        if (col, row) in self.path_cells:
            return False
        if (col, row) in self.occupied_towers:
            return False
        return True
import json
from pathlib import Path
from typing import Any, Dict

class ConfigError(Exception):
    """Excepție aruncată când fișierul JSON este corupt sau invalid."""


def load_and_validate_config(filepath: str | Path) -> Dict[str, Any]:
    path = Path(filepath)
    if not path.exists():
        raise ConfigError(f"Fișierul de configurare nu există: {path}")

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        raise ConfigError(f"JSON malformat în {path}: {exc}") from exc

    required_keys = {"map", "towers", "enemies", "waves"}
    if not isinstance(data, dict) or not required_keys.issubset(data.keys()):
        raise ConfigError("Lipsesc secțiuni obligatorii din JSON (map, towers, enemies, waves).")

    map_cfg = data["map"]
    for k in ("cols", "rows", "cell_size", "base_hp", "start_coins", "waypoints"):
        if k not in map_cfg:
            raise ConfigError(f"Lipsește cheia '{k}' din secțiunea 'map'.")

    if map_cfg["base_hp"] <= 0 or map_cfg["start_coins"] < 0:
        raise ConfigError("Valori invalide pentru base_hp sau start_coins.")

    if len(map_cfg["waypoints"]) < 2:
        raise ConfigError("Harta trebuie să conțină cel puțin 2 waypoints.")

    if len(data["towers"]) < 2:
        raise ConfigError("Configurația trebuie să conțină cel puțin 2 tipuri de turnuri.")

    if len(data["enemies"]) < 2:
        raise ConfigError("Configurația trebuie să conțină cel puțin 2 tipuri de inamici.")

    if len(data["waves"]) != 5:
        raise ConfigError("Configurația trebuie să conțină exact 5 valuri.")

    return data


def save_game_result(
    filepath: str | Path,
    status: str,
    wave_reached: int,
    kills: int,
    coins_spent: int,
) -> None:
    path = Path(filepath)
    results = []
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                if isinstance(loaded, list):
                    results = loaded
        except (json.JSONDecodeError, OSError):
            results = []

    results.append(
        {
            "status": status,
            "wave_reached": wave_reached,
            "kills": kills,
            "coins_spent": coins_spent,
        }
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

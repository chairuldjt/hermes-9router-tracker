import json
import subprocess
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise RuntimeError(
        "PyYAML is required for Hermes config installation flows. Install Hermes or 'pip install pyyaml'."
    ) from exc


def get_hermes_config_path(hermes_bin: str) -> Path:
    result = subprocess.run(
        [hermes_bin, "config", "path"],
        check=True,
        capture_output=True,
        text=True,
    )
    return Path(result.stdout.strip())


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        return {}
    return data


def dump_yaml(path: Path, data: dict[str, Any]) -> None:
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")


def ensure_dict(parent: dict[str, Any], key: str) -> dict[str, Any]:
    current = parent.get(key)
    if not isinstance(current, dict):
        current = {}
        parent[key] = current
    return current


def read_menu_commands(telegram_cfg: dict[str, Any]) -> dict[str, str]:
    raw = telegram_cfg.get("menu_commands", {})
    if isinstance(raw, dict):
        return {str(k): str(v) for k, v in raw.items()}
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                return {str(k): str(v) for k, v in parsed.items()}
        except Exception:
            return {}
    return {}


def write_menu_commands(telegram_cfg: dict[str, Any], menu: dict[str, str]) -> None:
    telegram_cfg["menu_commands"] = menu

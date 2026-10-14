"""Loads settings (routes, exchange rates, defaults) from a JSON file.

Keeping numbers in a config file means the business can change a rate or a
baggage fee without touching any Python code.
"""

import json
from dataclasses import dataclass
from pathlib import Path

from .models import Route


@dataclass(frozen=True)
class Settings:
    routes: dict[str, Route]
    rates_to_brl: dict[str, float]
    default_markup_percent: float
    default_import_tax_percent: float


def load_settings(path: str | Path) -> Settings:
    file = Path(path)
    if not file.exists():
        raise FileNotFoundError(
            f"Config file not found: {file}. "
            "Copy config/settings.example.json to config/settings.json first."
        )
    raw = json.loads(file.read_text(encoding="utf-8"))

    routes = {}
    for key, r in raw["routes"].items():
        routes[key] = Route(
            key=key,
            name=r["name"],
            trip_cost_usd=float(r["trip_cost_usd"]),
            capacity_kg=float(r["capacity_kg"]),
            onward_bag_fee_usd=float(r.get("onward_bag_fee_usd", 0)),
            onward_bag_kg=float(r.get("onward_bag_kg", 0)),
        )

    rates = {code.upper(): float(v) for code, v in raw["rates_to_brl"].items()}
    for code, value in rates.items():
        if value <= 0:
            raise ValueError(f"Exchange rate for {code} must be greater than zero")

    defaults = raw.get("defaults", {})
    return Settings(
        routes=routes,
        rates_to_brl=rates,
        default_markup_percent=float(defaults.get("markup_percent", 0)),
        default_import_tax_percent=float(defaults.get("import_tax_percent", 0)),
    )

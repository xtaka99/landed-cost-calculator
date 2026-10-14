"""Data models: plain containers that describe the inputs and outputs.

Using dataclasses keeps the data separate from the math (calculator.py)
and from the user interface (cli.py). Each file has one job.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Route:
    """A way of moving merchandise from where it is bought to Brazil.

    trip_cost_usd:    total cost of the sourcing trip (flights, hotel, etc.).
                      Use 0 for a home-base route where no trip is needed.
    capacity_kg:      how many kg of merchandise that trip can carry.
    onward_bag_fee_usd / onward_bag_kg:
                      cost and usable weight of one checked bag for the
                      final leg to Brazil. Use 0 / 0 if the route already
                      ends in Brazil.
    """

    key: str
    name: str
    trip_cost_usd: float
    capacity_kg: float
    onward_bag_fee_usd: float = 0.0
    onward_bag_kg: float = 0.0

    def freight_per_kg_usd(self) -> float:
        """Freight cost in USD for moving 1 kg over the whole route."""
        trip_part = self.trip_cost_usd / self.capacity_kg if self.capacity_kg else 0.0
        bag_part = (
            self.onward_bag_fee_usd / self.onward_bag_kg if self.onward_bag_kg else 0.0
        )
        return trip_part + bag_part


@dataclass(frozen=True)
class Commission:
    """Fee paid to a local buying partner.

    method "percent": value is a % of the merchandise cost (exact method).
    method "per_kg":  value is a flat BRL amount per kg (shortcut method).
    method "none":    no partner involved.
    """

    method: str = "none"
    value: float = 0.0

    def __post_init__(self) -> None:
        if self.method not in ("none", "percent", "per_kg"):
            raise ValueError(f"Unknown commission method: {self.method!r}")
        if self.value < 0:
            raise ValueError("Commission value cannot be negative")


@dataclass(frozen=True)
class Item:
    """One product being priced."""

    name: str
    cost: float          # purchase price in the currency it was bought in
    currency: str        # e.g. "USD", "JPY", "EUR"
    weight_kg: float     # weight of ONE unit, including packaging
    quantity: int = 1

    def __post_init__(self) -> None:
        if self.cost < 0:
            raise ValueError(f"{self.name}: cost cannot be negative")
        if self.weight_kg <= 0:
            raise ValueError(f"{self.name}: weight must be greater than zero")
        if self.quantity < 1:
            raise ValueError(f"{self.name}: quantity must be at least 1")


@dataclass(frozen=True)
class CostBreakdown:
    """Result of the calculation. All money values are in BRL, per unit."""

    item: Item
    merchandise_brl: float
    freight_brl: float
    commission_brl: float
    import_tax_brl: float
    landed_cost_brl: float
    sale_price_brl: float
    profit_brl: float

    @property
    def margin_percent(self) -> float:
        """Profit as a % of the sale price."""
        if self.sale_price_brl == 0:
            return 0.0
        return self.profit_brl / self.sale_price_brl * 100

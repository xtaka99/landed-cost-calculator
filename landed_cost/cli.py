"""Command-line interface. Reads arguments, calls the calculator, prints.

Three commands:
    routes  list the routes in the config with their freight per kg
    item    price a single item
    batch   price every item in a CSV file
"""

import argparse
import csv
import sys
from pathlib import Path

from .calculator import calculate
from .config import Settings, load_settings
from .models import Commission, CostBreakdown, Item

DEFAULT_CONFIG = "config/settings.json"
FALLBACK_CONFIG = "config/settings.example.json"


def brl(value: float) -> str:
    """Format a number the Brazilian way: R$ 1.234,56"""
    text = f"{value:,.2f}"                     # 1,234.56
    text = text.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {text}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="landed_cost",
        description="Landed cost and sale price calculator for imported goods.",
    )
    parser.add_argument("--config", help="path to settings JSON")
    sub = parser.add_subparsers(dest="command", required=True)

    # Options shared by the "item" and "batch" commands.
    shared = argparse.ArgumentParser(add_help=False)
    shared.add_argument("--route", required=True, help="route key from the config")
    shared.add_argument("--commission", choices=["none", "percent", "per_kg"],
                        default="none", help="partner commission method")
    shared.add_argument("--commission-value", type=float, default=0.0,
                        help="%% of merchandise, or BRL per kg")
    shared.add_argument("--markup", type=float, help="markup %% over landed cost")
    shared.add_argument("--import-tax", type=float, help="import tax %%")
    shared.add_argument("--exact-price", action="store_true",
                        help="do not round the sale price up to a ,90 ending")

    sub.add_parser("routes", help="list routes and their freight per kg")

    one = sub.add_parser("item", parents=[shared], help="price a single item")
    one.add_argument("--name", required=True)
    one.add_argument("--cost", type=float, required=True)
    one.add_argument("--currency", required=True)
    one.add_argument("--weight", type=float, required=True, help="kg per unit")
    one.add_argument("--qty", type=int, default=1)

    many = sub.add_parser("batch", parents=[shared], help="price a CSV of items")
    many.add_argument("csv_file", help="columns: name,cost,currency,weight_kg,quantity")
    many.add_argument("--out", help="also save the results to this CSV file")
    return parser


def read_items(csv_path: str) -> list[Item]:
    items = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        for line_no, row in enumerate(csv.DictReader(f), start=2):
            try:
                items.append(Item(
                    name=row["name"].strip(),
                    cost=float(row["cost"]),
                    currency=row["currency"].strip().upper(),
                    weight_kg=float(row["weight_kg"]),
                    quantity=int(row.get("quantity") or 1),
                ))
            except (KeyError, ValueError) as err:
                raise ValueError(f"{csv_path}, line {line_no}: {err}") from err
    return items


def print_single(b: CostBreakdown) -> None:
    print(f"\n{b.item.name}  ({b.item.cost:g} {b.item.currency}, {b.item.weight_kg:g} kg)")
    print("-" * 44)
    rows = [
        ("Merchandise", b.merchandise_brl),
        ("Freight", b.freight_brl),
        ("Commission", b.commission_brl),
        ("Import tax", b.import_tax_brl),
        ("LANDED COST", b.landed_cost_brl),
        ("Sale price", b.sale_price_brl),
        ("Profit per unit", b.profit_brl),
    ]
    for label, value in rows:
        print(f"{label:<18}{brl(value):>26}")
    print(f"{'Margin':<18}{b.margin_percent:>25.1f}%")
    if b.item.quantity > 1:
        total = b.profit_brl * b.item.quantity
        print(f"{'Profit x' + str(b.item.quantity):<18}{brl(total):>26}")


def print_table(results: list[CostBreakdown]) -> None:
    header = f"{'Item':<28}{'Qty':>4}{'Landed':>14}{'Sale':>14}{'Profit':>14}{'Margin':>8}"
    print("\n" + header)
    print("-" * len(header))
    total_profit = 0.0
    total_weight = 0.0
    for b in results:
        total_profit += b.profit_brl * b.item.quantity
        total_weight += b.item.weight_kg * b.item.quantity
        print(f"{b.item.name[:27]:<28}{b.item.quantity:>4}"
              f"{brl(b.landed_cost_brl):>14}{brl(b.sale_price_brl):>14}"
              f"{brl(b.profit_brl):>14}{b.margin_percent:>7.1f}%")
    print("-" * len(header))
    print(f"Total weight: {total_weight:.2f} kg    Total profit: {brl(total_profit)}")


def save_csv(results: list[CostBreakdown], path: str) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["name", "quantity", "merchandise_brl", "freight_brl",
                    "commission_brl", "import_tax_brl", "landed_cost_brl",
                    "sale_price_brl", "profit_brl", "margin_percent"])
        for b in results:
            w.writerow([b.item.name, b.item.quantity, b.merchandise_brl,
                        b.freight_brl, b.commission_brl, b.import_tax_brl,
                        b.landed_cost_brl, b.sale_price_brl, b.profit_brl,
                        round(b.margin_percent, 1)])


def pick_config(arg: str | None) -> str:
    """Use the private settings.json if it exists, else the public example."""
    if arg:
        return arg
    return DEFAULT_CONFIG if Path(DEFAULT_CONFIG).exists() else FALLBACK_CONFIG


def run(argv: list[str] | None = None) -> int:
    """Entry point. Returns an exit code (0 = success) so it can be tested."""
    args = build_parser().parse_args(argv)
    try:
        settings: Settings = load_settings(pick_config(args.config))

        if args.command == "routes":
            for route in settings.routes.values():
                print(f"{route.key:<28}{route.name:<36}"
                      f"US$ {route.freight_per_kg_usd():.2f}/kg")
            return 0

        if args.route not in settings.routes:
            known = ", ".join(settings.routes)
            print(f"Unknown route '{args.route}'. Available: {known}", file=sys.stderr)
            return 2

        options = dict(
            route=settings.routes[args.route],
            rates_to_brl=settings.rates_to_brl,
            commission=Commission(args.commission, args.commission_value),
            import_tax_percent=(args.import_tax if args.import_tax is not None
                                else settings.default_import_tax_percent),
            markup_percent=(args.markup if args.markup is not None
                            else settings.default_markup_percent),
            pretty_price=not args.exact_price,
        )

        if args.command == "item":
            item = Item(args.name, args.cost, args.currency.upper(), args.weight, args.qty)
            print_single(calculate(item, **options))
        else:
            results = [calculate(i, **options) for i in read_items(args.csv_file)]
            print_table(results)
            if args.out:
                save_csv(results, args.out)
                print(f"Saved: {args.out}")
        return 0

    except (FileNotFoundError, ValueError, KeyError) as err:
        # Show a clean message instead of a scary traceback.
        message = err.args[0] if err.args else str(err)
        print(f"Error: {message}", file=sys.stderr)
        return 1

"""The math. No printing and no file reading here, so it is easy to test.

Landed cost = what one unit really costs by the time it is sitting in the
Brazil warehouse:

    merchandise + freight + partner commission + import tax

Sale price is then built from the landed cost using a markup %.
"""

from .models import Commission, CostBreakdown, Item, Route


def to_brl(amount: float, currency: str, rates_to_brl: dict[str, float]) -> float:
    """Convert an amount in any supported currency to BRL.

    rates_to_brl maps a currency code to "how many BRL is 1 unit worth",
    e.g. {"USD": 5.40, "JPY": 0.036}. BRL itself is always 1.
    """
    code = currency.upper()
    if code == "BRL":
        return amount
    if code not in rates_to_brl:
        raise KeyError(
            f"No exchange rate for {code}. Add it under 'rates_to_brl' in the config."
        )
    return amount * rates_to_brl[code]


def round_up_to_ending(price: float, ending: float = 0.90) -> float:
    """Round a price UP to the next value ending in e.g. ,90 (retail style).

    127.13 -> 127.90      127.95 -> 128.90
    """
    if price <= 0:
        return 0.0
    whole = int(price)
    candidate = whole + ending
    if candidate < price:
        candidate += 1
    return round(candidate, 2)


def calculate(
    item: Item,
    route: Route,
    rates_to_brl: dict[str, float],
    commission: Commission = Commission(),
    import_tax_percent: float = 0.0,
    markup_percent: float = 0.0,
    pretty_price: bool = True,
) -> CostBreakdown:
    """Work out the full per-unit cost breakdown for one item on one route."""
    if import_tax_percent < 0 or markup_percent < 0:
        raise ValueError("Percentages cannot be negative")

    # 1. Merchandise: what was paid at the store, converted to BRL.
    merchandise = to_brl(item.cost, item.currency, rates_to_brl)

    # 2. Freight: the route's USD-per-kg rate times this item's weight.
    freight_usd = route.freight_per_kg_usd() * item.weight_kg
    freight = to_brl(freight_usd, "USD", rates_to_brl)

    # 3. Partner commission: exact (% of merchandise) or shortcut (BRL per kg).
    if commission.method == "percent":
        commission_brl = merchandise * commission.value / 100
    elif commission.method == "per_kg":
        commission_brl = commission.value * item.weight_kg
    else:
        commission_brl = 0.0

    # 4. Import tax, applied on merchandise + freight (the usual customs base).
    import_tax = (merchandise + freight) * import_tax_percent / 100

    landed = merchandise + freight + commission_brl + import_tax

    # 5. Sale price from markup, optionally rounded up to a ",90" ending.
    sale_price = landed * (1 + markup_percent / 100)
    if pretty_price:
        sale_price = round_up_to_ending(sale_price)

    return CostBreakdown(
        item=item,
        merchandise_brl=round(merchandise, 2),
        freight_brl=round(freight, 2),
        commission_brl=round(commission_brl, 2),
        import_tax_brl=round(import_tax, 2),
        landed_cost_brl=round(landed, 2),
        sale_price_brl=round(sale_price, 2),
        profit_brl=round(sale_price - landed, 2),
    )

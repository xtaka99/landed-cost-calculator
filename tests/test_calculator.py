"""Tests for the math. Run with:  pytest

Each test sets up known inputs, runs the code, and checks the answer that
was worked out by hand. If someone later breaks the math, a test fails.
"""

import pytest

from landed_cost.calculator import calculate, round_up_to_ending, to_brl
from landed_cost.models import Commission, Item, Route

RATES = {"USD": 5.00, "JPY": 0.04}

# 1000 USD trip / 100 kg = 10 USD/kg, plus 200 USD bag / 20 kg = 10 USD/kg
VIA_ORLANDO = Route("via", "Via Orlando", 1000, 100, 200, 20)
DIRECT = Route("direct", "Direct", 1000, 100)
HOME_BASE = Route("home", "Home base", 0, 0, 200, 20)


def test_freight_per_kg_combines_trip_and_bag():
    assert VIA_ORLANDO.freight_per_kg_usd() == 20
    assert DIRECT.freight_per_kg_usd() == 10
    assert HOME_BASE.freight_per_kg_usd() == 10   # no trip cost, only baggage


def test_to_brl_converts_and_passes_brl_through():
    assert to_brl(10, "USD", RATES) == 50
    assert to_brl(10, "usd", RATES) == 50          # lowercase is accepted
    assert to_brl(10, "BRL", RATES) == 10


def test_to_brl_unknown_currency_raises():
    with pytest.raises(KeyError):
        to_brl(10, "GBP", RATES)


def test_basic_landed_cost():
    item = Item("Mug", cost=20, currency="USD", weight_kg=0.5)
    b = calculate(item, DIRECT, RATES, pretty_price=False)
    assert b.merchandise_brl == 100       # 20 USD x 5
    assert b.freight_brl == 25            # 10 USD/kg x 0.5 kg x 5
    assert b.landed_cost_brl == 125


def test_percent_commission_uses_merchandise_value():
    item = Item("Plush", cost=2500, currency="JPY", weight_kg=1)
    b = calculate(item, DIRECT, RATES, Commission("percent", 15), pretty_price=False)
    assert b.merchandise_brl == 100
    assert b.commission_brl == 15


def test_per_kg_commission_uses_weight():
    item = Item("Plush", cost=2500, currency="JPY", weight_kg=0.5)
    b = calculate(item, DIRECT, RATES, Commission("per_kg", 80), pretty_price=False)
    assert b.commission_brl == 40


def test_import_tax_applies_to_merchandise_plus_freight():
    item = Item("Mug", cost=20, currency="USD", weight_kg=0.5)
    b = calculate(item, DIRECT, RATES, import_tax_percent=60, pretty_price=False)
    assert b.import_tax_brl == 75         # 60% of (100 + 25)
    assert b.landed_cost_brl == 200


def test_markup_profit_and_margin():
    item = Item("Mug", cost=20, currency="USD", weight_kg=0.5)
    b = calculate(item, DIRECT, RATES, markup_percent=100, pretty_price=False)
    assert b.sale_price_brl == 250
    assert b.profit_brl == 125
    assert b.margin_percent == 50


def test_pretty_price_rounds_up_never_down():
    assert round_up_to_ending(127.13) == 127.90
    assert round_up_to_ending(127.95) == 128.90
    assert round_up_to_ending(127.90) == 127.90
    assert round_up_to_ending(0) == 0


def test_invalid_inputs_are_rejected():
    with pytest.raises(ValueError):
        Item("Bad", cost=-1, currency="USD", weight_kg=1)
    with pytest.raises(ValueError):
        Item("Bad", cost=1, currency="USD", weight_kg=0)
    with pytest.raises(ValueError):
        Commission("weekly", 10)
    with pytest.raises(ValueError):
        calculate(Item("X", 1, "USD", 1), DIRECT, RATES, markup_percent=-5)

# landed-cost-calculator

![tests](https://github.com/xtaka99/landed-cost-calculator/actions/workflows/tests.yml/badge.svg)

Command-line tool that answers one question for an import/resale business:
**"What does this product really cost me once it is in Brazil, and what should I sell it for?"**

I help run a family business that buys merchandise in Orlando, Tokyo, Paris and
California and resells it in Brazil. The store price is only part of the cost.
Freight (priced per kg of luggage), a buying partner's commission, exchange
rates and import tax all change the real number. This tool puts them together.

## What it does

- Converts the purchase price from USD, JPY, EUR, CNY or HKD to BRL
- Works out **freight per kg for each route** from the trip cost, luggage capacity and onward baggage fees
- Supports two partner-commission methods: **% of merchandise** (exact) or **BRL per kg** (shortcut)
- Applies optional import tax and a markup, then rounds the sale price up to a retail-style `,90` ending
- Prices a single item or a **whole CSV shopping list**, with total weight and total profit
- Reads all business numbers from a JSON config, so nobody has to edit code to change a rate

## Example

```
$ python -m landed_cost item --route tokyo-brazil --name "Duffy plush" \
      --cost 4500 --currency JPY --weight 0.3 \
      --commission percent --commission-value 15 --qty 5

Duffy plush  (4500 JPY, 0.3 kg)
--------------------------------------------
Merchandise                        R$ 162,00
Freight                             R$ 64,80
Commission                          R$ 24,30
Import tax                           R$ 0,00
LANDED COST                        R$ 251,10
Sale price                         R$ 401,90
Profit per unit                    R$ 150,80
Margin                                 37.5%
Profit x5                          R$ 754,00
```

Batch mode:

```
$ python -m landed_cost batch examples/items.csv --route tokyo-orlando-brazil \
      --commission per_kg --commission-value 80 --out results.csv
```

List routes and their freight cost per kg:

```
$ python -m landed_cost routes
```

## Setup

Requires Python 3.10 or newer. The tool itself has **no dependencies**.

```bash
git clone https://github.com/xtaka99/landed-cost-calculator.git
cd landed-cost-calculator
python -m landed_cost routes
```

To use your own numbers, copy `config/settings.example.json` to
`config/settings.json` and edit it. That file is in `.gitignore`, so real
business figures never end up on GitHub. The numbers in the example file are
illustrative only.

## Running the tests

```bash
pip install -r requirements-dev.txt
pytest
```

Tests also run automatically on every push through GitHub Actions.

## How it works

| File | Job |
|---|---|
| `landed_cost/models.py` | Dataclasses for `Route`, `Item`, `Commission`, `CostBreakdown`, with input validation |
| `landed_cost/calculator.py` | The math only. No printing, no file access, so it is easy to test |
| `landed_cost/config.py` | Loads routes, exchange rates and defaults from JSON |
| `landed_cost/cli.py` | `argparse` interface, table output, BRL formatting, CSV export |
| `tests/` | 14 pytest tests with hand-calculated expected values |

The formula, per unit:

```
freight per kg = trip cost / trip capacity kg  +  onward bag fee / onward bag kg
landed cost    = merchandise + freight + commission + import tax
sale price     = landed cost x (1 + markup), rounded up to ,90
```

## What I learned

- Separating data, logic and interface so each part can be tested on its own
- Dataclasses and validation in `__post_init__`
- Building a multi-command CLI with `argparse`
- Writing pytest tests and running them in CI with GitHub Actions
- Keeping private data out of a public repo with `.gitignore` and example configs

## Possible next steps

- Pull live exchange rates from [cambio-alert-bot](https://github.com/xtaka99/cambio-alert-bot)
- Feed results into a luggage packing optimizer that picks the most profitable items per bag

## License

MIT

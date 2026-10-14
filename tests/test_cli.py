"""Tests that run the whole program the way a user would."""

from landed_cost.cli import brl, run

CONFIG = "config/settings.example.json"


def test_brl_formatting():
    assert brl(1234.5) == "R$ 1.234,50"
    assert brl(0.9) == "R$ 0,90"


def test_item_command_prints_breakdown(capsys):
    code = run(["--config", CONFIG, "item", "--route", "tokyo-brazil",
                "--name", "Test plush", "--cost", "2500", "--currency", "JPY",
                "--weight", "0.2"])
    out = capsys.readouterr().out
    assert code == 0
    assert "LANDED COST" in out
    assert "Test plush" in out


def test_batch_command_writes_csv(tmp_path, capsys):
    out_file = tmp_path / "result.csv"
    code = run(["--config", CONFIG, "batch", "examples/items.csv",
                "--route", "tokyo-orlando-brazil", "--out", str(out_file)])
    assert code == 0
    lines = out_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 6                 # header + 5 items


def test_unknown_route_returns_error_code(capsys):
    code = run(["--config", CONFIG, "item", "--route", "mars-brazil",
                "--name", "X", "--cost", "1", "--currency", "USD", "--weight", "1"])
    assert code == 2
    assert "Unknown route" in capsys.readouterr().err

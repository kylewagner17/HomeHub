from homehub.modules.groceries.estimate import estimate_total_cents
from homehub.modules.groceries.quantity import parse_quantity


def test_parse_quantity_defaults():
    assert parse_quantity("2.5") == 2.5
    assert parse_quantity("bad") == 1.0
    assert parse_quantity("0") == 1.0


def test_estimate_total_cents():
    items = [("Milk", "2"), ("Bread", "1")]
    prices = {"milk": 199, "bread": 350}
    total, missing = estimate_total_cents(items, prices)
    assert total == 199 * 2 + 350
    assert missing == []

    total2, missing2 = estimate_total_cents([("Eggs", "1")], prices)
    assert total2 == 0
    assert missing2 == []

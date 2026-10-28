"""Cart total from manual store prices (ADR-004)."""

from homehub.modules.groceries.quantity import parse_quantity


def estimate_total_cents(
    line_items: list[tuple[str, str]],
    price_by_item_name_lower: dict[str, int],
) -> tuple[int, list[str]]:
    """Sum all lines; missing prices count as zero (checked state does not affect total)."""
    total = 0
    for name, quantity in line_items:
        key = name.strip().lower()
        price = price_by_item_name_lower.get(key, 0)
        total += int(round(price * parse_quantity(quantity)))
    return total, []

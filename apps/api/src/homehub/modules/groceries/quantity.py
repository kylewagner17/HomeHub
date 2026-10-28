"""Quantity parsing and merge for grocery line items."""


def parse_quantity(raw: str) -> float:
    try:
        value = float(str(raw).strip())
    except ValueError:
        return 1.0
    return value if value > 0 else 1.0


def format_quantity(value: float) -> str:
    if abs(value - round(value)) < 1e-9:
        return str(int(round(value)))
    return f"{value:.2f}".rstrip("0").rstrip(".")


def add_quantities(left: str, right: str) -> str:
    return format_quantity(parse_quantity(left) + parse_quantity(right))


def adjust_quantity(raw: str, delta: float) -> str | None:
    """Return new quantity string, or None if result would be below 1."""
    next_value = parse_quantity(raw) + delta
    if next_value < 1:
        return None
    return format_quantity(next_value)

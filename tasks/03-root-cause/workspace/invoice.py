"""Invoice math for the shop. All amounts are in dollars."""

TAX_RATE = 0.08875


def line_total(price: float, qty: int) -> float:
    """Total for one line, rounded to the nearest cent."""
    return round(price * qty, 2)


def invoice_total(lines) -> float:
    """Subtotal of all (price, qty) lines plus sales tax, rounded to the nearest cent."""
    subtotal = sum(line_total(price, qty) for price, qty in lines)
    tax = round(subtotal * TAX_RATE, 2)
    return round(subtotal + tax, 2)

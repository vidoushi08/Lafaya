from decimal import ROUND_HALF_UP, Decimal

from .models import PricedCatalogItem

CENTS = Decimal("0.01")


def item_cost(item, guests):
    """Cost of one catalogue item for the given guest count.

    Items without a price are "Price on request" and add nothing to the total.
    """
    if item.price_basis == PricedCatalogItem.PriceBasis.PER_GUEST:
        quantity = guests
    else:
        quantity = 1
    if item.price is None:
        return None, quantity
    return (item.price * quantity).quantize(CENTS, rounding=ROUND_HALF_UP), quantity


def calculate_estimate(venue, package, services, guests):
    """Return the total and a snapshot of every line."""
    lines = []
    total = Decimal("0.00")
    for kind, item in (
        [("venue", venue), ("package", package)]
        + [("service", service) for service in services]
    ):
        subtotal, quantity = item_cost(item, guests)
        if subtotal is not None:
            total += subtotal
        lines.append(
            {
                "kind": kind,
                "name": item.name,
                "unit_price": str(item.price) if item.price is not None else None,
                "price_basis": item.price_basis,
                "quantity": quantity,
                "subtotal": str(subtotal) if subtotal is not None else None,
                "note": "" if item.price is not None else "Price on request",
            }
        )
    return total, lines

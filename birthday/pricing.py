from decimal import ROUND_HALF_UP, Decimal

from .models import PricedCatalogItem

CENTS = Decimal("0.01")


def item_cost(item, guests):
    quantity = (
        guests
        if item.price_basis == PricedCatalogItem.PriceBasis.PER_GUEST
        else 1
    )
    return (item.price * quantity).quantize(CENTS, rounding=ROUND_HALF_UP), quantity


def calculate_estimate(venue, package, services, guests):
    lines = []
    total = Decimal("0.00")
    for kind, item in (
        [("venue", venue), ("package", package)]
        + [("service", service) for service in services]
    ):
        subtotal, quantity = item_cost(item, guests)
        total += subtotal
        lines.append(
            {
                "kind": kind,
                "name": item.name,
                "unit_price": str(item.price),
                "price_basis": item.price_basis,
                "quantity": quantity,
                "subtotal": str(subtotal),
            }
        )
    return total, lines

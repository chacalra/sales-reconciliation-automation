from .models import Issue, Sale


def detect_duplicates(sales: list[Sale]) -> tuple[list[Sale], list[Issue]]:
    """Keep the first valid channel/order/SKU line; flag every later occurrence."""
    seen: dict[tuple[str, str, str], Sale] = {}
    unique = []
    issues = []
    for sale in sales:
        key = (sale.source, sale.order_id, sale.sku)
        first = seen.get(key)
        if first is None:
            seen[key] = sale
            unique.append(sale)
            continue
        same = (first.quantity, first.original_amount, first.currency, first.sale_date) == (
            sale.quantity,
            sale.original_amount,
            sale.currency,
            sale.sale_date,
        )
        label = "duplicate transaction" if same else "conflicting duplicate transaction"
        issues.append(
            Issue(
                sale.source,
                sale.row,
                sale.order_id,
                "duplicate",
                f"{label}; first valid occurrence at row {first.row}; SKU {sale.sku}",
            )
        )
    return unique, issues

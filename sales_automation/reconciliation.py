"""Account for every loaded record, separately for each source and in total."""

from decimal import Decimal

from .models import Counts, Result


def reconcile(result: Result) -> Counts:
    total = Counts()
    for source, counts in result.counts.items():
        counts.valid_records = sum(sale.source == source for sale in result.sales)
        counts.rejected_records = sum(
            issue.source == source and issue.category == "rejected" for issue in result.issues
        )
        counts.duplicates = sum(
            issue.source == source and issue.category == "duplicate" for issue in result.issues
        )
        counts.verify()
        for field in ("input_records", "valid_records", "rejected_records", "duplicates"):
            setattr(total, field, getattr(total, field) + getattr(counts, field))
    total.verify()
    return total


def revenue(result: Result) -> Decimal:
    return sum((sale.normalized_amount for sale in result.sales), Decimal("0.00"))

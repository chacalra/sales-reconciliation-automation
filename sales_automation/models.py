"""Shared data contracts; monetary calculations use Decimal throughout."""

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class Issue:
    source: str
    row: int
    order_id: str
    category: str
    issue: str


@dataclass(frozen=True)
class Sale:
    source: str
    row: int
    order_id: str
    sku: str
    quantity: int
    unit_price: Decimal
    currency: str
    sale_date: date
    original_amount: Decimal
    normalized_amount: Decimal = Decimal("0")


@dataclass
class Counts:
    input_records: int = 0
    valid_records: int = 0
    rejected_records: int = 0
    duplicates: int = 0

    def verify(self) -> None:
        if self.input_records != self.valid_records + self.rejected_records + self.duplicates:
            raise ValueError("Reconciliation failed: input != valid + rejected + duplicates")


@dataclass(frozen=True)
class Rates:
    base: str
    rates: dict[str, Decimal]
    dates: dict[str, date]
    origin: str  # api, cache or identity


@dataclass
class Result:
    sales: list[Sale] = field(default_factory=list)
    issues: list[Issue] = field(default_factory=list)
    counts: dict[str, Counts] = field(default_factory=dict)
    rates: Rates | None = None

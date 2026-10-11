"""Validate each record independently and collect all its reasons for rejection."""

import re
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE

from .config import SourceConfig
from .models import Issue, Sale

CENT = Decimal("0.01")


def escape_excel_controls(value: str) -> str:
    """Keep forbidden characters visible in issue exports, as literal \\xNN escapes."""
    return ILLEGAL_CHARACTERS_RE.sub(lambda match: f"\\x{ord(match[0]):02x}", value)


def money(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def missing_columns(columns: list[str], source: SourceConfig) -> list[str]:
    return sorted(set(source.columns.values()) - set(columns))


def parse_decimal(raw: str, separator: str) -> Decimal:
    pattern = rf"[+-]?\d+(?:{re.escape(separator)}\d+)?"
    if not re.fullmatch(pattern, raw):
        raise ValueError("Not a plain decimal; thousands separators are not supported")
    value = Decimal(raw.replace(separator, "."))
    if not value.is_finite() or abs(value) > Decimal("1000000000000"):
        raise ValueError("Number out of range")
    return value


def validate_record(
    fields: dict[str, str],
    source: SourceConfig,
    row: int,
    supported: tuple[str, ...],
) -> tuple[Sale | None, Issue | None]:
    errors = []
    for field, value in fields.items():
        forbidden = ILLEGAL_CHARACTERS_RE.findall(value)
        if forbidden:
            codes = ", ".join(f"U+{ord(char):04X}" for char in sorted(set(forbidden)))
            errors.append(
                f"Excel-incompatible control character(s) in {field}: {codes}; value={value!r}"
            )
    for key in ("order_id", "sku", "currency"):
        if not fields[key]:
            errors.append(f"missing {key}")
    if fields["currency"] and fields["currency"] not in supported:
        errors.append(f"unknown or unsupported currency: {fields['currency']}")
    quantity = 0
    amount = Decimal("0")
    sale_date = None
    try:
        value = parse_decimal(fields["quantity"], source.decimal_separator)
        if value <= 0 or value != value.to_integral_value() or value > 1000000000:
            raise ValueError("Quantity must be a positive integer")
        quantity = int(value)
    except (ValueError, InvalidOperation):
        errors.append("invalid quantity")
    try:
        amount = parse_decimal(fields["amount"], source.decimal_separator)
        if amount < 0:
            raise ValueError("Negative price")
    except (ValueError, InvalidOperation):
        errors.append("invalid price/amount")
    try:
        sale_date = datetime.strptime(fields["sale_date"], source.date_format).date()
    except ValueError:
        errors.append("invalid sale_date")
    if errors:
        return None, Issue(source.name, row, fields["order_id"], "rejected", "; ".join(errors))
    original = money(amount * quantity if source.amount_type == "unit_price" else amount)
    unit_price = amount if source.amount_type == "unit_price" else amount / quantity
    assert sale_date is not None
    return Sale(
        source.name,
        row,
        fields["order_id"],
        fields["sku"],
        quantity,
        unit_price,
        fields["currency"],
        sale_date,
        original,
    ), None

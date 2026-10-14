"""HTTP endpoints for the existing sales validation rules."""

from collections import defaultdict
from dataclasses import asdict
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Annotated, Literal

from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from .config import FIELDS, SourceConfig
from .duplicate_detector import detect_duplicates
from .models import Counts
from .normalizers import normalize_fields
from .validators import validate_record

SUPPORTED_CURRENCIES = ("USD", "EUR", "GBP", "BRL")
Cell = Annotated[str, Field(strict=True, max_length=128)]
SourceName = Annotated[
    str, StringConstraints(strict=True, strip_whitespace=True, min_length=1, max_length=80)
]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SaleInput(Contract):
    """String cells preserve decimal precision and leading zeros in identifiers."""

    source: SourceName = "api"
    order_id: Cell = ""
    sku: Cell = ""
    quantity: Cell = ""
    amount: Cell = ""
    currency: Cell = ""
    sale_date: Cell = Field(default="", description="Sale date in YYYY-MM-DD format")


class BatchInput(Contract):
    records: list[SaleInput] = Field(min_length=1, max_length=1000)
    amount_type: Literal["unit_price", "line_total"] = "unit_price"
    decimal_separator: Literal[".", ","] = "."


class SaleOutput(Contract):
    source: str
    row: int = Field(description="One-based position in the request records array")
    order_id: str
    sku: str
    quantity: int
    unit_price: Decimal
    currency: str
    sale_date: date
    original_amount: Decimal


class IssueOutput(Contract):
    source: str
    row: int
    order_id: str
    category: Literal["rejected", "duplicate"]
    issue: str


class Summary(Contract):
    input_records: int
    valid_records: int
    rejected_records: int
    duplicates: int


class BatchOutput(Contract):
    summary: Summary
    sales: list[SaleOutput]
    issues: list[IssueOutput]
    totals_by_currency: dict[str, Decimal]


class HealthOutput(Contract):
    status: Literal["ok"]


app = FastAPI(
    title="Sales Validation API",
    version="0.1.0",
    description=(
        "Send sales records as JSON to check fields, normalize values and find duplicates. "
        "The response includes accepted records, issues and totals for each currency."
    ),
)


@app.get("/health", response_model=HealthOutput, tags=["Health"])
def health() -> HealthOutput:
    return HealthOutput(status="ok")


@app.post(
    "/sales/validate",
    response_model=BatchOutput,
    tags=["Sales"],
    summary="Validate sales records",
    description=(
        "Supply 1–1000 records with string-valued cells. Invalid sale values and missing "
        "cells become per-record issues; malformed JSON, wrong types, unknown fields and "
        "invalid batch options return HTTP 422. Duplicate identity is (source, order_id, "
        "sku), keeping the first valid occurrence within this request. Currencies: "
        "USD, EUR, GBP, BRL. No cross-currency conversion or persistent deduplication."
    ),
)
def validate_sales(batch: BatchInput) -> BatchOutput:
    candidates = []
    issues = []
    for row, record in enumerate(batch.records, start=1):
        # SourceConfig adapts the existing pure validators; no file is opened here.
        source = SourceConfig(
            name=record.source,
            file=Path("."),
            columns={field: field for field in FIELDS},
            amount_type=batch.amount_type,
            date_format="%Y-%m-%d",
            decimal_separator=batch.decimal_separator,
        )
        fields = normalize_fields(record.model_dump(), source)
        sale, issue = validate_record(fields, source, row, SUPPORTED_CURRENCIES)
        if sale is not None:
            candidates.append(sale)
        if issue is not None:
            issues.append(issue)

    unique, duplicates = detect_duplicates(candidates)
    rejected_count = len(issues)
    issues.extend(duplicates)
    issues.sort(key=lambda issue: issue.row)
    counts = Counts(len(batch.records), len(unique), rejected_count, len(duplicates))
    counts.verify()
    totals: dict[str, Decimal] = defaultdict(lambda: Decimal("0.00"))
    for sale in unique:
        totals[sale.currency] += sale.original_amount

    return BatchOutput(
        summary=Summary(**asdict(counts)),
        sales=[SaleOutput.model_validate(sale, from_attributes=True) for sale in unique],
        issues=[IssueOutput.model_validate(issue, from_attributes=True) for issue in issues],
        totals_by_currency=dict(sorted(totals.items())),
    )

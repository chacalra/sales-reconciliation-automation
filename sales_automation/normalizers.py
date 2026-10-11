"""Provider-specific column names end at this boundary."""

from collections.abc import Mapping
from typing import Any

from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE

from .config import SourceConfig


def normalize_fields(row: Mapping[str, Any], source: SourceConfig) -> dict[str, str]:
    values = {}
    for field, column in source.columns.items():
        value = str(row[column])
        # str.strip() would silently remove some Excel-forbidden control characters.
        values[field] = value if ILLEGAL_CHARACTERS_RE.search(value) else value.strip()
    values["currency"] = values["currency"].upper()
    return values

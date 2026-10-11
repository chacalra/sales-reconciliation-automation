"""Read values as strings to preserve identifiers and decimal input."""

import csv
from pathlib import Path

import pandas as pd

from .config import SourceConfig


def load_source(source: SourceConfig) -> pd.DataFrame:
    suffix = Path(source.file).suffix.lower()
    if suffix == ".csv":
        # Reject malformed CSV structure instead of silently dropping extra fields.
        with source.file.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.reader(handle, delimiter=source.delimiter, strict=True)
            headers = next(reader, [])
            rows = []
            for row_number, row in enumerate(reader, start=2):
                if len(row) != len(headers):
                    raise ValueError(f"{source.name}: malformed CSV record {row_number}")
                rows.append(row)
        if len(headers) != len(set(headers)):
            raise ValueError(f"{source.name}: duplicate column headers")
        return pd.DataFrame(rows, columns=headers)
    if suffix == ".xlsx":
        with pd.ExcelFile(source.file, engine="openpyxl") as excel:
            sheet_name = source.sheet_name
            if isinstance(sheet_name, int):
                if not 0 <= sheet_name < len(excel.sheet_names):
                    raise ValueError(f"{source.name}: worksheet index out of range: {sheet_name}")
                sheet_name = excel.sheet_names[sheet_name]
            if sheet_name not in excel.sheet_names:
                raise ValueError(f"{source.name}: worksheet not found: {sheet_name}")
            sheet = excel.book[sheet_name]
            headers = next(sheet.iter_rows(min_row=1, max_row=1, values_only=True), ())
            # Check original cell values before pandas disambiguates duplicate names.
            named_headers = [header for header in headers if header is not None]
            if len(named_headers) != len(set(named_headers)):
                raise ValueError(f"{source.name}: duplicate column headers")
            return pd.read_excel(
                excel,
                sheet_name=sheet_name,
                dtype=str,
                keep_default_na=False,
            )
    raise ValueError(f"Unsupported input file extension: {suffix}")

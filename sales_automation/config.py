"""Load explicit source mappings; paths are relative to the configuration file."""

from dataclasses import dataclass
from math import isfinite
from pathlib import Path

import yaml
from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE

FIELDS = {"order_id", "sku", "quantity", "amount", "currency", "sale_date"}


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Config {field} must be a nonempty string")
    if ILLEGAL_CHARACTERS_RE.search(value):
        raise ValueError(f"Config {field} contains Excel-incompatible control characters")
    return value


def _number(value: object, field: str, *, integer: bool = False) -> int | float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"Config {field} must be a {'whole number' if integer else 'number'}")
    if integer and not isinstance(value, int):
        raise ValueError(f"Config {field} must be a whole number")
    try:
        finite = isfinite(value)
    except OverflowError as error:
        raise ValueError(f"Config {field} is out of range") from error
    if not finite:
        raise ValueError(f"Config {field} must be finite")
    return value


@dataclass(frozen=True)
class SourceConfig:
    name: str
    file: Path
    columns: dict[str, str]
    amount_type: str
    date_format: str
    decimal_separator: str = "."
    delimiter: str = ","
    sheet_name: str | int = 0


@dataclass(frozen=True)
class Config:
    base_currency: str
    supported_currencies: tuple[str, ...]
    output_dir: Path
    sources: tuple[SourceConfig, ...]
    url: str
    timeout_seconds: float
    retries: int
    backoff_seconds: float
    cache_file: Path
    max_cache_age_days: int


def load_config(path: Path) -> Config:
    root = path.resolve().parent
    with path.open(encoding="utf-8") as handle:
        raw = yaml.safe_load(handle)
    if not isinstance(raw, dict):
        raise ValueError("Config must be a YAML mapping")
    base = _text(raw.get("base_currency", "USD"), "base_currency").upper()
    currencies = raw.get("supported_currencies", ["USD", "EUR", "GBP", "BRL"])
    if not isinstance(currencies, list) or not currencies:
        raise ValueError("supported_currencies must be a nonempty list")
    supported = tuple(_text(item, "supported_currencies item").upper() for item in currencies)
    if any(len(item) != 3 or not item.isascii() or not item.isalpha() for item in supported):
        raise ValueError("Currencies must be three-letter codes")
    if base not in supported:
        raise ValueError("base_currency must be in supported_currencies")
    source_map = raw.get("sources")
    if not isinstance(source_map, dict) or not source_map:
        raise ValueError("At least one source is required")
    sources = []
    for name, spec in source_map.items():
        name = _text(name, "source name")
        if not isinstance(spec, dict):
            raise ValueError(f"Invalid configuration for source {name}")
        mapping = spec.get("columns", {})
        if not isinstance(mapping, dict) or set(mapping) != FIELDS:
            raise ValueError(f"{name}: columns must map exactly {sorted(FIELDS)}")
        if any(not isinstance(value, str) or not value for value in mapping.values()):
            raise ValueError(f"{name}: column names must be nonempty strings")
        if len(set(mapping.values())) != len(FIELDS):
            raise ValueError(f"{name}: column mappings must be distinct")
        amount_type = spec.get("amount_type", "unit_price")
        if not isinstance(amount_type, str) or amount_type not in {"unit_price", "line_total"}:
            raise ValueError(f"{name}: invalid amount_type")
        separator = spec.get("decimal_separator", ".")
        delimiter = spec.get("delimiter", ",")
        if (
            not isinstance(separator, str)
            or separator not in {".", ","}
            or not isinstance(delimiter, str)
            or len(delimiter) != 1
        ):
            raise ValueError(f"{name}: invalid decimal separator or delimiter")
        file = _text(spec.get("file"), f"sources.{name}.file")
        date_format = _text(spec.get("date_format"), f"sources.{name}.date_format")
        sheet_name = spec.get("sheet_name", 0)
        if (
            isinstance(sheet_name, bool)
            or not isinstance(sheet_name, (str, int))
            or isinstance(sheet_name, int)
            and sheet_name < 0
            or isinstance(sheet_name, str)
            and not sheet_name.strip()
        ):
            raise ValueError(f"{name}: sheet_name must be a worksheet name or nonnegative integer")
        sources.append(
            SourceConfig(
                name=name,
                file=root / file,
                columns=mapping,
                amount_type=amount_type,
                date_format=date_format,
                decimal_separator=separator,
                delimiter=delimiter,
                sheet_name=sheet_name,
            )
        )
    fx = raw.get("exchange_rates", {})
    if not isinstance(fx, dict):
        raise ValueError("Config exchange_rates must be a YAML mapping")
    timeout = float(_number(fx.get("timeout_seconds", 5), "exchange_rates.timeout_seconds"))
    retries = int(_number(fx.get("retries", 2), "exchange_rates.retries", integer=True))
    backoff = float(_number(fx.get("backoff_seconds", 0.5), "exchange_rates.backoff_seconds"))
    max_age = int(
        _number(fx.get("max_cache_age_days", 14), "exchange_rates.max_cache_age_days", integer=True)
    )
    if not (0 < timeout <= 60 and 0 <= retries <= 5 and 0 <= backoff <= 10 and max_age >= 0):
        raise ValueError("Invalid FX timeout/retry/cache settings")
    output = root / _text(raw.get("output_dir", "output"), "output_dir")
    cache = root / _text(
        fx.get("cache_file", "cache/exchange_rates.json"), "exchange_rates.cache_file"
    )
    url = _text(fx.get("url", "https://api.frankfurter.dev/v2/rates"), "exchange_rates.url")
    protected = {source.file.resolve() for source in sources} | {path.resolve()}
    artifacts = {
        output / name
        for name in (
            "report.xlsx",
            "issues.csv",
            "consolidated_sales.csv",
            "app.log",
        )
    } | {cache}
    if any(item.resolve() in protected for item in artifacts):
        raise ValueError("Output/cache paths must not overwrite inputs or configuration")
    return Config(
        base,
        supported,
        output,
        tuple(sources),
        url,
        timeout,
        retries,
        backoff,
        cache,
        max_age,
    )

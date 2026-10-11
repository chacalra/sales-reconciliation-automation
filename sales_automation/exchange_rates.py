"""Bounded REST retries, validated dated rates and a local cache that can be rebased."""

import json
import logging
import time
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

import requests

from .config import Config
from .models import Rates

logger = logging.getLogger(__name__)


def validate_rates(payload: object, base: str, max_age: int) -> Rates:
    if not isinstance(payload, dict) or payload.get("base") != base:
        raise ValueError("FX response/cache base mismatch")
    raw_rates = payload.get("rates")
    raw_dates = payload.get("dates")
    if not isinstance(raw_rates, dict) or not isinstance(raw_dates, dict):
        raise ValueError("Malformed FX rates/dates")
    rates = {base: Decimal("1")}
    dates = {}
    for code, raw in raw_rates.items():
        if code == base:
            if Decimal(str(raw)) != 1:
                raise ValueError("Base currency rate must be 1")
            continue
        value = Decimal(str(raw))
        if not value.is_finite() or value <= 0:
            raise ValueError(f"Invalid FX rate for {code}")
        observed = date.fromisoformat(raw_dates[code])
        age = (date.today() - observed).days
        if age < 0 or age > max_age:
            raise ValueError(f"FX date for {code} outside allowed age: {observed}")
        rates[code] = value
        dates[code] = observed
    return Rates(base, rates, dates, "api")


def parse_response(payload: object, base: str, quotes: set[str], max_age: int) -> Rates:
    if not isinstance(payload, list) or not payload:
        raise ValueError("Expected a nonempty Frankfurter v2 rate list")
    normalized: dict = {"base": base, "rates": {}, "dates": {}}
    for item in payload:
        if not isinstance(item, dict) or item.get("base") != base:
            raise ValueError("FX response contains an unexpected base")
        code = item["quote"]
        if code in normalized["rates"]:
            raise ValueError("Duplicate currency in FX response")
        normalized["rates"][code] = item["rate"]
        normalized["dates"][code] = item["date"]
    result = validate_rates(normalized, base, max_age)
    if not quotes.issubset(result.rates):
        raise ValueError("FX response is missing requested currencies")
    return result


def write_cache(path: Path, rates: Rates) -> None:
    payload = {
        "base": rates.base,
        "rates": {code: str(value) for code, value in rates.rates.items()},
        "dates": {code: value.isoformat() for code, value in rates.dates.items()},
        "provider": "Frankfurter v2",
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def read_cache(config: Config, required: set[str]) -> Rates:
    payload = json.loads(config.cache_file.read_text(encoding="utf-8"))
    result = validate_rates(payload, payload["base"], config.max_cache_age_days)
    if not (required | {config.base_currency}).issubset(result.rates):
        raise ValueError("Cached rates do not cover all currencies in this run")
    divisor = result.rates[config.base_currency]
    rebased = {code: value / divisor for code, value in result.rates.items()}
    dates = dict(result.dates)
    if config.base_currency != result.base:
        # A cross rate is only as recent as its oldest component.
        base_date = dates[config.base_currency]
        dates = {code: min(observed, base_date) for code, observed in dates.items()}
        dates[result.base] = base_date
        dates.pop(config.base_currency, None)
    return Rates(config.base_currency, rebased, dates, "cache")


def fetch_rates(config: Config, required: set[str], offline: bool = False) -> Rates:
    quotes = required - {config.base_currency}
    if not quotes:
        return Rates(config.base_currency, {config.base_currency: Decimal("1")}, {}, "identity")
    if not offline:
        for attempt in range(config.retries + 1):
            try:
                response = requests.get(
                    config.url,
                    params={"base": config.base_currency, "quotes": ",".join(sorted(quotes))},
                    timeout=config.timeout_seconds,
                )
                response.raise_for_status()
                result = parse_response(
                    response.json(),
                    config.base_currency,
                    quotes,
                    config.max_cache_age_days,
                )
                try:
                    write_cache(config.cache_file, result)
                except OSError as error:
                    logger.warning("Could not save FX cache: %s", error)
                logger.info("Using API exchange rates: %s", result.dates)
                return result
            except (
                requests.RequestException,
                ValueError,
                KeyError,
                TypeError,
                InvalidOperation,
            ) as error:
                logger.warning("Exchange rate API attempt %d failed: %s", attempt + 1, error)
                if attempt < config.retries:
                    logger.info("Retry %d/%d", attempt + 1, config.retries)
                    time.sleep(config.backoff_seconds * (2**attempt))
    try:
        result = read_cache(config, required)
    except (OSError, ValueError, KeyError, TypeError, InvalidOperation) as error:
        raise ValueError(
            f"No usable exchange rates; cache unavailable or invalid: {error}"
        ) from error
    logger.warning("Using cached exchange rates: %s", result.dates)
    return result

"""One command from provider exports to an auditable business report."""

import argparse
import csv
import logging
from dataclasses import replace
from decimal import InvalidOperation
from pathlib import Path
from zipfile import BadZipFile

import yaml

from .config import Config, load_config
from .duplicate_detector import detect_duplicates
from .exchange_rates import fetch_rates
from .loaders import load_source
from .models import Counts, Issue, Result
from .normalizers import normalize_fields
from .reconciliation import reconcile, revenue
from .reporting import write_report
from .validators import missing_columns, money, validate_record

logger = logging.getLogger(__name__)


def run(config: Config, offline: bool = False) -> Result:
    logger.info("Starting sales reconciliation; base currency %s", config.base_currency)
    result = Result()
    candidates = []
    for source in config.sources:
        frame = load_source(source)
        result.counts[source.name] = Counts(input_records=len(frame))
        logger.info("Loaded %d %s records from %s", len(frame), source.name, source.file)
        missing = missing_columns(list(frame.columns), source)
        if missing:
            reason = f"Missing required column(s): {', '.join(missing)}"
            logger.error("%s: %s", source.name, reason)
            # Header issues are separate; each data record still has exactly one outcome.
            result.issues.append(Issue(source.name, 1, "", "schema", reason))
            order_column = source.columns["order_id"]
            for row_number, raw in enumerate(frame.to_dict("records"), start=2):
                result.issues.append(
                    Issue(
                        source.name,
                        row_number,
                        str(raw.get(order_column, "")),
                        "rejected",
                        reason,
                    )
                )
            continue
        for row_number, raw in enumerate(frame.to_dict("records"), start=2):
            sale, issue = validate_record(
                normalize_fields(raw, source),
                source,
                row_number,
                config.supported_currencies,
            )
            if issue:
                result.issues.append(issue)
            if sale:
                candidates.append(sale)
    unique, duplicates = detect_duplicates(candidates)
    result.issues.extend(duplicates)
    # Fetch the configured set so a successful cache also supports changing base currency.
    needed = set(config.supported_currencies) if unique else {config.base_currency}
    result.rates = fetch_rates(config, needed, offline=offline)
    for sale in unique:
        converted = money(sale.original_amount / result.rates.rates[sale.currency])
        result.sales.append(replace(sale, normalized_amount=converted))
    result.issues.sort(key=lambda item: (item.source, item.row, item.category))
    total = reconcile(result)
    logger.info(
        "Rejected %d invalid records; detected %d duplicates",
        total.rejected_records,
        total.duplicates,
    )
    write_report(config.output_dir, result, total, config.base_currency)
    for filename in ("report.xlsx", "issues.csv", "consolidated_sales.csv"):
        logger.info("Generated %s", config.output_dir / filename)
    logger.info(
        "Reconciliation PASS | Input: %d | Valid: %d | Rejected: %d | Duplicates: %d",
        total.input_records,
        total.valid_records,
        total.rejected_records,
        total.duplicates,
    )
    logger.info(
        "Total revenue: %s %s | Processing completed", revenue(result), config.base_currency
    )
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Consolidate sales exports into an audited Excel report"
    )
    parser.add_argument("--config", type=Path, default=Path("config.yaml"))
    parser.add_argument(
        "--offline", action="store_true", help="Use validated local FX cache without HTTP requests"
    )
    args = parser.parse_args(argv)
    try:
        config = load_config(args.config)
        config.output_dir.mkdir(parents=True, exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(levelname)s %(message)s",
            force=True,
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(config.output_dir / "app.log", mode="w", encoding="utf-8"),
            ],
        )
        run(config, offline=args.offline)
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        InvalidOperation,
        yaml.YAMLError,
        csv.Error,
        BadZipFile,
    ) as error:
        logging.error("Processing failed: %s. Inspect app.log and the output directory.", error)
        return 1
    return 0

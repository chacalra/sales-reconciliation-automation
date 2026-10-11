from dataclasses import replace
from datetime import date
from pathlib import Path

import pytest

from sales_automation.config import load_config

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def config(tmp_path):
    return replace(
        load_config(ROOT / "config.example.yaml"),
        output_dir=tmp_path / "output",
        cache_file=tmp_path / "rates.json",
        retries=2,
        backoff_seconds=0,
    )


@pytest.fixture
def api_payload():
    return [
        {"base": "USD", "quote": code, "rate": rate, "date": date.today().isoformat()}
        for code, rate in [("EUR", 0.8), ("GBP", 0.5), ("BRL", 5)]
    ]

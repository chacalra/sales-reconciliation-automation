import copy
import logging
from pathlib import Path

import pytest
import yaml

from sales_automation.config import load_config
from sales_automation.main import main

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def raw_config():
    return yaml.safe_load((ROOT / "config.example.yaml").read_text())


@pytest.mark.parametrize("value", [[], None, "USD", 42])
def test_invalid_yaml_root_is_controlled(tmp_path, value):
    path = tmp_path / "bad.yaml"
    path.write_text(yaml.safe_dump(value))
    with pytest.raises(ValueError, match="Config must be a YAML mapping"):
        load_config(path)


@pytest.mark.parametrize(
    "keys,value,message",
    [
        (("exchange_rates",), [], "exchange_rates must be a YAML mapping"),
        (("exchange_rates",), None, "exchange_rates must be a YAML mapping"),
        (("exchange_rates",), "api", "exchange_rates must be a YAML mapping"),
        (("sources",), [], "At least one source"),
        (("sources", "amazon"), [], "Invalid configuration for source amazon"),
        (("sources", "amazon", "columns"), [], "columns must map exactly"),
        (("sources", "amazon", "columns", "sku"), [], "column names must be nonempty strings"),
        (("supported_currencies",), {}, "supported_currencies must be a nonempty list"),
        (
            ("supported_currencies",),
            ["USD", {}],
            "supported_currencies item must be a nonempty string",
        ),
        (("base_currency",), [], "base_currency must be a nonempty string"),
        (("sources", "amazon", "file"), {}, "sources.amazon.file must be a nonempty string"),
        (("sources", "amazon", "date_format"), None, "date_format must be a nonempty string"),
        (("sources", "amazon", "sheet_name"), [], "sheet_name must be a worksheet name"),
        (("sources", "amazon", "sheet_name"), True, "sheet_name must be a worksheet name"),
        (("sources", "amazon", "amount_type"), [], "invalid amount_type"),
        (("sources", "amazon", "decimal_separator"), [], "invalid decimal separator"),
        (("exchange_rates", "timeout_seconds"), [], "timeout_seconds must be a number"),
        (("exchange_rates", "retries"), 1.5, "retries must be a whole number"),
        (("exchange_rates", "retries"), True, "retries must be a whole number"),
        (("exchange_rates", "backoff_seconds"), float("nan"), "backoff_seconds must be finite"),
        (("exchange_rates", "timeout_seconds"), 10**400, "timeout_seconds is out of range"),
        (("exchange_rates", "url"), {}, "exchange_rates.url must be a nonempty string"),
        (("exchange_rates", "cache_file"), [], "cache_file must be a nonempty string"),
        (("output_dir",), [], "output_dir must be a nonempty string"),
    ],
)
def test_mistyped_config_fields_raise_clear_value_error(raw_config, tmp_path, keys, value, message):
    raw = copy.deepcopy(raw_config)
    parent = raw
    for key in keys[:-1]:
        parent = parent[key]
    parent[keys[-1]] = value
    path = tmp_path / "bad.yaml"
    path.write_text(yaml.safe_dump(raw))
    with pytest.raises(ValueError, match=message):
        load_config(path)


def test_invalid_exchange_rates_config_returns_one_without_traceback(raw_config, tmp_path, caplog):
    raw_config["exchange_rates"] = []
    path = tmp_path / "bad.yaml"
    path.write_text(yaml.safe_dump(raw_config))
    with caplog.at_level(logging.ERROR):
        assert main(["--config", str(path)]) == 1
    assert "exchange_rates must be a YAML mapping" in caplog.text
    assert "Traceback" not in caplog.text
    assert "No new report was published" not in caplog.text
    assert not (tmp_path / "output").exists()

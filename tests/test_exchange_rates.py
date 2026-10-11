from dataclasses import replace
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import Mock

import pytest
import requests

from sales_automation.exchange_rates import fetch_rates, parse_response, write_cache


def response(payload):
    result = Mock()
    result.json.return_value = payload
    return result


def seed(config, payload):
    rates = parse_response(payload, "USD", {"EUR", "GBP", "BRL"}, 14)
    write_cache(config.cache_file, rates)


def test_api_timeout_retries_and_cache_fallback(config, api_payload, monkeypatch):
    seed(config, api_payload)
    request = Mock(side_effect=requests.Timeout("simulated timeout"))
    monkeypatch.setattr("sales_automation.exchange_rates.requests.get", request)
    rates = fetch_rates(config, {"EUR", "USD"})
    assert request.call_count == 3
    assert rates.origin == "cache"
    assert rates.rates["EUR"] == Decimal("0.8")
    assert request.call_args.kwargs["timeout"] == 5


def test_retry_recovers_and_writes_cache(config, api_payload, monkeypatch):
    request = Mock(side_effect=[requests.Timeout(), response(api_payload)])
    monkeypatch.setattr("sales_automation.exchange_rates.requests.get", request)
    rates = fetch_rates(config, {"EUR", "GBP", "BRL"})
    assert rates.origin == "api"
    assert request.call_count == 2
    assert config.cache_file.exists()


def test_http_failure_uses_cache(config, api_payload, monkeypatch):
    seed(config, api_payload)
    bad = response(api_payload)
    bad.raise_for_status.side_effect = requests.HTTPError("503 unavailable")
    monkeypatch.setattr("sales_automation.exchange_rates.requests.get", Mock(return_value=bad))
    assert fetch_rates(config, {"EUR"}).origin == "cache"


def test_offline_makes_no_http_call_and_rebases(config, api_payload, monkeypatch):
    seed(config, api_payload)
    request = Mock(side_effect=AssertionError("No network permitted"))
    monkeypatch.setattr("sales_automation.exchange_rates.requests.get", request)
    rates = fetch_rates(replace(config, base_currency="EUR"), {"USD", "GBP", "BRL"}, offline=True)
    assert rates.rates["USD"] == Decimal("1.25")
    assert rates.rates["GBP"] == Decimal("0.625")
    request.assert_not_called()


def test_no_api_or_cache_means_no_fake_rates(config, monkeypatch):
    monkeypatch.setattr(
        "sales_automation.exchange_rates.requests.get", Mock(side_effect=requests.Timeout())
    )
    with pytest.raises(ValueError, match="No usable exchange rates"):
        fetch_rates(config, {"EUR"})


@pytest.mark.parametrize("rate", [0, -1, "NaN", "Infinity"])
def test_reject_bad_fx_rates(api_payload, rate):
    api_payload[0]["rate"] = rate
    with pytest.raises(ValueError):
        parse_response(api_payload, "USD", {"EUR"}, 14)


def test_reject_incomplete_response(api_payload):
    with pytest.raises(ValueError, match="missing requested"):
        parse_response(api_payload[:1], "USD", {"EUR", "GBP"}, 14)


def test_reject_stale_cache(config, api_payload):
    seed(config, api_payload)
    config = replace(config, max_cache_age_days=0)
    import json

    payload = json.loads(config.cache_file.read_text())
    payload["dates"]["EUR"] = (date.today() - timedelta(days=1)).isoformat()
    config.cache_file.write_text(json.dumps(payload))
    with pytest.raises(ValueError, match="outside allowed age"):
        fetch_rates(config, {"EUR"}, offline=True)


def test_invalid_json_falls_back(config, api_payload, monkeypatch):
    seed(config, api_payload)
    bad = Mock()
    bad.json.side_effect = ValueError("invalid JSON")
    request = Mock(return_value=bad)
    monkeypatch.setattr("sales_automation.exchange_rates.requests.get", request)
    assert fetch_rates(config, {"EUR"}).origin == "cache"
    assert request.call_count == 3


def test_identity_does_not_need_network_or_cache(config, monkeypatch):
    request = Mock(side_effect=AssertionError("No request needed"))
    monkeypatch.setattr("sales_automation.exchange_rates.requests.get", request)
    assert fetch_rates(config, {"USD"}).origin == "identity"
    request.assert_not_called()

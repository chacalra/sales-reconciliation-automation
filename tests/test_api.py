import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
import requests

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def client(monkeypatch):
    pytest.importorskip("fastapi", reason="Install the api extra to test the optional HTTP demo")
    from fastapi.testclient import TestClient

    from sales_automation.api import app

    def no_network(*args, **kwargs):
        pytest.fail("The JSON API must not call an exchange-rate service")

    monkeypatch.setattr(requests, "get", no_network)
    with TestClient(app) as client:
        yield client


@pytest.fixture
def example():
    return json.loads((ROOT / "examples/api/request.json").read_text())


def test_health_and_documented_contract(client):
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/docs").status_code == 200
    schema = client.get("/openapi.json").json()
    assert "/sales/validate" in schema["paths"]
    assert (
        schema["components"]["schemas"]["BatchInput"]["properties"]["records"]["maxItems"] == 1000
    )


def test_mixed_batch_matches_committed_response(client, example):
    response = client.post("/sales/validate", json=example)
    assert response.status_code == 200
    result = response.json()
    expected = json.loads((ROOT / "examples/api/response.json").read_text())
    assert result == expected
    assert result["summary"] == {
        "input_records": 4,
        "valid_records": 2,
        "rejected_records": 1,
        "duplicates": 1,
    }
    assert result["totals_by_currency"] == {"EUR": "15.00", "USD": "20.50"}


def test_all_invalid_records_are_reported(client):
    response = client.post("/sales/validate", json={"records": [{}, {"quantity": "NaN"}]})
    assert response.status_code == 200
    body = response.json()
    assert body["summary"]["rejected_records"] == 2
    assert body["sales"] == []
    assert body["totals_by_currency"] == {}
    assert [issue["row"] for issue in body["issues"]] == [1, 2]
    assert all("missing order_id" in issue["issue"] for issue in body["issues"])


def test_decimal_comma_line_total_and_rounding(client, example):
    record = example["records"][0]
    record.update(amount="10,005", quantity="3", currency="eur")
    response = client.post(
        "/sales/validate",
        json={"records": [record], "decimal_separator": ",", "amount_type": "line_total"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["sales"][0]["original_amount"] == "10.01"
    assert body["sales"][0]["order_id"] == "0001"
    assert body["totals_by_currency"] == {"EUR": "10.01"}


def test_conflicting_duplicates_and_source_identity(client, example):
    first = example["records"][0]
    response = client.post(
        "/sales/validate",
        json={"records": [first, {**first, "amount": "99.00"}, {**first, "source": "store"}]},
    )
    body = response.json()
    assert body["summary"]["valid_records"] == 2
    assert body["summary"]["duplicates"] == 1
    assert "conflicting duplicate" in body["issues"][0]["issue"]
    assert body["totals_by_currency"] == {"USD": "41.00"}


@pytest.mark.parametrize(
    "change,reason",
    [
        ({"currency": "ZZZ"}, "unsupported currency"),
        ({"sale_date": "2026-02-30"}, "invalid sale_date"),
        ({"quantity": "1.5"}, "invalid quantity"),
        ({"quantity": "0"}, "invalid quantity"),
        ({"amount": "-1"}, "invalid price/amount"),
        ({"amount": "Infinity"}, "invalid price/amount"),
        ({"sku": "bad\u0001value"}, "control character"),
    ],
)
def test_invalid_sale_does_not_drop_other_records(client, example, change, reason):
    first = example["records"][0]
    response = client.post("/sales/validate", json={"records": [{**first, **change}, first]})
    body = response.json()
    assert response.status_code == 200
    assert body["summary"] == {
        "input_records": 2,
        "valid_records": 1,
        "rejected_records": 1,
        "duplicates": 0,
    }
    assert body["sales"][0]["row"] == 2
    assert reason in body["issues"][0]["issue"]


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"records": []},
        {"records": [{}] * 1001},
        {"records": [{"amount": 10.25}]},
        {"records": [{"source": " "}]},
        {"records": [{"sku": "x" * 129}]},
        {"records": [{}], "amount_type": "guess"},
        {"records": [{}], "decimal_separator": ";"},
        {"records": [{"unknown": "column"}]},
        {"records": [{}], "output_dir": "/tmp"},
    ],
)
def test_invalid_contract_is_422(client, payload):
    response = client.post("/sales/validate", json=payload)
    assert response.status_code == 422
    assert "detail" in response.json()


def test_malformed_json_is_422(client):
    response = client.post(
        "/sales/validate", content='{"records":', headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 422


def test_simultaneous_requests_have_no_shared_deduplication_state(client, example):
    def submit(_):
        return client.post("/sales/validate", json=example).json()

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(submit, range(8)))
    assert all(result == results[0] for result in results)
    assert all(result["summary"]["valid_records"] == 2 for result in results)

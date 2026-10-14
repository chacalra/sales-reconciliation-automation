# Sales validation API

Use this endpoint when sales records arrive as JSON rather than CSV or Excel files.
It checks the fields, normalizes values and finds duplicates using the same functions
as the file workflow. The response contains accepted records, issues and totals for
each currency. It does not create Excel reports or fetch exchange rates.

The examples use fictional sales records.

## Run locally

From the repository root, with Python 3.11+:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[api]"
python -m uvicorn sales_automation.api:app --host 127.0.0.1 --port 8000
```

For the locked development environment:

```bash
uv sync --frozen --extra dev --extra api
.venv/bin/python -m uvicorn sales_automation.api:app --host 127.0.0.1 --port 8000
```

Open <http://127.0.0.1:8000/docs> for interactive documentation and
<http://127.0.0.1:8000/openapi.json> for the machine-readable contract.

## Endpoints

| Method | Route | Result |
| --- | --- | --- |
| GET | `/health` | `{"status": "ok"}` |
| POST | `/sales/validate` | Accepted records, issues, counts and totals by currency |

Send the committed example:

```bash
curl --fail-with-body http://127.0.0.1:8000/sales/validate \
  -H 'Content-Type: application/json' \
  --data-binary @examples/api/request.json
```

The complete expected response is in [response.json](../examples/api/response.json).
There are four input records: two valid, one rejected and one duplicate. Accepted
amounts total USD 20.50 and EUR 15.00 separately. No exchange-rate conversion or
combined total across currencies is performed.

## Request rules

- `records` contains 1–1000 objects. Cell values are strings, preserving identifiers
  such as `"0001"` and avoiding floating-point money inputs. Cells have a 128-character
  limit; source names have an 80-character limit and cannot be blank.
- Fields: `source` (default `"api"`), `order_id`, `sku`, `quantity`, `amount`, `currency`
  and `sale_date`. Missing cells become empty strings for domain validation.
- `sale_date` uses the existing validator's `%Y-%m-%d` date format.
- `amount_type` is `"unit_price"` (default) or `"line_total"`. Unit prices are multiplied
  by quantity; line totals are not. Monetary totals round half-up to two decimals.
- `decimal_separator` is `"."` (default) or `","`; thousands separators are unsupported.
- Supported currencies are USD, EUR, GBP and BRL. Whitespace is trimmed and currency
  codes are uppercased. Unknown currencies are rejected, not guessed or converted.
- Quantity must be a positive integer; amount must be nonnegative. Existing numeric
  bounds and validation of Excel-incompatible control characters still apply.
- Duplicate identity is `(source, order_id, sku)`. Keep the first valid occurrence
  within this request; flag subsequent exact or conflicting duplicates.
- `row` is the one-based array position, not a spreadsheet row. Returned money values
  are decimal strings. Totals include only accepted, unique records.

## Error behavior

Invalid sale values (bad dates, negative quantity, unsupported currency, missing
cells) produce per-record `issues` with HTTP 200. Other valid records are still
returned. An entirely rejected batch also returns HTTP 200 with empty sales/totals.

Malformed JSON, wrong field types, unknown fields, empty/oversized batches and
invalid batch options return HTTP 422 with FastAPI's structured `detail` response.
Structural errors reject the whole request; numeric cells are not silently coerced.

Every structurally valid request satisfies:

```text
input_records = valid_records + rejected_records + duplicates
```

## Tests

```bash
uv run --frozen --extra dev --extra api pytest -q
uv run --frozen --extra dev --extra api ruff check .
uv run --frozen --extra dev --extra api ruff format --check .
```

HTTP tests validate the example, mixed/error batches, decimal handling, duplicate
identity and simultaneous requests. Exchange-rate requests are forbidden by the
API test fixture. HTTP tests skip if FastAPI is absent; CI installs both extras.

## Storage and deployment

Each request is processed in memory. Records are not saved, and duplicate checks
apply only within that request. Use the CLI for file imports and Excel reports.

The commands above bind to localhost. Authentication and public hosting are not
configured in this project.

[Screenshots](../assets/api/README.md) show the documentation and the sample response.

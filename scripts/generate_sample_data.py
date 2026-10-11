"""Generate deterministic fictional exports; never uses customer data."""

import csv
from pathlib import Path

from openpyxl import Workbook

ROOT = Path(__file__).resolve().parents[1]


def generate() -> None:
    target = ROOT / "examples" / "input"
    target.mkdir(parents=True, exist_ok=True)
    amazon = [
        [f"AMZ-{i:03d}", f"SKU-{i % 6 + 1:02d}", i % 4 + 1, f"{12 + i}.50", "USD", "2026-10-05"]
        for i in range(1, 31)
    ]
    amazon += [amazon[0].copy(), amazon[5].copy()]
    for column, value in [(2, "-3"), (3, "-20"), (0, ""), (1, ""), (5, "wrong-date")]:
        row = [f"AMZ-BAD-{len(amazon)}", "SKU-01", 2, "20.00", "USD", "2026-10-05"]
        row[column] = value
        amazon.append(row)
    with (target / "amazon_sales.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["order_id", "sku", "quantity", "unit_price", "currency", "date"])
        writer.writerows(amazon)
    shopify = [
        [
            f"SH-{i:03d}",
            f"SKU-{i % 6 + 1:02d}",
            i % 3 + 1,
            f"{35 + i}.90",
            "EUR",
            "2026-10-06T14:30:00",
        ]
        for i in range(1, 26)
    ]
    # Two SKUs in one order are legitimate lines, not duplicates.
    shopify.append(["SH-001", "SKU-99", 2, "30.00", "EUR", "2026-10-06T14:30:00"])
    shopify += [shopify[0].copy()]
    shopify += [
        ["SH-BAD-1", "SKU-01", "abc", "50", "EUR", "2026-10-06T14:30:00"],
        ["SH-BAD-2", "SKU-01", 1, "50", "", "2026-10-06T14:30:00"],
    ]
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Sales"
    sheet.append(["id", "product_sku", "qty", "total_amount", "currency_code", "created_at"])
    for row in shopify:
        sheet.append(row)
    workbook.save(target / "shopify_sales.xlsx")
    marketplace = [
        [
            f"MP-{i:03d}",
            f"SKU-{i % 6 + 1:02d}",
            i % 3 + 1,
            f"{50 + i},25",
            "BRL" if i % 2 else "GBP",
            "07/10/2026",
        ]
        for i in range(1, 21)
    ]
    marketplace.append(marketplace[0].copy())
    conflict = marketplace[2].copy()
    conflict[3] = "999,00"
    marketplace.append(conflict)
    marketplace.append(["MP-BAD-1", "SKU-01", 1, "30,00", "XYZ", "07/10/2026"])
    with (target / "marketplace_sales.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, delimiter=";")
        writer.writerow(["transaction_id", "product", "units", "price", "currency", "sale_date"])
        writer.writerows(marketplace)
    print("Generated fictional exports: 89 input rows, 76 valid, 8 rejected, 5 duplicates.")


if __name__ == "__main__":
    generate()

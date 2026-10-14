"""Capture a local API run and render portfolio images from real response data.

Optional tooling: uv run --no-project --with playwright python scripts/capture_api_gallery.py
Install Chromium with Playwright first, or supply --browser /path/to/chromium.
"""

import argparse
import html
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]

CSS = """
*{box-sizing:border-box}body{margin:0;background:#eef3f4;color:#102831;
font-family:Arial,Helvetica,sans-serif}main{width:1000px;height:750px;padding:52px;
position:relative;overflow:hidden}h1{font-size:62px;line-height:1.04;letter-spacing:-2px;
margin:24px 0}h2{font-size:44px;line-height:1.1;margin:16px 0 24px;letter-spacing:-1px}
.eyebrow{font-size:16px;font-weight:700;letter-spacing:3px;text-transform:uppercase;
color:#42616b}.accent{color:#14777c}.sub{font-size:23px;color:#42616b;line-height:1.5}
.footer{position:absolute;bottom:27px;left:52px;right:52px;display:flex;
justify-content:space-between;font-size:14px;color:#59727a}.flow{display:flex;
align-items:center;gap:22px;margin:42px 0}.node{background:#fff;border:1px solid #cad9dd;
border-radius:18px;padding:26px;font-size:24px;font-weight:700;flex:1;text-align:center}
.arrow{font-size:32px;color:#14777c}.badges{display:flex;gap:14px}.badge{padding:12px 17px;
background:#dcebed;color:#18575c;border-radius:8px;font-size:17px;font-weight:600}
.dark{background:#102831;color:#e6f1f4;border-radius:16px;padding:24px}
.route{font-family:monospace;font-size:20px;display:flex;align-items:center;gap:14px}
.method{background:#56b8ac;color:#102831;padding:7px 10px;border-radius:6px;font-weight:700}
pre{margin:20px 0 0;font-family:monospace;font-size:18px;line-height:1.45;white-space:pre-wrap}
.stats{display:flex;gap:12px;margin:24px 0}.stat{flex:1;background:#fff;border-radius:12px;
padding:18px;border:1px solid #d6e2e6}.num{font-size:38px;font-weight:700}.label{font-size:16px;
color:#526b74;margin-top:5px}.split{display:grid;grid-template-columns:1.1fr 1fr;gap:18px}
.issue{background:#fff;border:1px solid #d6e2e6;border-radius:12px;padding:18px;margin-bottom:14px;
font-size:18px;line-height:1.4}.issue small{color:#59727a;font-size:14px}
.doc{width:896px;height:460px;object-fit:cover;object-position:top;border:1px solid #ccdce0;
border-radius:12px;background:white}.caption{font-size:18px;color:#42616b;margin-top:17px}
"""


def document(body: str) -> str:
    return (
        f"<!doctype html><html><head><meta charset='utf-8'><style>{CSS}</style></head>{body}</html>"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--output", type=Path, default=ROOT / "assets/api")
    parser.add_argument("--browser", type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    base = args.base_url.rstrip("/")
    request_data = (ROOT / "examples/api/request.json").read_bytes()
    request = Request(
        base + "/sales/validate", data=request_data, headers={"Content-Type": "application/json"}
    )
    with urlopen(request, timeout=10) as response:
        if response.status != 200:
            raise ValueError(f"Expected HTTP 200, received {response.status}")
        result = json.load(response)
    expected = json.loads((ROOT / "examples/api/response.json").read_text())
    if result != expected:
        raise ValueError(
            "Live response differs from the documented sample; inspect before capturing"
        )
    (output / "sample-response.json").write_text(json.dumps(result, indent=2) + "\n")
    stamp = datetime.now(timezone.utc).isoformat()
    (output / "capture-metadata.json").write_text(
        json.dumps(
            {"captured_at_utc": stamp, "data": "synthetic", "image_size": [2000, 1500]}, indent=2
        )
        + "\n"
    )
    summary = result["summary"]
    footer = "<footer class='footer'><span>Sample sales data</span><span>Python / FastAPI</span></footer>"
    cover = document(
        "<main><div class='eyebrow'>Python / FastAPI</div>"
        "<h1>Sales data<br><span class='accent'>validation API</span></h1>"
        "<div class='sub'>Checks fields, finds duplicates and returns a summary.</div>"
        "<div class='flow'><div class='node'>Sales records</div><span class='arrow'>→</span>"
        "<div class='node'>Validation</div><span class='arrow'>→</span>"
        "<div class='node'>Results & issues</div></div>"
        "<div class='dark route'><span class='method'>POST</span>/sales/validate</div>"
        "<div class='badges' style='margin-top:28px'><span class='badge'>JSON input / output</span>"
        "<span class='badge'>Request examples</span><span class='badge'>Automated tests</span></div>"
        + footer
        + "</main>"
    )
    stats = "".join(
        f"<div class='stat'><div class='num'>{summary[key]}</div><div class='label'>{label}</div></div>"
        for key, label in [
            ("input_records", "Input records"),
            ("valid_records", "Accepted"),
            ("rejected_records", "Rejected"),
            ("duplicates", "Duplicate"),
        ]
    )
    excerpt = html.escape(
        json.dumps({"totals_by_currency": result["totals_by_currency"]}, indent=2)
    )
    issues = "".join(
        f"<div class='issue'><small>Record {issue['row']} · {html.escape(issue['category'])}</small>"
        f"<div>{html.escape(issue['issue'])}</div></div>"
        for issue in result["issues"]
    )
    run = document(
        "<main><div class='eyebrow'>POST /sales/validate · HTTP 200</div>"
        "<h2>Sales validation results</h2>"
        f"<div class='stats'>{stats}</div><div class='split'>"
        f"<div class='dark'><div class='route'>Response excerpt</div><pre>{excerpt}</pre>"
        "<div style='margin-top:22px;color:#a2c9d2;font-size:16px'>Separate currency totals.<br>Exact decimal strings.</div></div>"
        f"<div>{issues}</div></div>" + footer + "</main>"
    )
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=str(args.browser) if args.browser else None
        )
        context = browser.new_context(
            viewport={"width": 1000, "height": 750}, device_scale_factor=2
        )
        page = context.new_page()
        page.goto(base + "/docs", wait_until="networkidle")
        page.locator(".swagger-ui .info .title").wait_for()
        page.screenshot(path=str(output / "swagger-raw.png"))
        docs = document(
            "<main><div class='eyebrow'>Interactive documentation</div>"
            "<h2>Available endpoints</h2>"
            "<img class='doc' src='swagger-raw.png' alt='Actual local API documentation'>"
            "<div class='caption'>Send a request from the browser and inspect the response.</div>"
            + footer
            + "</main>"
        )
        for filename, content in [
            ("01-service-cover", cover),
            ("02-sample-result", run),
            ("03-api-docs", docs),
        ]:
            path = output / f"{filename}.html"
            path.write_text(content)
            page.goto(path.as_uri(), wait_until="load")
            page.screenshot(path=str(output / f"{filename}.png"))
        browser.close()
    print(f"Captured three 2000×1500 PNG gallery images in {output}")


if __name__ == "__main__":
    main()

# API screenshots

These images show the sales validation endpoint and its output:

1. `01-service-cover.png` — what the endpoint does.
2. `02-sample-result.png` — actual sample response, counts, issues and currency totals.
3. `03-api-docs.png` — the API documentation in the browser.

Each image is 2000×1500 pixels (4:3). The sales records are fictional.

`swagger-raw.png` is the unframed documentation screenshot. `sample-response.json`
was fetched from the running API and checked against `examples/api/response.json`.
`capture-metadata.json` records when they were captured. The HTML files contain
the layouts used to render the images.

## Recreate

Start the API as described in [the demo guide](../../docs/api-demo.md), then run:

```bash
uv run --no-project --with playwright python -m playwright install chromium
uv run --no-project --with playwright python scripts/capture_api_gallery.py
```

Use `--browser /path/to/chromium` to select an existing browser, or `--output` to
save new captures outside this directory. Playwright is optional capture tooling,
not a runtime dependency of the API or CLI.

The image format follows the [Project Catalog gallery guidance](https://support.upwork.com/hc/en-us/articles/1500011309082-How-to-add-images-and-video-to-your-Project-Catalog-project)
consulted on October 14, 2026: PNG/JPEG under 10 MB, 4:3, maximum 4000 pixels per side.
These files do not imply marketplace approval.

# FastAPI gallery

The three numbered PNGs are presentation assets for the local portfolio demo:

1. `01-service-cover.png` — service overview.
2. `02-sample-result.png` — actual sample response, counts, issues and currency totals.
3. `03-api-docs.png` — screenshot of the running API documentation in a presentation frame.

Each image is 2000×1500 pixels (4:3). All example sales are synthetic. The figures
describe the sample request, not customer results, performance or freelancer revenue.

`swagger-raw.png` is the unframed documentation screenshot. `sample-response.json`
was fetched from the running API and checked against `examples/api/response.json`.
`capture-metadata.json` records capture time. HTML files are reproducible layouts,
not an additional application or claims about a client interface.

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

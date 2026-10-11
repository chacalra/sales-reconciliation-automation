# Silent portfolio demo — 75 seconds

## Existing video review

The original video is 75 seconds, 1600 × 900, H.264 at 24 fps, 622,494 bytes,
with no audio stream. Its sample metrics and file paths are correct. The high
contrast summary is clear at desktop size.

It uses six rendered slides rather than a live terminal and spreadsheet capture.
Some table text is too small for a small player, the opening is long, and there is
no test execution. The replacement follows seven scenes and gives the actual
report the longest screen time. Preserve the original until the replacement has
passed the shot-list review.

## Recording setup

- Capture only a clean, isolated desktop or application window.
- Use the included synthetic inputs and the fixed 2026-10-10 FX snapshot.
- Prepare with `bash scripts/run_demo.sh --prepare-only` in an activated Python
  environment installed as described in the README.
- Outputs go to `output/demo/`. The preparation leaves the normal `config.yaml`,
  cache, inputs, and portfolio examples unchanged.
- The recording command is deliberately offline so revenue is reproducible.
  The demo helper permits replay of the historical snapshot in its separate
  generated configuration; normal cache validation remains unchanged.
- Record the application and pytest output as it appears. Do not retype, filter,
  replace, or fabricate results for the recording.
- Open the actual workbooks in LibreOffice Calc or Excel. Import CSV columns as
  text to preserve literal dates and decimal separators. Change zoom, column
  widths, wrapping, and chart placement for readability without saving over the
  source files. Crop input shots to show the headers and a few rows clearly.
- Compose at 1920 × 1080, 24 fps, with a separate caption band. No audio track.
- Use direct cuts and simple cell selections; no decorative transitions.

## Timeline

Exact overlay wording is in [video_overlay_text.md](video_overlay_text.md).

| Time | Duration | Real screen content and action | Overlay / focus |
| --- | ---: | --- | --- |
| 00:00–00:03 | 3 s | Clean terminal: `ls -1 examples/input/`. Show the three filenames. | Three sources, different formats and currencies. |
| 00:03–00:08 | 5 s | Open Amazon CSV in Calc. Keep headers and a few USD rows visible. | Opening overlay stays on screen. |
| 00:08–00:11 | 3 s | Show Shopify XLSX headers and EUR line totals. | Manual consolidation and errors. |
| 00:11–00:14 | 3 s | Show Marketplace CSV headers, decimal commas, BRL and GBP. | Same short manual-work overlay. |
| 00:14–00:25 | 11 s | In a clean terminal, type and run the command below. Let the real logs finish. | Validate, normalize, deduplicate, convert, reconcile. |
| 00:25–00:33 | 8 s | Open `output/demo/report.xlsx` → Summary. Focus total revenue and counts. | USD 5,438.50. |
| 00:33–00:38 | 5 s | Keep Summary visible; select the input/valid/rejected/duplicate cells. | 89 = 76 + 8 + 5. |
| 00:38–00:44 | 6 s | Show the workbook's actual channel chart and channel totals. | Channel revenue and row accounting. |
| 00:44–00:48 | 4 s | Show the actual generated filenames in `output/demo/`. | Excel report, Sales CSV, Issues CSV. |
| 00:48–01:00 | 12 s | Open the Issues sheet. Select `invalid quantity`, then `invalid price/amount`. Include a real duplicate reason if legible. | Bad rows isolated; valid rows still processed. |
| 01:00–01:08 | 8 s | Clean terminal: run `pytest -q`. Show the real successful result. | Actual test count and covered failure modes. |
| 01:08–01:15 | 7 s | Return to Summary. Hold the result and repository URL. | Repetitive data workflows; Excel, CSV, REST APIs. |

Execution shown in scene 3:

```bash
python -m sales_automation --config output/demo/config.yaml --offline
```

The helper may be run without `--prepare-only` to prepare and execute in one step:

```bash
bash scripts/run_demo.sh
```

## Expected evidence

- 89 input rows, 76 accepted sales lines, 8 rejected rows, 5 duplicates.
- 75 distinct orders and USD 5,438.50 with the included snapshot.
- Channel revenue: Amazon USD 2,093.50; Shopify USD 1,404.97;
  Marketplace USD 1,940.03.
- Summary, Transactions, and Issues sheets plus both CSV exports.
- Real issue examples: `invalid quantity`, `invalid price/amount`, and duplicate
  transaction messages from the included dataset.
- The test count must come from the recorded `pytest -q`, not an old caption.

The video demonstrates validation of loaded records and reference-rate
conversion. It does not claim that every corrupt source or unavailable rate can
be recovered, or that this is historical accounting.

## Delivered video

- File: [demo.mp4](demo.mp4).
- 75 seconds; 1920 × 1080; 24 fps; H.264; 2,403,903 bytes.
- Real screen capture of Calc and a terminal, with English captions and no audio.
- Recorded test result: `84 passed in 1.72s`.
- Reviewed at full size and a 640-pixel-wide player. All 1,800 frames passed the
  automated OCR privacy scan; representative shots were also inspected visually.
- The original slide video and source recordings are preserved locally outside
  the public assets. No application engine code was changed.

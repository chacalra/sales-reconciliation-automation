# Recording checklist

Completed for the delivered `demo.mp4`. Uncheck these items when recording a new take.

## Prepare

- [x] Activate the project environment with dependencies installed.
- [x] Use an isolated desktop; keep personal windows and notifications outside capture.
- [x] Use a neutral recording location and a prompt without a username or home path.
- [x] Set capture to 1920 × 1080, 24 fps; disable microphone and system audio.
- [x] Run `bash scripts/run_demo.sh --prepare-only`.
- [x] Open only the three files in `examples/input/` and the generated demo report.
- [x] Use an English application UI, large fonts, and a readable spreadsheet zoom.
- [x] Keep captions outside the actual application content.

## Capture in order

- [x] 00:00 — Run `ls -1 examples/input/`; show all three filenames.
- [x] 00:03 — Amazon CSV: headers, quantities, unit prices, USD.
- [x] 00:08 — Shopify XLSX: different headers, line totals, EUR.
- [x] 00:11 — Marketplace CSV: decimal commas and BRL/GBP.
- [x] 00:14 — Clean terminal; type the exact command from `video_script.md`.
- [x] Wait for genuine `Reconciliation PASS` and `Total revenue: 5438.50 USD`.
- [x] 00:25 — Open `output/demo/report.xlsx` → Summary; focus revenue.
- [x] 00:33 — Highlight the four record counts without changing any cells.
- [x] 00:38 — Show actual channel totals and the workbook chart.
- [x] 00:44 — Show `report.xlsx`, `consolidated_sales.csv`, and `issues.csv` filenames.
- [x] 00:48 — Issues: select `invalid quantity`, then `invalid price/amount`.
- [x] Show one duplicate reason if it fits without shrinking the font.
- [x] 01:00 — Run `pytest -q`; keep the genuine final result visible.
- [x] 01:08 — Return to Summary; hold the repository URL through 01:15.

## Edit and check

- [x] Apply only the exact captions from `video_overlay_text.md`.
- [x] Use direct cuts; preserve the real execution and test output.
- [x] Do not accelerate the command execution or hide a failure.
- [x] Verify revenue, row counts, and the recorded test count.
- [x] Review every shot and transition, including the terminal's wrapped lines.
- [x] Inspect at normal size and at a 640-pixel-wide player.
- [x] Check all visible pixels for personal paths, private files, tokens, and prompts.
- [x] Confirm no `proyecto/`, `.env`, private history, or personal notification appears.
- [x] Confirm there is no audio stream, voice, or music.
- [x] Verify 60–75 seconds, H.264, 1920 × 1080, and browser-friendly MP4.
- [x] Preserve the original before replacing `assets/demo.mp4`.

Only synthetic input files, generated demo outputs, a neutral terminal, and test
results belong in the recording. Zoom and cell selection are fine; fabricated
application output is not.

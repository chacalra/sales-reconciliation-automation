#!/usr/bin/env bash
set -euo pipefail

if [[ $# -gt 1 || ($# -eq 1 && "$1" != "--prepare-only") ]]; then
    echo "Usage: bash scripts/run_demo.sh [--prepare-only]" >&2
    exit 2
fi

repo_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_dir"

python - <<'PY'
import json
import shutil
from datetime import date
from pathlib import Path

import yaml

root = Path.cwd()
demo = root / "output" / "demo"
demo.mkdir(parents=True, exist_ok=True)
config = yaml.safe_load((root / "config.example.yaml").read_text(encoding="utf-8"))
snapshot = root / "examples" / "exchange_rates.json"
dates = [date.fromisoformat(value) for value in json.loads(snapshot.read_text())["dates"].values()]
if not dates or any(value > date.today() for value in dates):
    raise SystemExit("The demo snapshot must have nonempty, nonfuture reference dates.")

# Allow replay of this historical example without weakening the normal configuration.
config["exchange_rates"]["max_cache_age_days"] = max(14, (date.today() - min(dates)).days)
config["exchange_rates"]["cache_file"] = str(demo / "exchange_rates.json")
config["output_dir"] = str(demo)
for source in config["sources"].values():
    source["file"] = str(root / source["file"])
shutil.copyfile(snapshot, demo / "exchange_rates.json")
(demo / "config.yaml").write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
print(f"Historical demo FX snapshot: {min(dates)}. This is not a current-rate run.")
print("Prepared output/demo/config.yaml; local config.yaml and normal cache are unchanged.")
PY

if [[ "${1:-}" == "--prepare-only" ]]; then
    echo "Next: python -m sales_automation --config output/demo/config.yaml --offline"
else
    python -m sales_automation --config output/demo/config.yaml --offline
fi

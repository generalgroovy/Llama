from __future__ import annotations

import argparse
import json
from pathlib import Path

from sds_eval.metrics.metric_registry import compute_all_metrics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", required=True)
    parser.add_argument("--out")
    args = parser.parse_args()
    data = json.loads(Path(args.run).read_text(encoding="utf-8"))
    runs = data.get("runs", [data])
    for run in runs:
        run["metrics"] = compute_all_metrics(run)
    output = data if "runs" in data else runs[0]
    text = json.dumps(output, indent=2)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(text, encoding="utf-8")
    else:
        print(text)


if __name__ == "__main__":
    main()

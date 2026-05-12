from __future__ import annotations

import argparse
from pathlib import Path

from sds_eval.experiments.runner import run_experiment, write_experiment_result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("configs", nargs="+")
    parser.add_argument("--out-dir", default="data/runs")
    args = parser.parse_args()
    for config in args.configs:
        result = run_experiment(config)
        out = Path(args.out_dir) / f"{result['experiment']['experiment_id']}.json"
        write_experiment_result(result, out)
        print(f"wrote {len(result['runs'])} runs to {out}")


if __name__ == "__main__":
    main()

from __future__ import annotations

import argparse

from sds_eval.experiments.runner import run_experiment, write_experiment_result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    result = run_experiment(args.config)
    write_experiment_result(result, args.out)
    print(f"wrote {len(result['runs'])} runs to {args.out}")


if __name__ == "__main__":
    main()

from __future__ import annotations

import argparse

from sds_eval.analysis.export_web import export_web_data


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", nargs="+", required=True)
    parser.add_argument("--out", default="web/public/data")
    args = parser.parse_args()
    summary = export_web_data(args.runs, args.out)
    print(f"exported {summary['runs']} runs to {summary['out_dir']}")


if __name__ == "__main__":
    main()

from __future__ import annotations

import argparse
from pathlib import Path

from sds_eval.experiments.runner import run_experiment, write_experiment_result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("configs", nargs="+")
    parser.add_argument("--out-dir", default="data/runs")
    parser.add_argument("--enable-asr", action="store_true")
    parser.add_argument("--enable-tts", action="store_true")
    parser.add_argument("--audio-dir", default=None)
    args = parser.parse_args()
    speech_pipeline = {}
    if args.enable_asr:
        speech_pipeline.setdefault("asr", {})["enabled"] = True
    if args.enable_tts:
        speech_pipeline.setdefault("tts", {})["enabled"] = True
    if args.audio_dir:
        speech_pipeline["audio_dir"] = args.audio_dir
    for config in args.configs:
        result = run_experiment(config, {"speech_pipeline": speech_pipeline})
        out = Path(args.out_dir) / f"{result['experiment']['experiment_id']}.json"
        write_experiment_result(result, out)
        print(f"wrote {len(result['runs'])} runs to {out}")


if __name__ == "__main__":
    main()

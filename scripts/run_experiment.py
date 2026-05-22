from __future__ import annotations

import argparse

from sds_eval.experiments.runner import run_experiment, write_experiment_result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--out", required=True)
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
    result = run_experiment(args.config, {"speech_pipeline": speech_pipeline})
    write_experiment_result(result, args.out)
    print(f"wrote {len(result['runs'])} runs to {args.out}")


if __name__ == "__main__":
    main()

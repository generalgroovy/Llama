from __future__ import annotations

import argparse

from sds_eval.experiments.runner import run_experiment, write_experiment_result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--enable-asr", action="store_true")
    parser.add_argument("--enable-tts", action="store_true")
    parser.add_argument("--speech", action="store_true", help="Enable both deterministic TTS and audio-backed ASR.")
    parser.add_argument("--asr-word-error-rate", type=float, default=None)
    parser.add_argument("--speech-rate-wpm", type=int, default=None)
    parser.add_argument("--max-speech-duration", type=float, default=None)
    parser.add_argument("--measure-latency", action="store_true")
    parser.add_argument("--audio-dir", default=None)
    args = parser.parse_args()
    speech_pipeline = {}
    if args.speech or args.enable_asr:
        speech_pipeline.setdefault("asr", {})["enabled"] = True
    if args.speech or args.enable_tts:
        speech_pipeline.setdefault("tts", {})["enabled"] = True
    if args.asr_word_error_rate is not None:
        speech_pipeline.setdefault("asr", {})["word_error_rate"] = args.asr_word_error_rate
    if args.speech_rate_wpm is not None:
        speech_pipeline.setdefault("tts", {})["speech_rate_wpm"] = args.speech_rate_wpm
    if args.max_speech_duration is not None:
        speech_pipeline.setdefault("tts", {})["max_duration_seconds"] = args.max_speech_duration
    if args.measure_latency:
        speech_pipeline["measure_latency"] = True
    if args.audio_dir:
        speech_pipeline["audio_dir"] = args.audio_dir
    result = run_experiment(args.config, {"speech_pipeline": speech_pipeline})
    write_experiment_result(result, args.out)
    print(f"wrote {len(result['runs'])} runs to {args.out}")


if __name__ == "__main__":
    main()

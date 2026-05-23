from __future__ import annotations

import json
import math
import re
import wave
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Any

from sds_eval.agents.base import AgentResponse


def default_pipeline_config() -> dict[str, Any]:
    return {
        "asr": {"enabled": False, "backend": "transcript_sidecar", "word_error_rate": 0.0, "require_audio": False},
        "nlu": {"enabled": True, "confidence": 1.0},
        "dialog_management": {"enabled": True},
        "nlg": {"enabled": True},
        "tts": {
            "enabled": False,
            "backend": "synthetic_wave",
            "sample_rate": 16000,
            "voice": "synthetic-dialogue",
            "speech_rate_wpm": 185,
            "min_duration_seconds": 0.55,
            "max_duration_seconds": 3.5,
            "write_transcript_sidecar": True,
        },
        "measure_latency": False,
        "record_audio": True,
        "audio_dir": "data/audio",
    }


def merge_pipeline_config(base: dict[str, Any] | None = None, overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    merged = default_pipeline_config()
    _deep_update(merged, base or {})
    _deep_update(merged, overrides or {})
    return merged


@dataclass
class PipelineResult:
    text: str
    spoken_text: str
    recognized_text: str
    events: list[dict[str, Any]]
    audio_path: str | None
    audio_sidecar_path: str | None
    audio_duration_seconds: float


class SpeechPipeline:
    """Deterministic research pipeline for ASR/NLU/DM/NLG/TTS phase logging."""

    def __init__(self, config: dict[str, Any], run_id: str):
        self.config = merge_pipeline_config(config)
        self.run_id = run_id
        self.audio_dir = Path(self.config.get("audio_dir", "data/audio")) / run_id

    def process_turn(self, turn_id: int, speaker: str, response: AgentResponse) -> PipelineResult:
        events: list[dict[str, Any]] = []
        dm_event = _event("dialog_management", True, {
            "dialogue_act": response.metadata.get("dialogue_act"),
            "intent": response.metadata.get("intent"),
            "selected_action": response.interpreted_action,
            "semantic_payload": _compact_metadata(response.metadata),
        })
        events.append(dm_event)

        nlg_text, spoken_text, nlg_event = self._nlg(response.text, response.metadata)
        events.append(nlg_event)
        audio_path, sidecar_path, duration, tts_event = self._tts(turn_id, speaker, spoken_text)
        events.append(tts_event)
        recognized_text, asr_event = self._asr(spoken_text, audio_path, sidecar_path)
        events.append(asr_event)
        events.append(self._nlu(recognized_text, response.metadata))
        return PipelineResult(
            text=nlg_text,
            spoken_text=spoken_text,
            recognized_text=recognized_text,
            events=events,
            audio_path=audio_path,
            audio_sidecar_path=sidecar_path,
            audio_duration_seconds=duration,
        )

    def _nlg(self, text: str, metadata: dict[str, Any]) -> tuple[str, str, dict[str, Any]]:
        start = self._latency_start()
        enabled = bool(self.config.get("nlg", {}).get("enabled", True))
        output = text if enabled else str(metadata.get("dialogue_act", ""))
        spoken = _spoken_form(output)
        return output, spoken, _event("nlg", enabled, {
            "text": output,
            "spoken_text": spoken,
            "token_count": len(output.split()),
            "spoken_token_count": len(spoken.split()),
        }, start)

    def _tts(self, turn_id: int, speaker: str, text: str) -> tuple[str | None, str | None, float, dict[str, Any]]:
        start = self._latency_start()
        tts_config = self.config.get("tts", {})
        enabled = bool(tts_config.get("enabled", False)) and bool(self.config.get("record_audio", True))
        if not enabled:
            return None, None, 0.0, _event("tts", False, {"audio_path": None, "duration_seconds": 0.0}, start)
        sample_rate = int(tts_config.get("sample_rate", 16000))
        duration = _estimate_duration_seconds(text, tts_config)
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        safe_speaker = "".join(ch if ch.isalnum() else "_" for ch in speaker)
        path = self.audio_dir / f"turn_{turn_id:03d}_{safe_speaker}.wav"
        _write_speech_like_wave(path, text, duration, sample_rate, 440 + (turn_id % 5) * 55)
        sidecar_path = _write_sidecar(path, {
            "turn_id": turn_id,
            "speaker": speaker,
            "text": text,
            "duration_seconds": duration,
            "sample_rate": sample_rate,
            "voice": tts_config.get("voice", "synthetic-dialogue"),
            "backend": tts_config.get("backend", "synthetic_wave"),
            "word_count": len(text.split()),
        }) if bool(tts_config.get("write_transcript_sidecar", True)) else None
        return str(path), sidecar_path, duration, _event("tts", True, {
            "audio_path": str(path),
            "sidecar_path": sidecar_path,
            "duration_seconds": duration,
            "sample_rate": sample_rate,
            "voice": tts_config.get("voice", "synthetic-dialogue"),
            "backend": tts_config.get("backend", "synthetic_wave"),
            "speech_rate_wpm": int(tts_config.get("speech_rate_wpm", 185)),
        }, start)

    def _asr(self, text: str, audio_path: str | None, sidecar_path: str | None) -> tuple[str, dict[str, Any]]:
        start = self._latency_start()
        asr_config = self.config.get("asr", {})
        enabled = bool(asr_config.get("enabled", False))
        source = "text_channel"
        input_text = text
        if enabled and audio_path:
            sidecar_text = _read_sidecar_text(sidecar_path or str(Path(audio_path).with_suffix(".json")))
            if sidecar_text is not None:
                input_text = sidecar_text
                source = "audio_transcript_sidecar"
            else:
                source = "audio_without_transcript"
        elif enabled and asr_config.get("require_audio", False):
            input_text = ""
            source = "missing_audio"
        word_error_rate = float(asr_config.get("word_error_rate", 0.0))
        recognized = _apply_word_error(input_text, word_error_rate) if enabled else input_text
        confidence = max(0.0, 1.0 - word_error_rate) if enabled else 1.0
        return recognized, _event("asr", enabled, {
            "recognized_text": recognized,
            "confidence": confidence,
            "audio_path": audio_path,
            "sidecar_path": sidecar_path,
            "source": source,
            "backend": asr_config.get("backend", "transcript_sidecar"),
            "word_error_rate": word_error_rate,
        }, start)

    def _nlu(self, text: str, metadata: dict[str, Any]) -> dict[str, Any]:
        start = self._latency_start()
        enabled = bool(self.config.get("nlu", {}).get("enabled", True))
        confidence = float(self.config.get("nlu", {}).get("confidence", 1.0)) if enabled else 1.0
        return _event("nlu", enabled, {
            "recognized_intent": metadata.get("intent"),
            "recognized_dialogue_act": metadata.get("dialogue_act"),
            "confidence": confidence,
            "text": text,
        }, start)

    def _latency_start(self) -> float | None:
        return perf_counter() if bool(self.config.get("measure_latency", False)) else None


def _event(phase: str, enabled: bool, payload: dict[str, Any], start: float | None = None) -> dict[str, Any]:
    latency = 0.0 if start is None else (perf_counter() - start) * 1000
    return {
        "phase": phase,
        "enabled": enabled,
        "latency_ms": round(latency, 3),
        "payload": payload,
    }


def _deep_update(target: dict[str, Any], source: dict[str, Any]) -> None:
    for key, value in source.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            _deep_update(target[key], value)
        else:
            target[key] = value


def _compact_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in metadata.items()
        if key in {"dialogue_act", "intent", "route_advice", "route_segments", "interpreted_goal", "interpreted_constraints"}
    }


def _spoken_form(text: str) -> str:
    spoken = text.replace("->", " to ")
    spoken = spoken.replace("Route request:", "")
    spoken = spoken.replace("Constraints:", "Need")
    spoken = spoken.replace("avoid_blocked", "avoid blocked")
    spoken = spoken.replace("prefer_shortest", "shortest")
    spoken = spoken.replace(";", ". Then ")
    spoken = re.sub(r"\b([A-Za-z][A-Za-z0-9]*)\s*:", r"line \1 from", spoken)
    spoken = re.sub(r"\b(Board|board)\s+([A-Za-z][A-Za-z0-9]*)\s+at\b", r"\1 line \2 at", spoken)
    spoken = re.sub(r"\bchange to\s+(?!line\b)([A-Za-z][A-Za-z0-9]*)\s+at\b", r"change to line \1 at", spoken)
    while "  " in spoken:
        spoken = spoken.replace("  ", " ")
    return spoken.strip()


def _estimate_duration_seconds(text: str, tts_config: dict[str, Any]) -> float:
    words = max(1, len(text.split()))
    speech_rate = max(120, int(tts_config.get("speech_rate_wpm", 185)))
    min_duration = float(tts_config.get("min_duration_seconds", 0.55))
    max_duration = float(tts_config.get("max_duration_seconds", 3.5))
    punctuation_pause = 0.08 * sum(text.count(mark) for mark in ".?!")
    duration = words / speech_rate * 60 + punctuation_pause
    return round(max(min_duration, min(max_duration, duration)), 3)


def _write_sidecar(path: Path, payload: dict[str, Any]) -> str:
    sidecar = path.with_suffix(".json")
    sidecar.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return str(sidecar)


def _read_sidecar_text(path: str | None) -> str | None:
    if not path:
        return None
    sidecar = Path(path)
    if not sidecar.exists():
        return None
    try:
        payload = json.loads(sidecar.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    text = payload.get("text")
    return text if isinstance(text, str) else None


def _write_speech_like_wave(path: Path, text: str, duration: float, sample_rate: int, frequency: int) -> None:
    frames = int(duration * sample_rate)
    amplitude = 9000
    word_boundaries = max(1, len(text.split()))
    with wave.open(str(path), "w") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        for index in range(frames):
            time = index / sample_rate
            progress = index / max(1, frames - 1)
            envelope = min(1.0, progress * 18, (1.0 - progress) * 18)
            syllable = 1.0 + 0.08 * math.sin(2 * math.pi * word_boundaries * time / max(duration, 0.001))
            formant = (
                math.sin(2 * math.pi * frequency * time)
                + 0.35 * math.sin(2 * math.pi * (frequency * 1.8) * time)
                + 0.18 * math.sin(2 * math.pi * (frequency * 2.6) * time)
            )
            value = int(amplitude * envelope * syllable * formant / 1.53)
            handle.writeframesraw(value.to_bytes(2, byteorder="little", signed=True))


def _apply_word_error(text: str, word_error_rate: float) -> str:
    if word_error_rate <= 0:
        return text
    words = text.split()
    if not words:
        return text
    interval = max(1, round(1 / min(word_error_rate, 1.0)))
    return " ".join(word for idx, word in enumerate(words, start=1) if idx % interval != 0)

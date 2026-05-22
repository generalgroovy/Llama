from __future__ import annotations

import math
import wave
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Any

from sds_eval.agents.base import AgentResponse


def default_pipeline_config() -> dict[str, Any]:
    return {
        "asr": {"enabled": False, "word_error_rate": 0.0},
        "nlu": {"enabled": True, "confidence": 1.0},
        "dialog_management": {"enabled": True},
        "nlg": {"enabled": True},
        "tts": {"enabled": False, "sample_rate": 16000, "voice": "synthetic-tone"},
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
    recognized_text: str
    events: list[dict[str, Any]]
    audio_path: str | None
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

        nlg_text, nlg_event = self._nlg(response.text, response.metadata)
        events.append(nlg_event)
        audio_path, duration, tts_event = self._tts(turn_id, speaker, nlg_text)
        events.append(tts_event)
        recognized_text, asr_event = self._asr(nlg_text, audio_path)
        events.append(asr_event)
        events.append(self._nlu(recognized_text, response.metadata))
        return PipelineResult(
            text=nlg_text,
            recognized_text=recognized_text,
            events=events,
            audio_path=audio_path,
            audio_duration_seconds=duration,
        )

    def _nlg(self, text: str, metadata: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        start = perf_counter()
        enabled = bool(self.config.get("nlg", {}).get("enabled", True))
        output = text if enabled else str(metadata.get("dialogue_act", ""))
        return output, _event("nlg", enabled, {"text": output, "token_count": len(output.split())}, start)

    def _tts(self, turn_id: int, speaker: str, text: str) -> tuple[str | None, float, dict[str, Any]]:
        start = perf_counter()
        tts_config = self.config.get("tts", {})
        enabled = bool(tts_config.get("enabled", False)) and bool(self.config.get("record_audio", True))
        if not enabled:
            return None, 0.0, _event("tts", False, {"audio_path": None, "duration_seconds": 0.0}, start)
        sample_rate = int(tts_config.get("sample_rate", 16000))
        duration = max(0.25, min(4.0, len(text.split()) * 0.18))
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        safe_speaker = "".join(ch if ch.isalnum() else "_" for ch in speaker)
        path = self.audio_dir / f"turn_{turn_id:03d}_{safe_speaker}.wav"
        _write_tone(path, duration, sample_rate, 440 + (turn_id % 5) * 55)
        return str(path), duration, _event("tts", True, {"audio_path": str(path), "duration_seconds": duration, "voice": tts_config.get("voice", "synthetic-tone")}, start)

    def _asr(self, text: str, audio_path: str | None) -> tuple[str, dict[str, Any]]:
        start = perf_counter()
        asr_config = self.config.get("asr", {})
        enabled = bool(asr_config.get("enabled", False))
        recognized = _apply_word_error(text, float(asr_config.get("word_error_rate", 0.0))) if enabled else text
        confidence = max(0.0, 1.0 - float(asr_config.get("word_error_rate", 0.0))) if enabled else 1.0
        return recognized, _event("asr", enabled, {"recognized_text": recognized, "confidence": confidence, "audio_path": audio_path}, start)

    def _nlu(self, text: str, metadata: dict[str, Any]) -> dict[str, Any]:
        start = perf_counter()
        enabled = bool(self.config.get("nlu", {}).get("enabled", True))
        confidence = float(self.config.get("nlu", {}).get("confidence", 1.0)) if enabled else 1.0
        return _event("nlu", enabled, {
            "recognized_intent": metadata.get("intent"),
            "recognized_dialogue_act": metadata.get("dialogue_act"),
            "confidence": confidence,
            "text": text,
        }, start)


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


def _write_tone(path: Path, duration: float, sample_rate: int, frequency: int) -> None:
    frames = int(duration * sample_rate)
    amplitude = 9000
    with wave.open(str(path), "w") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        for index in range(frames):
            value = int(amplitude * math.sin(2 * math.pi * frequency * index / sample_rate))
            handle.writeframesraw(value.to_bytes(2, byteorder="little", signed=True))


def _apply_word_error(text: str, word_error_rate: float) -> str:
    if word_error_rate <= 0:
        return text
    words = text.split()
    if not words:
        return text
    interval = max(1, round(1 / min(word_error_rate, 1.0)))
    return " ".join(word for idx, word in enumerate(words, start=1) if idx % interval != 0)

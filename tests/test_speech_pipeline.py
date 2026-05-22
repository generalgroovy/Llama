from pathlib import Path

from sds_eval.agents import RuleAgent, UserLMAgent
from sds_eval.dialogue.manager import DialogueManager
from sds_eval.dialogue.transcript import validate_transcript
from sds_eval.task.navigation_env import NavigationEnvironment, NavigationMap


def test_pipeline_phases_are_logged_with_speech_off():
    transcript = _run_transcript({"tts": {"enabled": False}, "asr": {"enabled": False}})
    validate_transcript(transcript)
    first_turn = transcript["turns"][0]
    phases = [event["phase"] for event in first_turn["pipeline_events"]]
    assert phases == ["dialog_management", "nlg", "tts", "asr", "nlu"]
    assert first_turn["audio_path"] is None
    assert transcript["audio_recordings"] == []


def test_tts_runtime_toggle_creates_wav_audio(tmp_path):
    audio_dir = tmp_path / "audio"
    transcript = _run_transcript({"tts": {"enabled": True}, "asr": {"enabled": True}, "audio_dir": str(audio_dir)})
    assert transcript["audio_recordings"]
    first_audio = Path(transcript["audio_recordings"][0]["audio_path"])
    assert first_audio.exists()
    assert first_audio.suffix == ".wav"
    assert transcript["metrics"]["tts_audio_coverage"] > 0


def _run_transcript(speech_pipeline):
    nav_map = NavigationMap(
        "m",
        2,
        1,
        (0, 0),
        (1, 0),
        landmarks={"Alpha": (0, 0), "Bravo": (1, 0)},
        stations={"Alpha": (0, 0), "Bravo": (1, 0)},
        transit_lines={"R": [(0, 0), (1, 0)]},
    )
    manager = DialogueManager(
        UserLMAgent(),
        RuleAgent(),
        NavigationEnvironment(nav_map),
        "exp",
        "run",
        1,
        {"parameters": {}, "speech_pipeline": speech_pipeline},
    )
    return manager.run()

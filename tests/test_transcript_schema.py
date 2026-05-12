from sds_eval.agents import RuleAgent, UserLMAgent
from sds_eval.dialogue.manager import DialogueManager
from sds_eval.dialogue.transcript import validate_transcript
from sds_eval.task.navigation_env import NavigationEnvironment, NavigationMap


def test_transcript_contains_required_schema_fields():
    manager = DialogueManager(
        UserLMAgent(),
        RuleAgent(),
        NavigationEnvironment(NavigationMap("m", 3, 3, (0, 0), (1, 0))),
        "exp",
        "run",
        1,
        {"parameters": {}},
    )
    transcript = manager.run()
    validate_transcript(transcript)
    assert transcript["success"]
    assert transcript["state_trace"]
    assert transcript["action_trace"]

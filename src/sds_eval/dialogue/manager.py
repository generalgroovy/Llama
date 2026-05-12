from __future__ import annotations

from dataclasses import asdict

from sds_eval.agents.base import AgentAdapter, AgentContext
from sds_eval.dialogue.state import DialogueState
from sds_eval.metrics.metric_registry import compute_all_metrics
from sds_eval.task.navigation_env import NavigationEnvironment


class DialogueManager:
    def __init__(
        self,
        agent_a: AgentAdapter,
        agent_b: AgentAdapter,
        environment: NavigationEnvironment,
        experiment_id: str,
        run_id: str,
        seed: int,
        config: dict,
        max_turns: int = 20,
        max_invalid_moves: int = 3,
    ):
        self.agent_a = agent_a
        self.agent_b = agent_b
        self.environment = environment
        self.experiment_id = experiment_id
        self.run_id = run_id
        self.seed = seed
        self.config = config
        self.max_turns = max_turns
        self.max_invalid_moves = max_invalid_moves

    def run(self) -> dict:
        self.agent_a.reset(self.seed)
        self.agent_b.reset(self.seed)
        state = DialogueState()
        turns: list[dict] = []
        action_trace: list[dict] = []
        state_trace: list[dict] = [self.environment.reset()]
        task = self.environment.map.to_dict()
        last_instruction: str | None = None

        while state.turn_id < self.max_turns and not self.environment.state()["success"]:
            context = AgentContext(
                experiment_id=self.experiment_id,
                run_id=self.run_id,
                turn_id=state.turn_id,
                state=self.environment.state(),
                task=task,
                history=turns,
                last_instruction=last_instruction,
                parameters=self.config.get("parameters", {}),
            )
            user_response = self.agent_a.respond(context)
            last_instruction = user_response.text
            turns.append(_turn(state.turn_id, self.agent_a.name, user_response.text, user_response.interpreted_action, self.environment.state(), self.environment.state(), True, False))
            state.turn_id += 1

            context.turn_id = state.turn_id
            context.history = turns
            context.last_instruction = last_instruction
            sds_response = self.agent_b.respond(context)
            action = sds_response.interpreted_action or "clarify"
            step = self.environment.apply_action(action)
            if not step.valid_action:
                state.invalid_moves += 1
                state.errors.append(step.error or "invalid action")
            is_repair = action == "clarify" or not step.valid_action
            turns.append(_turn(state.turn_id, self.agent_b.name, sds_response.text, action, step.state_before, step.state_after, step.valid_action, is_repair))
            action_trace.append(asdict(step))
            state_trace.append(step.state_after)
            state.turn_id += 1

            if action == "stop" or state.invalid_moves >= self.max_invalid_moves:
                break

        transcript = {
            "run_id": self.run_id,
            "experiment_id": self.experiment_id,
            "seed": self.seed,
            "config": self.config,
            "agent_a": self.agent_a.describe(),
            "agent_b": self.agent_b.describe(),
            "task": task,
            "turns": turns,
            "state_trace": state_trace,
            "action_trace": action_trace,
            "final_state": self.environment.state(),
            "success": self.environment.state()["success"],
            "errors": state.errors,
            "metrics": {},
        }
        transcript["metrics"] = compute_all_metrics(transcript)
        return transcript


def _turn(
    turn_id: int,
    speaker: str,
    text: str,
    action: str | None,
    before: dict,
    after: dict,
    valid: bool,
    repair: bool,
) -> dict:
    return {
        "turn_id": turn_id,
        "speaker": speaker,
        "text": text,
        "interpreted_action": action,
        "state_before": before,
        "state_after": after,
        "valid_action": valid,
        "repair_or_clarification": repair,
    }

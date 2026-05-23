from __future__ import annotations

from dataclasses import asdict
from typing import Any

from sds_eval.agents.base import AgentAdapter, AgentContext
from sds_eval.analysis.explanations import analyze_run
from sds_eval.dialogue.state import DialogueState
from sds_eval.experiments.profiles import resolve_system_profile
from sds_eval.metrics.metric_registry import compute_all_metrics
from sds_eval.pipeline import SpeechPipeline, merge_pipeline_config
from sds_eval.task.navigation_env import NavigationEnvironment
from sds_eval.task.planner import path_length, route_advice_text, shortest_path, station_label, summarize_route_segments


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
        max_turns: int | None = None,
        max_invalid_moves: int | None = None,
    ):
        self.agent_a = agent_a
        self.agent_b = agent_b
        self.environment = environment
        self.experiment_id = experiment_id
        self.run_id = run_id
        self.seed = seed
        self.config = config
        self.system_profile = resolve_system_profile(
            config.get("system_profile", "low"),
            {
                "max_turns": max_turns,
                "max_invalid_moves": max_invalid_moves,
                **config.get("system_profile_overrides", {}),
            },
        )
        self.max_turns = int(self.system_profile["max_turns"])
        self.max_invalid_moves = int(self.system_profile["max_invalid_moves"])

    def run(self) -> dict:
        self.agent_a.reset(self.seed)
        self.agent_b.reset(self.seed)
        dialogue_state = DialogueState()
        turns: list[dict[str, Any]] = []
        action_trace: list[dict[str, Any]] = []
        state_trace: list[dict[str, Any]] = [self.environment.reset()]
        audio_recordings: list[dict[str, Any]] = []
        task = self.environment.map.to_dict()
        params = {
            **self.config.get("parameters", {}),
            "prompt_policy": self.config.get("prompt_policy", {}),
        }
        speech_pipeline_config = merge_pipeline_config(self.config.get("speech_pipeline", {}))
        speech_pipeline = SpeechPipeline(speech_pipeline_config, self.run_id)
        agent_a_private = _agent_a_private_knowledge(task, params)
        agent_b_private = _agent_b_private_knowledge(task)
        shared_state = {
            "b_belief": {},
            "known_goal": None,
            "known_constraints": [],
            "secondary_constraints_requested": False,
            "agreed_plan": [],
            "unresolved_ambiguities": 0,
        }
        last_instruction: str | None = None

        while dialogue_state.turn_id < self.max_turns and not self.environment.state()["success"]:
            agent_a_context = AgentContext(
                experiment_id=self.experiment_id,
                run_id=self.run_id,
                turn_id=dialogue_state.turn_id,
                state=_public_state(self.environment.state()),
                history=turns,
                last_instruction=last_instruction,
                parameters=params,
                private_context=agent_a_private,
                shared_state=shared_state,
                speaker_role="agent_a",
                system_profile=self.system_profile,
            )
            user_response = self.agent_a.respond(agent_a_context)
            user_pipeline = speech_pipeline.process_turn(dialogue_state.turn_id, self.agent_a.name, user_response)
            if user_pipeline.audio_path:
                audio_recordings.append(_audio_record(dialogue_state.turn_id, self.agent_a.name, user_pipeline))
            last_instruction = user_pipeline.recognized_text
            user_metadata = {
                **user_response.metadata,
                "pipeline_events": user_pipeline.events,
                "spoken_text": user_pipeline.spoken_text,
                "recognized_text": user_pipeline.recognized_text,
                "audio_path": user_pipeline.audio_path,
                "audio_sidecar_path": user_pipeline.audio_sidecar_path,
                "audio_duration_seconds": user_pipeline.audio_duration_seconds,
            }
            turns.append(_turn(dialogue_state.turn_id, self.agent_a.name, user_pipeline.text, None, self.environment.state(), self.environment.state(), True, user_metadata))
            if user_response.metadata.get("mentioned_constraints"):
                shared_state["secondary_constraints_requested"] = True
            dialogue_state.turn_id += 1

            agent_b_private["current_position"] = self.environment.state()["position"]
            agent_b_context = AgentContext(
                experiment_id=self.experiment_id,
                run_id=self.run_id,
                turn_id=dialogue_state.turn_id,
                state=self.environment.state(),
                history=turns,
                last_instruction=last_instruction,
                parameters=params,
                private_context=agent_b_private,
                shared_state=shared_state,
                speaker_role="agent_b",
                system_profile=self.system_profile,
            )
            sds_response = self.agent_b.respond(agent_b_context)
            sds_pipeline = speech_pipeline.process_turn(dialogue_state.turn_id, self.agent_b.name, sds_response)
            if sds_pipeline.audio_path:
                audio_recordings.append(_audio_record(dialogue_state.turn_id, self.agent_b.name, sds_pipeline))
            shared_state["b_belief"] = dict(sds_response.metadata.get("belief_state_after", shared_state.get("b_belief", {})))
            shared_state["known_goal"] = shared_state["b_belief"].get("goal")
            shared_state["known_constraints"] = shared_state["b_belief"].get("constraints", [])
            shared_state["agreed_plan"] = sds_response.metadata.get("route_plan", [])
            shared_state["route_segments"] = sds_response.metadata.get("route_segments", [])
            shared_state["route_advice"] = sds_response.metadata.get("route_advice")
            if sds_response.metadata.get("ambiguity_detected"):
                shared_state["unresolved_ambiguities"] += 1

            action = sds_response.interpreted_action or "clarify"
            step = self.environment.apply_action(action)
            if not step.valid_action:
                dialogue_state.invalid_moves += 1
                dialogue_state.errors.append(step.error or "invalid action")
            action_metadata = {
                **sds_response.metadata,
                "pipeline_events": sds_pipeline.events,
                "spoken_text": sds_pipeline.spoken_text,
                "recognized_text": sds_pipeline.recognized_text,
                "audio_path": sds_pipeline.audio_path,
                "audio_sidecar_path": sds_pipeline.audio_sidecar_path,
                "audio_duration_seconds": sds_pipeline.audio_duration_seconds,
                "selected_action": action,
                "constraint_satisfied": sds_response.metadata.get("constraint_satisfied", step.valid_action),
                "repair_or_clarification": action == "clarify" or not step.valid_action or sds_response.metadata.get("repair_or_clarification", False),
                "errors": [step.error] if step.error else [],
            }
            turns.append(_turn(dialogue_state.turn_id, self.agent_b.name, sds_pipeline.text, action, step.state_before, step.state_after, step.valid_action, action_metadata))
            action_trace.append(asdict(step))
            state_trace.append(step.state_after)
            dialogue_state.turn_id += 1

            if action == "stop" or dialogue_state.invalid_moves >= self.max_invalid_moves:
                break

        planning_constraints = _planning_constraints(agent_a_private["constraints"], self.config.get("prompt_policy", {}))
        shortest, diagnostics = shortest_path(task, task["start"], task["goal"], planning_constraints)
        shortest_segments = summarize_route_segments(task, shortest)
        actual_path = [state["position"] for state in state_trace]
        actual_segments = summarize_route_segments(task, actual_path)
        route_summary = {
            "shortest_path": shortest,
            "shortest_path_length": path_length(shortest),
            "shortest_route_segments": shortest_segments,
            "shortest_route_advice": route_advice_text(shortest_segments),
            "actual_path": actual_path,
            "actual_path_length": max(0, len(self.environment.path) - 1),
            "actual_route_segments": actual_segments,
            "actual_route_advice": route_advice_text(actual_segments),
            "planner_diagnostics": diagnostics,
        }
        transcript = {
            "run_id": self.run_id,
            "experiment_id": self.experiment_id,
            "seed": self.seed,
            "config": self.config,
            "system_profile": self.system_profile,
            "speech_pipeline": speech_pipeline_config,
            "knowledge_split": self.config.get("knowledge_split", _default_knowledge_split()),
            "agent_a": self.agent_a.describe(),
            "agent_b": self.agent_b.describe(),
            "agent_a_private_knowledge": agent_a_private,
            "agent_b_private_knowledge_summary": {
                "knows_network": True,
                "map_id": task["map_id"],
                "node_count": task["width"] * task["height"] - len(task.get("obstacles", [])),
                "blocked_node_count": len(task.get("obstacles", [])),
                "line_count": len(task.get("transit_lines", {})),
            },
            "shared_dialogue_state": shared_state,
            "task": task,
            "turns": turns,
            "state_trace": state_trace,
            "action_trace": action_trace,
            "audio_recordings": audio_recordings,
            "route_summary": route_summary,
            "final_state": self.environment.state(),
            "success": self.environment.state()["success"],
            "errors": dialogue_state.errors,
            "metrics": {},
            "failure_analysis": {},
        }
        transcript["metrics"] = compute_all_metrics(transcript)
        transcript["failure_analysis"] = analyze_run(transcript)
        return transcript


def _turn(
    turn_id: int,
    speaker: str,
    text: str,
    action: str | None,
    before: dict[str, Any],
    after: dict[str, Any],
    valid: bool,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    return {
        "turn_id": turn_id,
        "speaker": speaker,
        "text": text,
        "spoken_text": metadata.get("spoken_text", text),
        "recognized_text": metadata.get("recognized_text", text),
        "dialogue_act": metadata.get("dialogue_act", "action_execution" if action else "message"),
        "intent": metadata.get("intent"),
        "mentioned_goal": metadata.get("mentioned_goal"),
        "mentioned_origin": metadata.get("mentioned_origin"),
        "mentioned_start_time": metadata.get("mentioned_start_time"),
        "mentioned_constraints": metadata.get("mentioned_constraints", []),
        "interpreted_goal": metadata.get("interpreted_goal"),
        "interpreted_constraints": metadata.get("interpreted_constraints", []),
        "proposed_action": metadata.get("proposed_action"),
        "selected_action": metadata.get("selected_action", action),
        "interpreted_action": action,
        "route_plan": metadata.get("route_plan", []),
        "route_segments": metadata.get("route_segments", []),
        "route_advice": metadata.get("route_advice"),
        "pipeline_events": metadata.get("pipeline_events", []),
        "audio_path": metadata.get("audio_path"),
        "audio_sidecar_path": metadata.get("audio_sidecar_path"),
        "audio_duration_seconds": metadata.get("audio_duration_seconds", 0.0),
        "state_before": before,
        "state_after": after,
        "valid_action": valid,
        "constraint_satisfied": metadata.get("constraint_satisfied", True),
        "repair_or_clarification": metadata.get("repair_or_clarification", False),
        "ambiguity_detected": metadata.get("ambiguity_detected", False),
        "belief_state_before": metadata.get("belief_state_before", {}),
        "belief_state_after": metadata.get("belief_state_after", {}),
        "errors": metadata.get("errors", []),
    }


def _agent_a_private_knowledge(task: dict[str, Any], params: dict[str, Any]) -> dict[str, Any]:
    constraints = params.get("constraints") or _constraints_for_type(params.get("secondary_constraint_type", params.get("constraint_type", "comfort")))
    return {
        "origin": task["start"],
        "origin_label": station_label(task, task["start"]),
        "start_time": params.get("start_time", "08:00"),
        "goal": task["goal"],
        "goal_label": station_label(task, task["goal"]),
        "constraints": constraints,
        "preferences": params.get("preferences", ["prefer_shortest"]),
        "success_criteria": ["reach_goal", "respect_constraints"],
        "knows_network": False,
    }


def _agent_b_private_knowledge(task: dict[str, Any]) -> dict[str, Any]:
    return {
        "network": task,
        "current_position": task["start"],
        "knows_network": True,
        "knows_goal_initially": False,
        "knows_constraints_initially": False,
    }


def _constraints_for_type(constraint_type: str) -> list[str]:
    if constraint_type == "none":
        return []
    if constraint_type == "comfort":
        return ["low_fullness", "few_transfers"]
    return ["avoid_blocked", "prefer_shortest"]


def _planning_constraints(constraints: list[str], prompt_policy: dict[str, Any]) -> list[str]:
    values = list(constraints)
    if prompt_policy.get("route_strategy", "shortest_path_first") == "shortest_path_first" and "prefer_shortest" not in values:
        values.append("prefer_shortest")
    return values


def _public_state(state: dict[str, Any]) -> dict[str, Any]:
    return {"position": state["position"], "success": state["success"]}


def _default_knowledge_split() -> dict[str, Any]:
    return {
        "agent_a": {"knows_goal": True, "knows_constraints": True, "knows_network": False},
        "agent_b": {"knows_goal_initially": False, "knows_constraints_initially": False, "knows_network": True},
    }


def _audio_record(turn_id: int, speaker: str, pipeline_result: Any) -> dict[str, Any]:
    return {
        "turn_id": turn_id,
        "speaker": speaker,
        "audio_path": pipeline_result.audio_path,
        "audio_sidecar_path": pipeline_result.audio_sidecar_path,
        "duration_seconds": pipeline_result.audio_duration_seconds,
    }

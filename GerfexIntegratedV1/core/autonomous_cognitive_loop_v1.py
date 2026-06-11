import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.perception_cycle import run_perception_cycle
from core.execution_manager import execute


def plan_to_decision(goal, perception):
    plan = perception.get("plan", {}) if isinstance(perception, dict) else {}

    if not plan.get("ok"):
        return {
            "ok": False,
            "brain": "AutonomousCognitiveLoopV1",
            "intent": "no_plan",
            "target": None,
            "action": None,
            "reason": plan.get("reason", "no_valid_plan"),
            "perception": perception,
        }

    action_name = plan.get("action")

    if action_name == "search_web":
        return {
            "ok": True,
            "brain": "AutonomousCognitiveLoopV1",
            "intent": "web_search",
            "target": "chrome",
            "action": {
                "action": "open_url",
                "args": {
                    "url": "https://www.google.com/search?q=" + goal.replace(" ", "+")
                },
            },
            "reason": "perception_plan_search_web",
            "perception": perception,
        }

    if action_name == "open_app":
        target = "chrome"
        if "يوتيوب" in goal or "youtube" in goal.lower():
            target = "youtube"
        elif "الإعدادات" in goal or "اعدادات" in goal or "settings" in goal.lower():
            target = "settings"

        return {
            "ok": True,
            "brain": "AutonomousCognitiveLoopV1",
            "intent": "open_app",
            "target": target,
            "action": {
                "action": "open_app",
                "args": {"package": target},
            },
            "reason": "perception_plan_open_app",
            "perception": perception,
        }

    if action_name in ("read_page", "inspect_browser"):
        return {
            "ok": True,
            "brain": "AutonomousCognitiveLoopV1",
            "intent": "observe_only",
            "target": "screen",
            "action": None,
            "reason": "perception_plan_observe_only",
            "perception": perception,
        }

    return {
        "ok": False,
        "brain": "AutonomousCognitiveLoopV1",
        "intent": "unsupported_plan",
        "target": None,
        "action": None,
        "reason": f"unsupported_plan_action:{action_name}",
        "perception": perception,
    }


def run_autonomous_cognitive_loop(goal, max_steps=3, delay=1.0, execute_actions=True):
    history = []

    for step in range(1, max_steps + 1):
        perception = run_perception_cycle(goal)
        decision = plan_to_decision(goal, perception)

        record = {
            "step": step,
            "perception_ok": perception.get("ok"),
            "screen_type": perception.get("understanding", {}).get("screen_type"),
            "plan": perception.get("plan"),
            "decision": {
                "ok": decision.get("ok"),
                "intent": decision.get("intent"),
                "target": decision.get("target"),
                "action": decision.get("action"),
                "reason": decision.get("reason"),
            },
        }

        if not decision.get("ok"):
            record["execution"] = {"ok": False, "reason": "decision_not_ok"}
            history.append(record)
            return {
                "ok": False,
                "mode": "AUTONOMOUS_COGNITIVE_LOOP_V1",
                "goal": goal,
                "status": "stopped_no_decision",
                "steps": history,
            }

        if decision.get("intent") == "observe_only":
            record["execution"] = {"ok": True, "reason": "observe_only_no_action"}
            history.append(record)
            return {
                "ok": True,
                "mode": "AUTONOMOUS_COGNITIVE_LOOP_V1",
                "goal": goal,
                "status": "observed",
                "steps": history,
            }

        execution = execute(decision) if execute_actions else {"ok": True, "dry_run": True}
        record["execution"] = execution
        history.append(record)

        if not execution.get("ok"):
            return {
                "ok": False,
                "mode": "AUTONOMOUS_COGNITIVE_LOOP_V1",
                "goal": goal,
                "status": "execution_failed",
                "steps": history,
            }

        time.sleep(delay)

    return {
        "ok": True,
        "mode": "AUTONOMOUS_COGNITIVE_LOOP_V1",
        "goal": goal,
        "status": "max_steps_reached",
        "steps": history,
    }


if __name__ == "__main__":
    goal = " ".join(sys.argv[1:]) or "حلل الشاشة الحالية"
    print(json.dumps(run_autonomous_cognitive_loop(goal), ensure_ascii=False, indent=2))

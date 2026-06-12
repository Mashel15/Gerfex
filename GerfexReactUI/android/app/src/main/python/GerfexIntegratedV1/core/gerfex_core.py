import sys
from pathlib import Path
from gerfex_android_paths import app_path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from learning.unified_learning import learn_from_goal
from runtime.runtime_state_manager import update_state
from brain.experience_decision import apply_experience_advice
from memory.memory_advisor import advise
from memory.memory_recall import recall
import json


from brain.brain_manager import decide, remember
from brain.brain_router import route
from core.execution_manager import execute
from learning.learning_manager import learn


def clear_queue():
    q = app_path("runtime", "android_queue.txt")
    q.parent.mkdir(parents=True, exist_ok=True)
    q.write_text("", encoding="utf-8")


def run_goal(goal):
    try:
        memory_recall = recall(goal)
    except Exception as e:
        memory_recall = {"ok": False, "error": str(e)}

    try:
        memory_advice = advise(goal, memory_recall)
    except Exception as e:
        memory_advice = {"ok": False, "error": str(e)}
    routing = route(goal)

    # Multi-step commands must go to Queen first.
    # Example: "افتح كروم وابحث عن أخبار الذكاء الاصطناعي"
    text = (goal or "").strip()
    multi_step_request = (
        ("افتح" in text and ("ابحث" in text or "بحث" in text))
        or ("ثم" in text)
        or ("و" in text and "ابحث" in text)
    )

    if multi_step_request:
        routing = {"ok": True, "route": "android", "reason": "multi_step_priority_to_queen"}
        decision = decide(goal)
        decision["route"] = routing

        try:
            decision = apply_experience_advice(goal, decision, memory_advice)
        except Exception as e:
            decision["experience_error"] = str(e)

        execution = execute(decision)
        learning = learn(goal, decision, execution)

    elif routing.get("route") == "research":
        clear_queue()
        from autonomous.autonomous_loop import run_autonomous_goal
        execution = run_autonomous_goal(goal)
        decision = {
            "ok": True,
            "brain": "BrainRouter",
            "intent": "news_research_pipeline",
            "target": "research",
            "route": routing,
            "reason": "Brain Router وجّه الطلب إلى مسار الأخبار الجاهز"
        }
        learning = {"ok": True, "mode": "router_research"}
    elif routing.get("route") == "cognitive":
        execution = run_cognitive_goal(goal)
        decision = {
            "ok": True,
            "brain": "BrainRouter",
            "intent": "cognitive",
            "target": "cognitive",
            "route": routing,
            "reason": "Brain Router وجّه الطلب إلى التفكير/التخطيط"
        }
        learning = {"ok": True, "mode": "router_cognitive"}
    else:
        decision = decide(goal)
        decision["route"] = routing

        try:
            decision = apply_experience_advice(goal, decision, memory_advice)
        except Exception as e:
            decision["experience_error"] = str(e)

        execution = execute(decision)
        learning = learn(goal, decision, execution)

    out = {
        "ok": execution.get("ok", False),
        "goal": goal,
        "memory_recall": memory_recall,
        "memory_advice": memory_advice,
        "routing": routing,
        "decision": decision,
        "execution": execution,
        "learning": learning
    }

    remember({
        "goal": goal,
        "routing": routing,
        "decision": decision,
        "execution_ok": execution.get("ok")
    })

    try:
        runtime_state = update_state({
            "goal": goal,
            "route": out.get("routing"),
            "intent": out.get("decision", {}).get("intent"),
            "target": out.get("decision", {}).get("target"),
            "ok": out.get("execution", {}).get("ok"),
            "error": out.get("execution", {}).get("reason")
        })
    except Exception as e:
        runtime_state = {"ok": False, "error": str(e)}

    out["runtime_state"] = runtime_state

    try:
        out["unified_learning"] = learn_from_goal(
            goal,
            out.get("routing"),
            out.get("decision", {}),
            out.get("execution", {})
        )
    except Exception as e:
        out["unified_learning"] = {"ok": False, "error": str(e)}

    return out


def run_cognitive_goal(goal):
    from core.perception_cycle import run_perception_cycle

    perception = run_perception_cycle(goal)
    return {
        "ok": perception.get("ok", False),
        "mode": "cognitive_plan_only",
        "goal": goal,
        "perception": perception,
        "note": "Cognitive mode observes, understands, and plans without direct execution."
    }


if __name__ == "__main__":
    goal = " ".join(sys.argv[1:]) or "افتح كروم"
    print(json.dumps(run_goal(goal), ensure_ascii=False, indent=2))

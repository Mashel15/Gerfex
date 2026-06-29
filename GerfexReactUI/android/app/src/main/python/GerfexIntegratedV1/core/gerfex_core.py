import sys
from pathlib import Path
from GerfexIntegratedV1.gerfex_android_paths import app_path

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
from runtime.execution_trace import add_stage, new_trace, save_trace
from core.secondary_systems import run_secondary_system


def clear_queue():
    # APK standalone mode: no external legacy queue is used.
    # Kept as a compatibility no-op for old research paths.
    return True


def run_goal(goal, trace=None):
    if trace is None:
        trace = new_trace(goal)

    add_stage(trace, "core_start", source="gerfex_core", goal=goal)

    try:
        memory_recall = recall(goal)
        add_stage(trace, "memory_recall", source="memory_recall", ok=memory_recall.get("ok"))
    except Exception as e:
        memory_recall = {"ok": False, "error": str(e)}
        add_stage(trace, "memory_recall_error", source="memory_recall", error=str(e))

    try:
        memory_advice = advise(goal, memory_recall)
        add_stage(trace, "memory_advice", source="memory_advisor", ok=memory_advice.get("ok"))
    except Exception as e:
        memory_advice = {"ok": False, "error": str(e)}
        add_stage(trace, "memory_advice_error", source="memory_advisor", error=str(e))

    routing = route(goal)
    add_stage(trace, "brain_router", source="brain_router", route=routing.get("route"), ok=routing.get("ok"))

    # Multi-step commands go through Internal Intelligence.
    # Example: "افتح كروم وابحث عن أخبار الذكاء الاصطناعي"
    text = (goal or "").strip()
    multi_step_request = (
        ("افتح" in text and ("ابحث" in text or "بحث" in text))
        or ("ثم" in text)
        or ("و" in text and "ابحث" in text)
    )

    if multi_step_request:
        routing = {"ok": True, "route": "android", "reason": "multi_step_priority_to_internal_intelligence"}
        add_stage(trace, "provider_request", source="gerfex_core", provider="internal_intelligence", route=routing.get("route"))
        decision = decide(goal)
        add_stage(trace, "provider_response", source="brain_manager", provider="internal_intelligence", intent=decision.get("intent"), target=decision.get("target"), ok=decision.get("ok"), reason=decision.get("reason"))
        decision["route"] = routing

        try:
            decision = apply_experience_advice(goal, decision, memory_advice)
        except Exception as e:
            decision["experience_error"] = str(e)

        execution = execute(decision, trace=trace)
        learning = learn(goal, decision, execution)

    elif routing.get("route") == "research":
        try:
            from search_bundle.core.news_pipeline import run as run_news_pipeline

            query = text
            for w in ["تابع", "آخر", "اخر", "أخبار", "اخبار", "خبر", "news"]:
                query = query.replace(w, " ")
            query = " ".join(query.split()) or goal

            news_result = run_news_pipeline(query)
            execution = {
                "ok": bool(news_result.get("ok")),
                "mode": "research_news_pipeline",
                "query": query,
                "result": news_result,
                "reply": "تم تشغيل مسار الأخبار الداخلي." if news_result.get("ok") else "فشل مسار الأخبار الداخلي."
            }
        except Exception as e:
            execution = {
                "ok": False,
                "mode": "research_news_pipeline",
                "reason": "research_pipeline_error",
                "error": str(e)
            }

        decision = {
            "ok": execution.get("ok", False),
            "brain": "BrainRouter",
            "intent": "news_research_pipeline",
            "target": "research",
            "route": routing,
            "reason": "Brain Router وجّه الطلب إلى search_bundle/core/news_pipeline.py"
        }
        learning = {"ok": True, "mode": "router_research"}
    elif routing.get("route") == "cognitive":
        try:
            from core.cognitive_execute import execute_cognitive_goal
            execution = execute_cognitive_goal(goal)
        except Exception as e:
            execution = {
                "ok": False,
                "mode": "cognitive_execute",
                "reason": "cognitive_execute_error",
                "error": str(e)
            }
        decision = {
            "ok": True,
            "brain": "BrainRouter",
            "intent": "cognitive",
            "target": "cognitive",
            "route": routing,
            "reason": "Brain Router وجّه الطلب إلى التفكير/التخطيط"
        }
        learning = {"ok": True, "mode": "router_cognitive"}

    elif routing.get("route") == "secondary":
        system_name = routing.get("system") or routing.get("target") or "unknown"
        execution = run_secondary_system(goal, system_name, trace=trace)
        decision = {
            "ok": execution.get("ok", False),
            "brain": "BrainRouter",
            "intent": "secondary_system",
            "target": system_name,
            "route": routing,
            "reason": "Brain Router وجّه الطلب إلى نظام ثانوي"
        }
        learning = {"ok": True, "mode": "router_secondary"}

    else:
        add_stage(trace, "provider_request", source="gerfex_core", provider="internal_intelligence", route=routing.get("route"))
        decision = decide(goal)
        add_stage(trace, "provider_response", source="brain_manager", provider="internal_intelligence", intent=decision.get("intent"), target=decision.get("target"), ok=decision.get("ok"), reason=decision.get("reason"))
        decision["route"] = routing

        try:
            decision = apply_experience_advice(goal, decision, memory_advice)
        except Exception as e:
            decision["experience_error"] = str(e)

        execution = execute(decision, trace=trace)
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

    add_stage(trace, "core_end", source="gerfex_core", ok=out.get("ok"))
    try:
        save_trace(trace)
        out["trace_saved"] = True
        out["trace_id"] = trace.get("trace_id")
    except Exception as e:
        out["trace_saved"] = False
        out["trace_error"] = str(e)
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

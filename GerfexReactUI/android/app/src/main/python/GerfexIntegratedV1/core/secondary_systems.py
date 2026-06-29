from runtime.execution_trace import add_stage

def run_secondary_system(goal, system_name, trace=None):
    name = (system_name or "").strip().lower()

    add_stage(
        trace,
        "secondary_system_start",
        source="secondary_systems",
        system=name,
        goal=goal
    )

    try:
        if name in ["goal_worker", "worker", "run_goal_worker"]:
            from runtime.goal_worker import run_next_goal
            result = run_next_goal()

        elif name in ["autonomous_scheduler", "scheduler"]:
            from runtime.autonomous_scheduler import scheduler_tick
            result = scheduler_tick()

        elif name in ["autonomous_goal_generator", "goal_generator"]:
            from runtime.autonomous_goal_generator import generate_and_queue
            result = generate_and_queue()

        elif name in ["autonomous_cognitive_loop", "autonomous_loop"]:
            from core.autonomous_cognitive_loop_v1 import run_autonomous_cognitive_loop
            result = run_autonomous_cognitive_loop(goal, max_steps=3, delay=0.2, execute_actions=False)

        elif name in ["cognitive_search", "cognitive_search_execute"]:
            from core.cognitive_search_execute import execute_goal
            result = execute_goal(goal)

        else:
            result = {
                "ok": False,
                "reason": "unknown_secondary_system",
                "system": name
            }

        add_stage(
            trace,
            "secondary_system_end",
            source="secondary_systems",
            system=name,
            ok=result.get("ok") if isinstance(result, dict) else True
        )

        return {
            "ok": result.get("ok", True) if isinstance(result, dict) else True,
            "mode": "secondary_system",
            "system": name,
            "result": result,
            "reply": _reply_for(name, result)
        }

    except Exception as e:
        add_stage(
            trace,
            "secondary_system_error",
            source="secondary_systems",
            system=name,
            error=str(e)
        )

        return {
            "ok": False,
            "mode": "secondary_system",
            "system": name,
            "reason": "secondary_system_error",
            "error": str(e),
            "reply": "فشل تشغيل النظام الثانوي: " + str(e)
        }

def _reply_for(name, result):
    if not isinstance(result, dict):
        return str(result)

    if result.get("reply"):
        return result.get("reply")

    if result.get("ok") is False:
        return result.get("reason") or result.get("error") or "فشل تشغيل النظام الثانوي."

    labels = {
        "goal_worker": "تم تشغيل عامل الأهداف.",
        "worker": "تم تشغيل عامل الأهداف.",
        "autonomous_scheduler": "تم تشغيل المجدول الذاتي.",
        "scheduler": "تم تشغيل المجدول الذاتي.",
        "autonomous_goal_generator": "تم توليد هدف ذاتي.",
        "goal_generator": "تم توليد هدف ذاتي.",
        "autonomous_cognitive_loop": "تم تشغيل الحلقة المعرفية الذاتية.",
        "autonomous_loop": "تم تشغيل الحلقة المعرفية الذاتية.",
        "cognitive_search": "تم تشغيل البحث المعرفي.",
        "cognitive_search_execute": "تم تشغيل البحث المعرفي.",
    }

    return labels.get(name, "تم تشغيل النظام الثانوي.")

from memory.unified_memory import remember

def learn_from_goal(goal, route, decision, execution):
    return remember({
        "type": "goal_learning",
        "goal": goal,
        "route": route,
        "intent": decision.get("intent") if isinstance(decision, dict) else None,
        "target": decision.get("target") if isinstance(decision, dict) else None,
        "ok": execution.get("ok") if isinstance(execution, dict) else None,
        "summary": (
            execution.get("summary", {}).get("summary")
            if isinstance(execution, dict) and isinstance(execution.get("summary"), dict)
            else None
        )
    })

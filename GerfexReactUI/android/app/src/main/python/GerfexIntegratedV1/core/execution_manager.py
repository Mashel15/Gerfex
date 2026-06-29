from android.android_bridge import queue_action
from safety.safety_guard import check_action
from runtime.execution_trace import add_stage


def _block(action, safety):
    return {
        "ok": False,
        "blocked": True,
        "action": action,
        "safety": safety
    }


def _safe_name(action):
    return action.get("action") if isinstance(action, dict) else None


def _safe_args(action):
    return action.get("args", {}) if isinstance(action, dict) else {}


def execute(decision, trace=None):
    add_stage(
        trace,
        "execution_manager_start",
        source="execution_manager",
        intent=decision.get("intent"),
        target=decision.get("target")
    )

    intent = decision.get("intent")
    if intent in ("gma_chat", "gma_learning_chat", "conversation"):
        reply = decision.get("reply") or decision.get("message") or decision.get("response") or decision.get("text") or "GMA جاهز."
        add_stage(trace, "execution_manager_end", source="execution_manager", ok=True, reason="gma_passthrough")
        return {"ok": True, "intent": intent, "target": decision.get("target", "conversation"), "reply": reply, "message": reply, "reason": "gma_passthrough", "decision": decision}

    if not decision.get("ok"):
        add_stage(
            trace,
            "execution_manager_stop",
            source="execution_manager",
            reason="decision_not_ok"
        )
        return {"ok": False, "reason": "decision_not_ok", "decision": decision}

    actions = decision.get("actions")

    if actions:
        results = []
        all_ok = True

        for index, action in enumerate(actions):
            action_name = _safe_name(action)
            action_args = _safe_args(action)

            safety = check_action(action)
            add_stage(
                trace,
                "action_safety_checked",
                source="safety_guard",
                index=index,
                action=action_name,
                allowed=safety.get("allowed")
            )

            if not safety.get("allowed"):
                results.append(_block(action, safety))
                all_ok = False
                add_stage(
                    trace,
                    "action_blocked",
                    source="safety_guard",
                    index=index,
                    action=action_name,
                    reason=safety.get("reason")
                )
                continue

            add_stage(
                trace,
                "native_action_request",
                source="execution_manager",
                index=index,
                action=action_name,
                args=action_args
            )

            r = queue_action(action)

            add_stage(
                trace,
                "native_action_created",
                source="android_bridge",
                index=index,
                action=action_name,
                ok=r.get("ok")
            )

            r["safety"] = safety
            results.append(r)

            if not r.get("ok"):
                all_ok = False

        native_actions = [
            r.get("native_action") or r.get("queued")
            for r in results
            if r.get("native_action") or r.get("queued")
        ]

        add_stage(
            trace,
            "execution_manager_end",
            source="execution_manager",
            ok=all_ok,
            native_action_count=len(native_actions),
            blocked_count=sum(1 for r in results if r.get("blocked"))
        )

        return {
            "ok": all_ok,
            "queued_count": sum(1 for r in results if r.get("ok")),
            "blocked_count": sum(1 for r in results if r.get("blocked")),
            "native_actions": native_actions,
            "results": results,
            "decision": decision
        }

    action = decision.get("action")

    if action:
        action_name = _safe_name(action)
        action_args = _safe_args(action)

        safety = check_action(action)
        add_stage(
            trace,
            "action_safety_checked",
            source="safety_guard",
            index=0,
            action=action_name,
            allowed=safety.get("allowed")
        )

        if not safety.get("allowed"):
            add_stage(
                trace,
                "action_blocked",
                source="safety_guard",
                index=0,
                action=action_name,
                reason=safety.get("reason")
            )
            return {
                "ok": False,
                "blocked": True,
                "action": action,
                "safety": safety,
                "decision": decision
            }

        add_stage(
            trace,
            "native_action_request",
            source="execution_manager",
            index=0,
            action=action_name,
            args=action_args
        )

        result = queue_action(action)

        add_stage(
            trace,
            "native_action_created",
            source="android_bridge",
            index=0,
            action=action_name,
            ok=result.get("ok")
        )

        result["safety"] = safety
        native_action = result.get("native_action") or result.get("queued")

        add_stage(
            trace,
            "execution_manager_end",
            source="execution_manager",
            ok=bool(result.get("ok")),
            native_action_count=1 if native_action else 0
        )

        return {
            "ok": bool(result.get("ok")),
            "native_actions": [native_action] if native_action else [],
            "queued": result,
            "decision": decision
        }

    add_stage(
        trace,
        "execution_manager_end",
        source="execution_manager",
        ok=False,
        reason="no_executable_action"
    )
    return {"ok": False, "reason": "no_executable_action", "decision": decision}

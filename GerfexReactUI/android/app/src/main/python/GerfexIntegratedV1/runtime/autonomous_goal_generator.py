import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from memory.unified_memory import recent
from runtime.goal_manager import list_goals, add_goal
from runtime.runtime_state_manager import get_state

DEFAULT_GOALS = [
    "أخبار الذكاء الاصطناعي",
    "افتح كروم",
    "حلل الشاشة الحالية"
]

def generate_goal():
    state = get_state()
    pending = list_goals("pending")

    if pending.get("count", 0) > 0:
        return {
            "ok": True,
            "mode": "pending_exists",
            "goal": None,
            "reason": "يوجد أهداف معلقة، لا نضيف هدف جديد"
        }

    mem = recent(20)
    failures = [m for m in mem if m.get("ok") is False]
    research_success = [
        m for m in mem
        if m.get("target") == "research" and m.get("ok") is True
    ]
    android_success = [
        m for m in mem
        if m.get("target") == "chrome" and m.get("ok") is True
    ]

    if failures:
        goal = "راجع آخر فشل وحاول إصلاحه"
        reason = "وجدت فشل سابق في الذاكرة"
    elif len(research_success) < 2:
        goal = "أخبار الذكاء الاصطناعي"
        reason = "مسار البحث يحتاج خبرة أكثر"
    elif len(android_success) < 3:
        goal = "افتح كروم"
        reason = "مسار أندرويد يحتاج تثبيت أكثر"
    else:
        goal = "حلل الشاشة الحالية"
        reason = "المسارات الأساسية مستقرة، ننتقل للإدراك"

    return {
        "ok": True,
        "mode": "generated",
        "goal": goal,
        "reason": reason,
        "state_status": state.get("status"),
        "memory_count": len(mem)
    }

def generate_and_queue():
    g = generate_goal()
    if not g.get("goal"):
        return g

    queued = add_goal(g["goal"], source="autonomous_goal_generator")
    g["queued"] = queued
    return g

if __name__ == "__main__":
    import json
    print(json.dumps(generate_and_queue(), ensure_ascii=False, indent=2))

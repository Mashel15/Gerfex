import json
from apk_runtime import is_apk_runtime, skip_external_runner_result
import sys
import time
from pathlib import Path
from gerfex_android_paths import app_path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.news_pipeline import run as run_news_pipeline
from research.open_best_news_result import open_best
from research.article_reader import read_article
from research.article_summarizer import summarize

LOG = app_path("learning", "autonomous_loop_log.json")


def save_event(event):
    LOG.parent.mkdir(parents=True, exist_ok=True)

    data = []
    if LOG.exists():
        try:
            data = json.loads(LOG.read_text(encoding="utf-8"))
        except Exception:
            data = []

    data.append(event)
    LOG.write_text(
        json.dumps(data[-300:], ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def run_autonomous_goal(goal):
    started = time.time()

    news = run_news_pipeline(goal)
    opened = open_best(open_chrome=False)

    # APK runtime: لا نستخدم Termux queue_runner
    if is_apk_runtime():
        opened["queue_process"] = skip_external_runner_result("autonomous_loop.initial_queue")
    else:
        try:
            from runtime.queue_runner import process_queue
            process_queue()
        except Exception as e:
            opened["queue_process_error"] = str(e)


    # نترك queue_runner يفتح الرابط ويعمل dump_ui
    time.sleep(7)

    article = read_article()

    if not article.get("ok") and article.get("reason") == "dirty_termux_dump":
        try:
            from android.android_bridge import queue_action

            queue_action({"action": "open_app", "args": {"package": "chrome"}})
            queue_action({"action": "wait", "args": {"seconds": 2}})
            queue_action({"action": "dump_ui", "args": {"focus": "chrome"}})

            if not is_apk_runtime():
                from runtime.queue_runner import process_queue
                process_queue()

            article = read_article()
        except Exception as e:
            article["recovery_error"] = str(e)

    summary = summarize()

    event = {
        "time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "goal": goal,
        "news_ok": news.get("ok"),
        "news_count": news.get("count"),
        "opened_ok": opened.get("ok"),
        "opened_title": opened.get("title"),
        "opened_domain": opened.get("domain"),
        "article_ok": article.get("ok"),
        "article_title": article.get("title"),
        "summary_ok": summary.get("ok") if isinstance(summary, dict) else None,
        "duration_seconds": round(time.time() - started, 2)
    }

    save_event(event)

    return {
        "ok": True,
        "mode": "GERFEX_AUTONOMOUS_COGNITIVE_LOOP_V1_RESEARCH_PIPELINE",
        "goal": goal,
        "news": news,
        "opened": opened,
        "article": article,
        "summary": summary,
        "learned": True,
        "log": str(LOG)
    }


if __name__ == "__main__":
    goal = " ".join(sys.argv[1:]) or "أخبار الذكاء الاصطناعي"
    print(json.dumps(run_autonomous_goal(goal), ensure_ascii=False, indent=2))

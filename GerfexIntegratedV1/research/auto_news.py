import sys, json, subprocess
from pathlib import Path

ROOT = Path.cwd()

def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT))
    return {
        "ok": r.returncode == 0,
        "stdout": r.stdout.strip(),
        "stderr": r.stderr.strip()
    }

def process_queue():
    code = """
import sys
from pathlib import Path
ROOT = Path.cwd()
sys.path.insert(0, str(ROOT / "runtime"))
import queue_runner
queue_runner.process_queue()
"""
    return run(["python", "-c", code])

def main():
    query = " ".join(sys.argv[1:]) or "أخبار الذكاء الاصطناعي"

    steps = []

    steps.append(("search", run(["python", "-m", "research.news_pipeline", query])))
    steps.append(("open", run(["python", "-m", "research.open_news_result", "افتح 1"])))
    steps.append(("queue", process_queue()))

    # تم تعطيل إعادة فتح Chrome هنا لمنع تكرار البحث/الفتح.
    # المسار الحالي يعتمد على open_news_result ثم قراءة الشاشة مباشرة.
    steps.append(("read_article", run(["python", "-m", "research.article_reader"])))
    steps.append(("summarize", run(["python", "-m", "research.article_summarizer"])))

    summary_path = Path("research/last_article_summary.txt")
    summary = summary_path.read_text(encoding="utf-8") if summary_path.exists() else ""

    out = {
        "ok": bool(summary.strip()),
        "query": query,
        "summary": summary,
        "steps_ok": {name: res["ok"] for name, res in steps}
    }

    Path("research/last_auto_news.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print(summary if summary else json.dumps(out, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()

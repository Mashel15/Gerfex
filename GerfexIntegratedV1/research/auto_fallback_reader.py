import json
import subprocess
from pathlib import Path

RESULTS = Path("research/last_news_results.json")
REPORT = Path("research/last_fallback_report.json")
SUMMARY = Path("research/last_article_summary.txt")

def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    return {
        "ok": r.returncode == 0,
        "stdout": r.stdout.strip(),
        "stderr": r.stderr.strip()
    }

def load_results():
    if not RESULTS.exists():
        return []
    data = json.loads(RESULTS.read_text(encoding="utf-8"))
    items = data.get("all") or data.get("top") or []
    return [x for x in items if x.get("readable_candidate", True)]

def main():
    items = load_results()
    attempts = []

    if not items:
        out = {
            "ok": False,
            "reason": "no_readable_candidates",
            "attempts": []
        }
        REPORT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return

    for i, item in enumerate(items, 1):
        title = item.get("title", "")
        score = item.get("source_quality_score", 0)

        run(["python", "-m", "research.open_news_result", f"افتح {i}"])

        q = run([
            "python", "-c",
            "import sys; from pathlib import Path; "
            "sys.path.insert(0, str(Path.cwd()/'runtime')); "
            "import queue_runner; queue_runner.process_queue()"
        ])

        reader = run(["python", "-m", "research.article_reader"])
        summarizer = run(["python", "-m", "research.article_summarizer"])

        summary_text = SUMMARY.read_text(encoding="utf-8") if SUMMARY.exists() else ""

        success = (
            "ملخص المقال:" in summary_text
            and "فشل التلخيص" not in summary_text
            and len(summary_text.strip()) > 120
        )

        attempts.append({
            "index": i,
            "title": title,
            "score": score,
            "queue_ok": q["ok"],
            "reader_ok": reader["ok"],
            "summarizer_ok": summarizer["ok"],
            "success": success,
            "summary_preview": summary_text[:500]
        })

        if success:
            out = {
                "ok": True,
                "selected_index": i,
                "selected_title": title,
                "attempts": attempts,
                "summary": summary_text
            }
            REPORT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
            print(summary_text)
            return

    out = {
        "ok": False,
        "reason": "all_candidates_failed",
        "attempts": attempts
    }
    REPORT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()

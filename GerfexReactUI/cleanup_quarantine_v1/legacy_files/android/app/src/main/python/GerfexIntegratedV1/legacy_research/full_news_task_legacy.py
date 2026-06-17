import json
import subprocess
import sys
from pathlib import Path

def run_cmd(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    return {
        "ok": r.returncode == 0,
        "stdout": r.stdout.strip(),
        "stderr": r.stderr.strip()
    }

def main():
    query = " ".join(sys.argv[1:]) or "أخبار الذكاء الاصطناعي"

    steps = []

    steps.append({
        "step": "search_news",
        "result": run_cmd(["python", "-m", "research.news_pipeline", query])
    })

    steps.append({
        "step": "open_first_result",
        "result": run_cmd(["python", "-m", "research.open_news_result", "افتح 1"])
    })

    steps.append({
        "step": "process_queue",
        "note": "نفّذ هذا يدويًا بعده لتشغيل فتح المتصفح ثم dump"
    })

    out = {
        "ok": True,
        "query": query,
        "steps": steps,
        "next": "بعد فتح الصفحة وتنفيذ dump، شغّل: python -m research.article_reader ثم python -m research.article_summarizer"
    }

    print(json.dumps(out, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()

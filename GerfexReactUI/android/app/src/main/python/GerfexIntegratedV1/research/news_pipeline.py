import json, urllib.parse, urllib.request, xml.etree.ElementTree as ET
from research.source_filter import filter_results
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

TRUSTED = ["الجزيرة", "BBC", "رويترز", "Reuters", "AP", "Google", "OpenAI", "Microsoft"]

def recency_score(pub):
    try:
        dt = parsedate_to_datetime(pub)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        days = (datetime.now(timezone.utc) - dt).days
        return 30 if days <= 1 else 20 if days <= 3 else 10 if days <= 7 else 0
    except Exception:
        return 0

def score(item, query):
    title = item.get("title", "").lower()
    s = recency_score(item.get("date", ""))
    for w in query.lower().split():
        if len(w) > 2 and w in title:
            s += 5
    for src in TRUSTED:
        if src.lower() in title:
            s += 20
    return s

def collect(query, limit=8):
    q = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={q}&hl=ar&gl=SA&ceid=SA:ar"
    with urllib.request.urlopen(url, timeout=12) as r:
        root = ET.fromstring(r.read())

    results = []
    for item in root.findall(".//item")[:limit]:
        results.append({
            "title": item.findtext("title") or "",
            "source": "google_news_rss",
            "date": item.findtext("pubDate") or "",
            "link": item.findtext("link") or "",
        })
    return results

def run(query):
    results = collect(query)
    ranked = filter_results(sorted(results, key=lambda x: score(x, query), reverse=True))
    out = {
        "ok": True,
        "query": query,
        "mode": "rss",
        "count": len(ranked),
        "top": ranked[:3],
        "all": ranked
    }

    Path("research/last_news_results.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    return out

if __name__ == "__main__":
    import sys
    q = " ".join(sys.argv[1:]) or "أخبار الذكاء الاصطناعي"
    print(json.dumps(run(q), ensure_ascii=False, indent=2))

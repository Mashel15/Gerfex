import json, re
from pathlib import Path
from urllib.parse import urlparse

MEMORY = Path("memory/source_memory.json")
SCORES = Path("research/source_score.json")

DEFAULT_SCORES = {
    "reuters.com": 95,
    "apnews.com": 95,
    "bbc.com": 90,
    "bbc.co.uk": 90,
    "aljazeera.net": 85,
    "aawsat.com": 80,
    "alarabiya.net": 45,
    "youtube.com": 10,
    "youtu.be": 10,
    "instagram.com": 10,
    "tiktok.com": 10,
    "facebook.com": 15,
    "x.com": 20,
    "twitter.com": 20,
    "investing.com": 55,
}

BAD_HINTS = [
    "video", "tv", "youtube", "instagram", "shorts",
    "فيديو", "شاهد", "بث", "قناة", "تلفزيونية"
]

GOOD_HINTS = [
    "article", "news", "سياسة", "اقتصاد", "تقنية", "علوم",
    "تقرير", "تحليل", "مقال"
]

def load_json(path, default):
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return default

def save_default_scores():
    if not SCORES.exists():
        SCORES.write_text(json.dumps(DEFAULT_SCORES, ensure_ascii=False, indent=2), encoding="utf-8")

def domain_of(url):
    try:
        host = urlparse(url).netloc.lower()
        return host.replace("www.", "")
    except Exception:
        return ""

def score_item(item):
    save_default_scores()

    scores = load_json(SCORES, DEFAULT_SCORES)
    memory = load_json(MEMORY, {})

    title = item.get("title", "")
    link = item.get("link", "")
    source = item.get("source", "")
    text = f"{title} {link} {source}".lower()
    domain = domain_of(link)

    score = 50
    reasons = []

    for d, s in scores.items():
        if d in domain or d in text:
            score = max(score, s)
            reasons.append(f"known_source:{d}:{s}")

    if "news.google.com/rss/articles" in link:
        score -= 5
        reasons.append("google_news_redirect")

    if any(h in text for h in BAD_HINTS):
        score -= 25
        reasons.append("video_or_social_hint")

    if any(h in text for h in GOOD_HINTS):
        score += 10
        reasons.append("article_hint")

    mem = memory.get(domain) or memory.get(source) or {}
    failures = int(mem.get("failures", 0))
    successes = int(mem.get("successes", 0))

    if failures:
        score -= min(40, failures * 15)
        reasons.append(f"past_failures:{failures}")

    if successes:
        score += min(25, successes * 10)
        reasons.append(f"past_successes:{successes}")

    score = max(0, min(100, score))
    readable = score >= 60

    return {
        **item,
        "domain": domain,
        "source_quality_score": score,
        "readable_candidate": readable,
        "quality_reasons": reasons
    }

def filter_results(results):
    scored = [score_item(x) for x in results]
    scored.sort(key=lambda x: x.get("source_quality_score", 0), reverse=True)
    return scored

def remember_result(item, ok, reason=""):
    memory = load_json(MEMORY, {})
    key = item.get("domain") or domain_of(item.get("url", "") or item.get("link", "")) or item.get("source", "unknown")

    row = memory.get(key, {"successes": 0, "failures": 0, "last_reason": ""})
    if ok:
        row["successes"] = int(row.get("successes", 0)) + 1
    else:
        row["failures"] = int(row.get("failures", 0)) + 1
    row["last_reason"] = reason
    memory[key] = row

    MEMORY.write_text(json.dumps(memory, ensure_ascii=False, indent=2), encoding="utf-8")
    return row

if __name__ == "__main__":
    import sys
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("research/last_news_results.json")
    data = json.loads(path.read_text(encoding="utf-8"))
    items = data.get("all") or data.get("top") or []
    out = filter_results(items)
    print(json.dumps(out[:8], ensure_ascii=False, indent=2))

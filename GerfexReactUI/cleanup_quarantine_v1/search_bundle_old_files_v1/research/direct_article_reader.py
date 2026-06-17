import json, re, html, urllib.request
from pathlib import Path

RESULTS = Path("research/last_news_results.json")
OUT = Path("research/last_article_read.json")

BAD = ["script", "style", "nav", "footer", "header"]

def strip_tags(s):
    s = re.sub(r"<(script|style)[\s\S]*?</\1>", " ", s, flags=re.I)
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s)
    return " ".join(s.split())

def read(index=1):
    data = json.loads(RESULTS.read_text(encoding="utf-8"))
    items = data.get("all") or data.get("top") or []
    item = items[index - 1]
    url = item["link"]

    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    raw = urllib.request.urlopen(req, timeout=15).read().decode("utf-8", "ignore")

    title = item.get("title", "")
    parts = re.findall(r"<p[^>]*>([\s\S]*?)</p>", raw, flags=re.I)
    paragraphs = []

    for p in parts:
        t = strip_tags(p)
        if len(t) < 45:
            continue
        if any(b in t.lower() for b in BAD):
            continue
        paragraphs.append(t)

    out = {
        "ok": len(paragraphs) >= 2,
        "source": "direct_html",
        "title": title,
        "url": url,
        "paragraph_count": len(paragraphs),
        "paragraphs": paragraphs[:25],
        "preview": "\n\n".join(paragraphs[:5])
    }

    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    return out

if __name__ == "__main__":
    import sys
    idx = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    print(json.dumps(read(idx), ensure_ascii=False, indent=2))

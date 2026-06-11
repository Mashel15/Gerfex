import json, re, html, urllib.request
from pathlib import Path

OUT = Path("research/last_article_read.json")

BAD = ["script", "style", "instagram", "jpg", "إعلان", "اقرأ أيضاً"]

def strip_tags(s):
    s = re.sub(r"<script[\s\S]*?</script>", " ", s, flags=re.I)
    s = re.sub(r"<style[\s\S]*?</style>", " ", s, flags=re.I)
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s)
    return " ".join(s.split())

def read(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    raw = urllib.request.urlopen(req, timeout=20).read().decode("utf-8", "ignore")

    title_m = re.search(r"<title[^>]*>([\s\S]*?)</title>", raw, re.I)
    title = strip_tags(title_m.group(1)) if title_m else ""

    parts = re.findall(r"<p[^>]*>([\s\S]*?)</p>", raw, flags=re.I)
    paragraphs = []

    for p in parts:
        t = strip_tags(p)
        if len(t) < 45:
            continue
        if any(b.lower() in t.lower() for b in BAD):
            continue
        paragraphs.append(t)

    out = {
        "ok": len(paragraphs) >= 2,
        "source": "direct_url_html",
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
    url = sys.argv[1]
    print(json.dumps(read(url), ensure_ascii=False, indent=2))

import re
import urllib.request

for url in ["https://www.b17.ru/forum/", "https://www.b17.ru/forum/?mod=new"]:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
    topics = re.findall(r"<tr class='list\s*'\s+id=topic_(\d+)>(.*?)</tr>", html, re.DOTALL | re.IGNORECASE)
    print(f"\n=== {url} === topics: {len(topics)}")
    for tid, body in topics:
        if "ico_svg_f2" not in body:
            continue
        m = re.search(r"<td class=n[^>]*>.*?>(\d+)</span>", body, re.DOTALL)
        replies = int(m.group(1)) if m else -1
        title_m = re.search(r"<td class=t[^>]*>.*?<a[^>]*>([^<]+)</a>", body, re.DOTALL)
        title = title_m.group(1).strip() if title_m else "?"
        consultant_m = re.search(r"Консультирует:\s*([^)<&]+)", body)
        consultant = consultant_m.group(1).strip() if consultant_m else ""
        print(f"  id={tid} replies={replies} | {title[:50]} | {consultant}")

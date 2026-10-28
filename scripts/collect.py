"""매일 인기 키워드 후보를 모으고 data/index.json을 다시 만든다. 표준 라이브러리만 사용."""
import json, sys, urllib.request, urllib.parse, xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
CAND = DATA / "candidates"
KST = timezone(timedelta(hours=9))
UA = {"User-Agent": "Mozilla/5.0 (keyword-desk; GitHub Actions)"}

TRENDS_RSS = "https://trends.google.com/trending/rss?geo=KR"
NEWS_QUERIES = ["코스피", "증시", "환율"]  # 경제 뉴스 후보를 모을 검색어 (자유롭게 수정)


def fetch(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def _local(tag):
    return tag.rsplit("}", 1)[-1]


def _child(el, name):
    for c in el:
        if _local(c.tag) == name:
            return (c.text or "").strip()
    return ""


def google_trends():
    # 네임스페이스 주소가 바뀌어도 동작하도록 태그 이름 끝부분으로만 찾음
    root = ET.fromstring(fetch(TRENDS_RSS))
    out = []
    for i, item in enumerate(root.iter("item")):
        news = []
        for c in item:
            if _local(c.tag) == "news_item":
                news.append({"title": _child(c, "news_item_title"), "url": _child(c, "news_item_url"), "source": _child(c, "news_item_source")})
        out.append({"rank": i + 1, "keyword": _child(item, "title"), "traffic": _child(item, "approx_traffic"),
                    "pubDate": _child(item, "pubDate"), "news": news[:3]})
    return out


def google_news(q):
    url = "https://news.google.com/rss/search?" + urllib.parse.urlencode(
        {"q": q + " when:1d", "hl": "ko", "gl": "KR", "ceid": "KR:ko"})
    root = ET.fromstring(fetch(url))
    out = []
    for item in list(root.iter("item"))[:8]:
        src = item.find("source")
        out.append({
            "title": (item.findtext("title") or "").strip(),
            "url": (item.findtext("link") or "").strip(),
            "source": (src.text or "").strip() if src is not None else "",
            "pubDate": (item.findtext("pubDate") or "").strip(),
        })
    return out


def rebuild_index():
    days = sorted(p.stem for p in DATA.glob("20??-??-??.json"))
    cands = sorted(p.stem for p in CAND.glob("20??-??-??.json"))
    (DATA / "index.json").write_text(json.dumps({"days": days, "candidates": cands}, ensure_ascii=False, indent=1), encoding="utf-8")
    print("index:", len(days), "days,", len(cands), "candidate files")


def collect():
    today = datetime.now(KST).strftime("%Y-%m-%d")
    result = {"date": today, "collectedAt": datetime.now(KST).isoformat(timespec="minutes"), "errors": []}
    try:
        result["googleTrends"] = google_trends()
    except Exception as e:  # 피드 형식이 바뀌거나 접속이 막히면 기록만 남김
        result["googleTrends"] = []
        result["errors"].append("구글 트렌드 RSS 수집 실패: " + repr(e))
    result["news"] = []
    for q in NEWS_QUERIES:
        try:
            result["news"].append({"query": q, "items": google_news(q)})
        except Exception as e:
            result["errors"].append("뉴스 수집 실패(" + q + "): " + repr(e))
    CAND.mkdir(parents=True, exist_ok=True)
    (CAND / (today + ".json")).write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    print(today, "trends:", len(result["googleTrends"]), "errors:", result["errors"])


if __name__ == "__main__":
    if "--index-only" not in sys.argv:
        collect()
    rebuild_index()

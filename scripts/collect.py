"""매일 인기 키워드 후보를 모으고 data/index.json을 다시 만든다. 표준 라이브러리만 사용."""
import html, json, os, re, sys, urllib.request, urllib.parse, xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
CAND = DATA / "candidates"
KST = timezone(timedelta(hours=9))
UA = {"User-Agent": "Mozilla/5.0 (keyword-desk; GitHub Actions)"}

TRENDS_RSS = "https://trends.google.com/trending/rss?geo=KR"
NEWS_QUERIES = ["코스피", "증시", "환율"]  # 경제 뉴스 후보를 모을 검색어 (자유롭게 수정)
YNA_ENT_RSS = "https://www.yna.co.kr/rss/entertainment.xml"  # 연합뉴스 연예 RSS
YNA_ENT_LIMIT = 10

# 네이버 API HUB (매일 10시 30분, --naver). 키는 GitHub Secrets의 NAVER_CLIENT_ID / NAVER_CLIENT_SECRET
NAVER_API = "https://naverapihub.apigw.ntruss.com/search/v1/"
NAVER_NEWS_QUERIES = ["영화", "드라마", "연예", "경제"]  # 네이버 뉴스 검색어 (자유롭게 수정)
NAVER_BLOG_FROM_TRENDS = 3  # 구글 트렌드 상위 몇 개로 블로그 상위 글을 볼지
BLOG_REQUEST = DATA / "blog-request.txt"  # 블로그 상위 글을 보고 싶은 키워드 (한 줄에 하나)


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


def google_news(q, limit=8):
    url = "https://news.google.com/rss/search?" + urllib.parse.urlencode(
        {"q": q + " when:1d", "hl": "ko", "gl": "KR", "ceid": "KR:ko"})
    root = ET.fromstring(fetch(url))
    out = []
    for item in list(root.iter("item"))[:limit]:
        src = item.find("source")
        out.append({
            "title": (item.findtext("title") or "").strip(),
            "url": (item.findtext("link") or "").strip(),
            "source": (src.text or "").strip() if src is not None else "",
            "pubDate": (item.findtext("pubDate") or "").strip(),
        })
    return out


def yonhap_entertainment():
    """연합뉴스 연예 기사 목록(최신순). RSS가 실패하면 구글 뉴스에서 연합뉴스 기사만 골라 옴."""
    errors = []
    try:
        root = ET.fromstring(fetch(YNA_ENT_RSS))
        items = []
        for item in list(root.iter("item"))[:YNA_ENT_LIMIT]:
            items.append({
                "title": (item.findtext("title") or "").strip(),
                "url": (item.findtext("link") or "").strip(),
                "source": "연합뉴스",
                "pubDate": (item.findtext("pubDate") or "").strip(),
            })
        if items:
            return {"via": "연합뉴스 RSS", "items": items}, errors
        errors.append("연합뉴스 RSS에 기사가 없음")
    except Exception as e:
        errors.append("연합뉴스 RSS 수집 실패: " + repr(e))
    try:
        items = [n for n in google_news("site:yna.co.kr 연예", limit=30) if "연합" in n["source"]]
        return {"via": "구글 뉴스 대체", "items": items[:YNA_ENT_LIMIT]}, errors
    except Exception as e:
        errors.append("연합뉴스 연예 대체 경로(구글 뉴스) 실패: " + repr(e))
    return {"via": "", "items": []}, errors


def _clean(text):
    # 네이버 응답 제목·요약에 섞인 <b> 태그와 &quot; 같은 기호를 정리
    return html.unescape(re.sub(r"<[^>]+>", "", text or "")).strip()


def naver_search(kind, query, display, sort):
    cid, secret = os.environ.get("NAVER_CLIENT_ID", ""), os.environ.get("NAVER_CLIENT_SECRET", "")
    if not cid or not secret:
        raise RuntimeError("NAVER_CLIENT_ID / NAVER_CLIENT_SECRET이 설정되지 않음")
    url = NAVER_API + kind + "?" + urllib.parse.urlencode({"query": query, "display": display, "sort": sort})
    req = urllib.request.Request(url, headers={**UA, "X-NCP-APIGW-API-KEY-ID": cid, "X-NCP-APIGW-API-KEY": secret})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8")).get("items", [])


def naver_news(q):
    # 정확도순으로 받은 뒤 최근 이틀 안의 기사만 남김
    cutoff = datetime.now(KST) - timedelta(days=2)
    out = []
    for it in naver_search("news", q, 30, "sim"):
        try:
            when = parsedate_to_datetime(it.get("pubDate", ""))
        except (TypeError, ValueError):
            when = None
        if when and when < cutoff:
            continue
        out.append({"title": _clean(it.get("title")), "url": it.get("originallink") or it.get("link", ""),
                    "pubDate": it.get("pubDate", "")})
    return out[:10]


def naver_blog(q):
    return [{"title": _clean(it.get("title")), "url": it.get("link", ""), "blogger": _clean(it.get("bloggername")),
             "bloggerUrl": it.get("bloggerlink", ""), "postdate": it.get("postdate", ""),
             "summary": _clean(it.get("description"))[:120]}
            for it in naver_search("blog", q, 10, "sim")]


def blog_keywords(cand):
    words = []
    if BLOG_REQUEST.exists():
        words += [l.strip() for l in BLOG_REQUEST.read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]
    words += [t["keyword"] for t in cand.get("googleTrends", [])[:NAVER_BLOG_FROM_TRENDS]]
    return list(dict.fromkeys(w for w in words if w))


def collect_naver():
    today = datetime.now(KST).strftime("%Y-%m-%d")
    path = CAND / (today + ".json")
    cand = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"date": today, "errors": []}
    cand["errors"] = [e for e in cand.get("errors", []) if not e.startswith("네이버")]  # 다시 실행할 때 이전 네이버 오류는 지움
    cand["naverCollectedAt"] = datetime.now(KST).isoformat(timespec="minutes")
    cand["naverNews"], cand["naverBlogs"] = [], []
    for q in NAVER_NEWS_QUERIES:
        try:
            cand["naverNews"].append({"query": q, "items": naver_news(q)})
        except Exception as e:
            cand["errors"].append("네이버 뉴스 수집 실패(" + q + "): " + repr(e))
    for q in blog_keywords(cand):
        try:
            cand["naverBlogs"].append({"query": q, "items": naver_blog(q)})
        except Exception as e:
            cand["errors"].append("네이버 블로그 수집 실패(" + q + "): " + repr(e))
    CAND.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cand, ensure_ascii=False, indent=1), encoding="utf-8")
    print(today, "naver news:", len(cand["naverNews"]), "blogs:", len(cand["naverBlogs"]), "errors:", cand["errors"])


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
    result["yonhapEnt"], errs = yonhap_entertainment()
    result["errors"].extend(errs)
    result["news"] = []
    for q in NEWS_QUERIES:
        try:
            result["news"].append({"query": q, "items": google_news(q)})
        except Exception as e:
            result["errors"].append("뉴스 수집 실패(" + q + "): " + repr(e))
    CAND.mkdir(parents=True, exist_ok=True)
    (CAND / (today + ".json")).write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    print(today, "trends:", len(result["googleTrends"]), "yonhap:", len(result["yonhapEnt"]["items"]), "errors:", result["errors"])


if __name__ == "__main__":
    if "--naver" in sys.argv:
        collect_naver()
    elif "--index-only" not in sys.argv:
        collect()
    rebuild_index()

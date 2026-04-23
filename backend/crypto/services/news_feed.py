"""
News feed realtime cho crypto & commodity bots.
Nguồn: RSS feeds miễn phí (CoinDesk, CoinTelegraph, Decrypt, Reuters)
       + Fear & Greed Index API (alternative.me)
Chạy mỗi 5 phút trong background thread.
"""
import threading
import time
import logging
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
from django.utils import timezone as dj_tz

logger = logging.getLogger(__name__)

_feed_started = False
_feed_lock = threading.Lock()

# ── RSS Sources ──────────────────────────────────────────────────────────────
RSS_SOURCES = [
    # Crypto news
    {"url": "https://www.coindesk.com/arc/outboundfeeds/rss/",          "source": "CoinDesk",      "category": "CRYPTO"},
    {"url": "https://cointelegraph.com/rss",                             "source": "CoinTelegraph", "category": "CRYPTO"},
    {"url": "https://decrypt.co/feed",                                   "source": "Decrypt",       "category": "CRYPTO"},
    {"url": "https://bitcoinmagazine.com/.rss/full/",                   "source": "BitcoinMag",    "category": "CRYPTO"},
    {"url": "https://cryptonews.com/news/feed/",                         "source": "CryptoNews",    "category": "CRYPTO"},
    # Macro & Finance
    {"url": "https://feeds.content.dowjones.io/public/rss/mw_realtimeheadlines", "source": "MarketWatch", "category": "MACRO"},
    {"url": "https://www.investing.com/rss/news_25.rss",                 "source": "Investing.com", "category": "MACRO"},
    # Commodity
    {"url": "https://www.kitco.com/rss/kitco-news.xml",                  "source": "Kitco",         "category": "COMMODITY"},
    {"url": "https://oilprice.com/rss/main",                             "source": "OilPrice",      "category": "COMMODITY"},
]

# Keywords mapping để gắn symbols
SYMBOL_KEYWORDS = {
    "BTC": ["bitcoin", "btc", "satoshi", "halving"],
    "ETH": ["ethereum", "eth", "vitalik", "eip"],
    "SOL": ["solana", "sol"],
    "XRP": ["xrp", "ripple"],
    "BNB": ["binance", "bnb"],
    "DOGE": ["dogecoin", "doge", "musk"],
    "PEPE": ["pepe", "meme coin", "memecoin"],
    "WIF": ["dogwifhat", "wif"],
    "BONK": ["bonk"],
    "AAVE": ["aave", "lending protocol"],
    "LINK": ["chainlink", "link", "oracle"],
    "UNI": ["uniswap", "uni"],
    "ARB": ["arbitrum", "arb"],
    "OP": ["optimism"],
    "XAU": ["gold", "vang", "precious metal", "xau", "bullion", "fed rate", "inflation"],
    "XAG": ["silver", "bac", "xag"],
    "WTI": ["oil", "crude", "wti", "opec", "petroleum", "barrel"],
    "BRENT": ["brent", "crude oil"],
    "NATGAS": ["natural gas", "natgas", "lng"],
    "COPPER": ["copper", "dong"],
    "WHEAT": ["wheat", "grain", "ukraine war", "russia export"],
    "CORN": ["corn", "ethanol", "grain"],
    "COFFEE": ["coffee", "brazil drought", "el nino"],
    "SUGAR": ["sugar", "cane"],
    "XPT": ["platinum"],
}

# Sentiment keywords
BULLISH_WORDS = [
    "surge", "rally", "pump", "bullish", "all-time high", "ath", "adoption",
    "institutional", "etf approved", "partnership", "upgrade", "growth",
    "record", "breakout", "recovery", "rebound", "moon", "bull",
    "rate cut", "dovish", "stimulus", "accumulate", "buy"
]
BEARISH_WORDS = [
    "crash", "dump", "bearish", "ban", "hack", "exploit", "scam", "fraud",
    "regulation", "sec", "lawsuit", "bankruptcy", "delist", "plunge",
    "selloff", "panic", "fear", "recession", "hawkish", "rate hike",
    "inflation high", "collapse", "warning", "risk", "sell"
]


def _detect_symbols(text: str) -> str:
    text_lower = text.lower()
    found = []
    for symbol, keywords in SYMBOL_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            found.append(symbol)
    return ",".join(found[:5])


def _detect_sentiment(text: str) -> str:
    text_lower = text.lower()
    bull = sum(1 for w in BULLISH_WORDS if w in text_lower)
    bear = sum(1 for w in BEARISH_WORDS if w in text_lower)
    if bull > bear + 1:
        return "BULLISH"
    if bear > bull + 1:
        return "BEARISH"
    return "NEUTRAL"


def _parse_date(date_str: str) -> datetime:
    from django.utils.timezone import make_aware, utc
    try:
        dt = parsedate_to_datetime(date_str)
        if dt.tzinfo is None:
            dt = make_aware(dt, utc)
        return dt
    except Exception:
        pass
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S%z", "%a, %d %b %Y %H:%M:%S %z"):
        try:
            dt = datetime.strptime(date_str[:30], fmt)
            if dt.tzinfo is None:
                dt = make_aware(dt, utc)
            return dt
        except Exception:
            pass
    return dj_tz.now()


def _fetch_rss(source: dict) -> list:
    try:
        resp = requests.get(
            source["url"],
            timeout=15,
            headers={"User-Agent": "Mozilla/5.0 (compatible; NewsBot/1.0)"},
        )
        resp.raise_for_status()
        root = ET.fromstring(resp.content)

        items = []
        channel = root.find("channel")
        if channel is None:
            channel = root

        for item in (channel.findall("item") or root.findall(".//{http://www.w3.org/2005/Atom}entry"))[:15]:
            def _get(tag, atom_tag=None):
                el = item.find(tag)
                if el is None and atom_tag:
                    el = item.find(f"{{http://www.w3.org/2005/Atom}}{atom_tag}")
                return (el.text or "").strip() if el is not None else ""

            title = _get("title", "title")
            link = _get("link", "id") or _get("guid")
            summary = _get("description", "summary") or _get("content")
            date_str = _get("pubDate", "published") or _get("updated")

            if not title or not link:
                continue

            # Strip HTML tags from summary
            import re
            summary = re.sub(r"<[^>]+>", "", summary)[:300]

            full_text = f"{title} {summary}"
            published_at = _parse_date(date_str) if date_str else dj_tz.now()

            items.append({
                "title": title[:400],
                "summary": summary,
                "source": source["source"],
                "url": link[:490],
                "category": source["category"],
                "sentiment": _detect_sentiment(full_text),
                "symbols": _detect_symbols(full_text),
                "published_at": published_at,
            })
        return items
    except Exception as e:
        logger.debug(f"RSS {source['source']}: {e}")
        return []


def _fetch_fear_greed() -> dict | None:
    try:
        r = requests.get("https://api.alternative.me/fng/?limit=1", timeout=10)
        data = r.json()["data"][0]
        return {"value": int(data["value"]), "label": data["value_classification"]}
    except Exception:
        return None


def _save_news(items: list):
    from crypto.models import NewsItem

    cutoff = dj_tz.now() - timedelta(hours=24)
    saved = 0
    for item in items:
        if item["published_at"] < cutoff:
            continue
        try:
            NewsItem.objects.get_or_create(
                url=item["url"],
                defaults={
                    "title": item["title"],
                    "summary": item["summary"],
                    "source": item["source"],
                    "category": item["category"],
                    "sentiment": item["sentiment"],
                    "symbols": item["symbols"],
                    "published_at": item["published_at"],
                },
            )
            saved += 1
        except Exception:
            pass

    # Giữ tối đa 500 tin, xóa cũ
    from crypto.models import NewsItem as NI
    count = NI.objects.count()
    if count > 500:
        old_ids = NI.objects.order_by("-published_at").values_list("id", flat=True)[400:]
        NI.objects.filter(id__in=list(old_ids)).delete()

    return saved


def _save_fear_greed(data: dict):
    from crypto.models import FearGreedSnapshot
    FearGreedSnapshot.objects.create(value=data["value"], label=data["label"])
    # Giữ tối đa 200 snapshots
    old = FearGreedSnapshot.objects.order_by("-timestamp").values_list("id", flat=True)[100:]
    if old:
        FearGreedSnapshot.objects.filter(id__in=list(old)).delete()


def _news_loop():
    time.sleep(30)  # Chờ Django khởi động xong

    while True:
        total = 0
        for source in RSS_SOURCES:
            items = _fetch_rss(source)
            if items:
                total += _save_news(items)

        fg = _fetch_fear_greed()
        if fg:
            try:
                _save_fear_greed(fg)
                logger.info(f"[news] Fear&Greed: {fg['value']} ({fg['label']})")
            except Exception:
                pass

        logger.info(f"[news] Saved {total} new items from {len(RSS_SOURCES)} sources.")
        time.sleep(5 * 60)  # 5 phút/lần


def start_news_feed():
    global _feed_started
    with _feed_lock:
        if _feed_started:
            return
        _feed_started = True
    t = threading.Thread(target=_news_loop, daemon=True, name="news_feed")
    t.start()
    logger.info("[news] News feed thread started.")


# ── Helper cho bots: lấy context tin tức ────────────────────────────────────

def get_news_context(limit: int = 10) -> str:
    """Trả về chuỗi tin tức gần nhất để inject vào market context."""
    try:
        from crypto.models import NewsItem, FearGreedSnapshot

        lines = []
        now = dj_tz.now()

        # Fear & Greed
        try:
            fg = FearGreedSnapshot.objects.latest("timestamp")
            age_min = int((now - fg.timestamp).total_seconds() / 60)
            fg_label = fg.label.upper()
            advice = ""
            if fg.value <= 20:
                advice = "→ EXTREME FEAR: co the la day thi truong, xem xet MUA"
            elif fg.value <= 40:
                advice = "→ FEAR: tam tinh thi truong xau, can than"
            elif fg.value >= 80:
                advice = "→ EXTREME GREED: co the la dinh, xem xet CHOT LOI / SHORT"
            elif fg.value >= 60:
                advice = "→ GREED: thi truong lac quan, giu long nhung chat stop"
            lines.append(f"FEAR & GREED INDEX: {fg.value}/100 ({fg_label}) {advice}")
        except Exception:
            lines.append("FEAR & GREED INDEX: khong co du lieu")

        lines.append("")

        # Tin tức gần nhất 6 giờ
        cutoff = now - timedelta(hours=6)
        news = NewsItem.objects.filter(published_at__gte=cutoff).order_by("-published_at")[:limit]

        if not news:
            lines.append("TIN TUC: Chua co tin tuc moi trong 6 gio qua.")
        else:
            lines.append(f"TIN TUC MOI NHAT (6h qua, {news.count()} tin):")
            for n in news:
                sentiment_icon = "🟢" if n.sentiment == "BULLISH" else "🔴" if n.sentiment == "BEARISH" else "⚪"
                symbols_str = f" [{n.symbols}]" if n.symbols else ""
                age_min = int((now - n.published_at).total_seconds() / 60)
                age_str = f"{age_min}p" if age_min < 60 else f"{age_min//60}h{age_min%60}p"
                lines.append(f"  {sentiment_icon} [{n.source}/{age_str}]{symbols_str} {n.title}")

        return "\n".join(lines)
    except Exception as e:
        logger.error(f"get_news_context: {e}")
        return "TIN TUC: Loi khi lay du lieu."

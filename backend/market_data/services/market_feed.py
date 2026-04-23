"""
Vòng lặp thị trường — tự động chạy khi Django khởi động.

Lịch:
  - Startup (ngoài giờ)  : fetch daily toàn bộ mã (~30 phút)
  - Giờ giao dịch        : fetch VN30 mỗi 30s qua intraday → realtime ~15s delay
  - Mỗi ngày 8:50        : fetch lại daily toàn bộ mã (giá tham chiếu)
  - Mỗi ngày 14:30       : chạy AI bots
"""
import logging
import threading
import time
from datetime import datetime, date
import zoneinfo

logger = logging.getLogger(__name__)

_TZ = zoneinfo.ZoneInfo("Asia/Ho_Chi_Minh")
_started = False
_start_lock = threading.Lock()

# ── Global rate limiter (chia sẻ giữa tất cả threads) ───────────────────────
_rate_lock = threading.Lock()
_rate_times: list = []


def _rate_wait():
    """Block cho đến khi có slot API (giới hạn 58 req/60s để có buffer)."""
    while True:
        with _rate_lock:
            now = time.monotonic()
            _rate_times[:] = [t for t in _rate_times if now - t < 60]
            if len(_rate_times) < 58:
                _rate_times.append(now)
                return
            oldest = _rate_times[0]
        wait = 61 - (time.monotonic() - oldest)
        if wait > 0:
            logger.info(f"[feed] Rate limit — chờ {wait:.0f}s...")
            time.sleep(max(1, wait))


# ── Helpers thời gian ────────────────────────────────────────────────────────

def _now():
    return datetime.now(_TZ)


def _is_market_open():
    n = _now()
    if n.weekday() >= 5:
        return False
    t = n.time()
    from datetime import time as dtime
    return (dtime(9, 0) <= t <= dtime(11, 30)) or (dtime(13, 0) <= t <= dtime(14, 45))


def _is_trading_day():
    return _now().weekday() < 5


# ── Fetch helpers ────────────────────────────────────────────────────────────

def _fetch_and_save(symbols):
    """Fetch + lưu giá cho danh sách mã. Dùng global rate limiter."""
    from market_data.services.vnstock_client import fetch_current_price
    from market_data.services.data_processor import save_price_snapshot

    saved = 0
    for symbol in symbols:
        _rate_wait()
        data = fetch_current_price(symbol)
        time.sleep(0.2)
        if data and save_price_snapshot(data):
            saved += 1
    return saved


def _get_active_symbols():
    from market_data.models import Stock
    return list(Stock.objects.filter(is_active=True).values_list("symbol", flat=True))


def _get_vn30_symbols():
    from market_data.services.vnstock_client import VN30_SYMBOLS
    return VN30_SYMBOLS


# ── Task threads ─────────────────────────────────────────────────────────────

def _run_daily_fetch(label="daily"):
    """Fetch giá daily toàn thị trường trong background thread."""
    try:
        symbols = _get_active_symbols()
        logger.info(f"[feed] Bắt đầu {label} fetch {len(symbols)} mã...")
        saved = _fetch_and_save(symbols)
        logger.info(f"[feed] Hoàn thành {label}: {saved}/{len(symbols)} mã.")
    except Exception as e:
        logger.error(f"[feed] Lỗi {label} fetch: {e}")


def _run_bots():
    """Chạy tất cả AI bot trader một lần."""
    try:
        from django.core.management import call_command
        logger.info("[bots] Bat dau chay AI bots...")
        call_command("run_bots")
        logger.info("[bots] Hoan thanh AI bots.")
    except Exception as e:
        logger.error(f"[bots] Loi chay bots: {e}")


def _pre_market_analysis():
    """Chạy 1 lần trước giờ mở cửa: bot đọc tin tức, phân tích, chuẩn bị lệnh."""
    try:
        from django.core.management import call_command
        logger.info("[bots] Pre-market: bat dau phan tich truoc gio mo cua...")
        call_command("run_bots", "--no-analyst")
        logger.info("[bots] Pre-market: hoan thanh.")
    except Exception as e:
        logger.error(f"[bots] Pre-market loi: {e}")


def _bot_continuous_loop():
    """
    Vòng lặp AI bots:
    - 8:30 trước mở cửa: chạy 1 lần phân tích pre-market
    - 9:00 - 11:30 và 13:00 - 14:45: chạy mỗi 5 phút
    - Ngoài giờ GD: ngủ, không chạy bot
    """
    from datetime import time as dtime

    time.sleep(45)

    pre_market_done_date = None  # Tránh chạy pre-market nhiều lần trong ngày

    while True:
        n = _now()
        t = n.time()
        today = n.date()

        # Pre-market analysis: 8:30 → 8:59, chỉ ngày thường
        if (n.weekday() < 5
                and dtime(8, 30) <= t < dtime(9, 0)
                and pre_market_done_date != today):
            pre_market_done_date = today
            _pre_market_analysis()
            time.sleep(60)
            continue

        # Trong giờ giao dịch: chạy bot, nghỉ 5 phút
        if _is_market_open():
            cycle_start = time.monotonic()
            _run_bots()
            elapsed = time.monotonic() - cycle_start
            sleep = max(0, 5 * 60 - elapsed)
            logger.info(f"[bots] Vong tiep theo sau {sleep/60:.1f} phut.")
            time.sleep(sleep)
        else:
            # Ngoài giờ GD: ngủ 60s rồi check lại
            time.sleep(60)


def _realtime_loop():
    """Vòng lặp realtime VN30 trong giờ giao dịch (30s/cycle)."""
    from market_data.services.data_processor import save_price_snapshot
    from market_data.services.vnstock_client import fetch_current_price

    vn30 = _get_vn30_symbols()

    while True:
        if not _is_market_open():
            time.sleep(15)
            continue

        cycle_start = time.monotonic()
        ok = 0
        for symbol in vn30:
            _rate_wait()  # Dùng global rate limiter — phối hợp với daily fetch
            data = fetch_current_price(symbol)
            time.sleep(0.2)
            if data and save_price_snapshot(data):
                ok += 1

        elapsed = time.monotonic() - cycle_start
        logger.info(f"[feed] Realtime VN30: {ok}/{len(vn30)} mã, {elapsed:.1f}s")

        sleep = max(0, 30 - elapsed)
        if sleep:
            time.sleep(sleep)


# ── Main entry point ─────────────────────────────────────────────────────────

def _main_loop():
    """Thread chính: khởi động daily fetch + bot loop + realtime loop."""
    time.sleep(3)

    n = _now()
    today = date.today()
    cur_min = n.hour * 60 + n.minute

    # Startup fetch toàn thị trường (chỉ ngoài giờ giao dịch)
    if not _is_market_open():
        threading.Thread(
            target=_run_daily_fetch, args=("startup",), daemon=True
        ).start()

    # Fetch daily 8:50 hàng ngày (cập nhật giá tham chiếu)
    last_fetch_date = today if cur_min >= 8 * 60 + 50 else None

    def _daily_fetch_scheduler():
        nonlocal last_fetch_date
        while True:
            _today = date.today()
            t = _now().hour * 60 + _now().minute
            if _is_trading_day() and t >= 8 * 60 + 50 and last_fetch_date != _today:
                last_fetch_date = _today
                threading.Thread(
                    target=_run_daily_fetch, args=("08:50",), daemon=True
                ).start()
            time.sleep(60)

    threading.Thread(target=_daily_fetch_scheduler, daemon=True).start()

    # Bot loop liên tục (5 phút/lần trong giờ GD, 30 phút/lần ngoài giờ)
    threading.Thread(target=_bot_continuous_loop, name="bot-loop", daemon=True).start()

    # Realtime loop VN30 (chạy mãi, tự ngủ khi ngoài giờ giao dịch)
    _realtime_loop()


def start():
    """Gọi từ AppConfig.ready() — chỉ khởi động 1 lần duy nhất."""
    global _started
    with _start_lock:
        if _started:
            return
        _started = True

    t = threading.Thread(target=_main_loop, name="market-feed", daemon=True)
    t.start()
    logger.info("[feed] Market feed thread started.")

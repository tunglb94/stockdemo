"""
Tổng hợp dữ liệu thị trường VN30 thành context đầy đủ cho LLM.
Bao gồm: giá thực, technical indicators, market breadth, top movers.
"""
from decimal import Decimal


def _compute_rsi(change_pcts: list, periods: int = 5) -> float | None:
    """RSI đơn giản từ danh sách % thay đổi gần nhất."""
    if len(change_pcts) < 2:
        return None
    gains = [c for c in change_pcts if c > 0]
    losses = [abs(c) for c in change_pcts if c < 0]
    avg_gain = sum(gains) / periods if gains else 0
    avg_loss = sum(losses) / periods if losses else 0
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 1)


def _price_position(cur, low, high) -> float:
    """Vị trí giá trong khoảng [sàn, trần] ngày, 0-100%."""
    if high <= low:
        return 50.0
    return round((cur - low) / (high - low) * 100, 1)


def build_market_context(portfolio: dict, wallet_balance: Decimal) -> str:
    """
    Tạo context thị trường đầy đủ cho LLM phân tích.
    portfolio: {symbol: {quantity, avg_cost, current_price, pnl_pct}}
    """
    from market_data.models import Stock

    stocks = list(
        Stock.objects.filter(is_vn30=True, is_active=True)
        .prefetch_related("snapshots")
        .order_by("symbol")
    )

    lines = ["=== DỮ LIỆU THỊ TRƯỜNG VN30 ===\n"]
    lines.append(
        f"{'Mã':<6} {'Giá':>7} {'Ref':>7} {'%':>7} {'Pos%':>5} "
        f"{'RSI':>5} {'Cao':>7} {'Thấp':>7} {'KL(K)':>8}"
    )
    lines.append("-" * 70)

    up, down, flat = 0, 0, 0
    top_gainers, top_losers = [], []
    total_volume = 0

    for stock in stocks:
        try:
            snap = stock.snapshots.latest("timestamp")
        except Exception:
            continue

        cur = float(snap.current_price)
        ref = float(snap.reference_price) or cur
        high = float(snap.high_price or cur)
        low = float(snap.low_price or cur)
        vol = snap.volume or 0
        pct = float(snap.change_percent)
        ceil_p = float(snap.ceiling_price or ref * 1.07)
        floor_p = float(snap.floor_price or ref * 0.93)

        total_volume += vol

        # RSI từ các snapshot gần đây trong DB
        recent_snaps = stock.snapshots.order_by("-timestamp")[:10]
        change_history = [float(s.change_percent) for s in recent_snaps]
        rsi = _compute_rsi(change_history)
        rsi_str = f"{rsi:.0f}" if rsi is not None else "N/A"

        pos = _price_position(cur, low, high)

        if pct > 0:
            up += 1
            arrow = "▲"
        elif pct < 0:
            down += 1
            arrow = "▼"
        else:
            flat += 1
            arrow = "─"

        # Đánh dấu gần trần/sàn
        ceiling_dist = (ceil_p - cur) / cur * 100
        floor_dist = (cur - floor_p) / cur * 100
        flag = ""
        if ceiling_dist < 1.5:
            flag = " [GẦN TRẦN]"
        elif floor_dist < 1.5:
            flag = " [GẦN SÀN]"

        lines.append(
            f"{stock.symbol:<6} {cur/1000:>7.2f} {ref/1000:>7.2f} "
            f"{arrow}{pct:>+6.2f}% {pos:>5.0f}% {rsi_str:>5} "
            f"{high/1000:>7.2f} {low/1000:>7.2f} {vol//1000:>7,}K{flag}"
        )

        top_gainers.append((stock.symbol, pct, cur, vol))
        top_losers.append((stock.symbol, pct, cur, vol))

    # Market breadth
    lines.append(f"\n{'='*70}")
    lines.append(f"TỔNG QUAN THỊ TRƯỜNG:")
    lines.append(f"  Tăng: {up} mã  |  Đứng: {flat} mã  |  Giảm: {down} mã")
    total_active = up + flat + down
    if total_active > 0:
        breadth = up / total_active * 100
        trend_label = "BULLISH 🟢" if breadth > 60 else "BEARISH 🔴" if breadth < 40 else "SIDEWAYS 🟡"
        lines.append(f"  Advance/Decline ratio: {breadth:.0f}% tăng → {trend_label}")
    lines.append(f"  Tổng volume VN30: {total_volume//1000:,}K cổ")

    # Top 5 tăng mạnh nhất
    top_gainers.sort(key=lambda x: -x[1])
    lines.append(f"\nTOP 5 TĂNG MẠNH NHẤT:")
    for sym, pct, cur, vol in top_gainers[:5]:
        lines.append(f"  {sym:<6} {pct:>+6.2f}%  giá {cur/1000:.2f}  KL {vol//1000:,}K")

    # Top 5 giảm mạnh nhất
    top_losers.sort(key=lambda x: x[1])
    lines.append(f"\nTOP 5 GIẢM MẠNH NHẤT:")
    for sym, pct, cur, vol in top_losers[:5]:
        lines.append(f"  {sym:<6} {pct:>+6.2f}%  giá {cur/1000:.2f}  KL {vol//1000:,}K")

    # Tín hiệu kỹ thuật tổng hợp
    lines.append(f"\nTÍN HIỆU KỸ THUẬT:")
    overbought = [s.symbol for s in stocks
                  if _get_rsi(s) and _get_rsi(s) > 70]
    oversold = [s.symbol for s in stocks
                if _get_rsi(s) and _get_rsi(s) < 30]
    if overbought:
        lines.append(f"  Overbought (RSI>70): {', '.join(overbought)}")
    if oversold:
        lines.append(f"  Oversold (RSI<30): {', '.join(oversold)}")

    # Danh mục bot hiện tại
    lines.append(f"\n{'='*70}")
    lines.append("DANH MỤC HIỆN TẠI CỦA BẠN:")
    lines.append(f"  Tiền mặt khả dụng: {float(wallet_balance):>15,.0f} VNĐ")

    if portfolio:
        total_stock_val = sum(
            p["quantity"] * p["current_price"] for p in portfolio.values()
        )
        total_val = float(wallet_balance) + total_stock_val
        cash_pct = float(wallet_balance) / total_val * 100 if total_val else 100
        lines.append(f"  Tổng tài sản:      {total_val:>15,.0f} VNĐ")
        lines.append(f"  Tỷ lệ tiền mặt:    {cash_pct:.1f}%")
        lines.append(f"\n  {'Mã':<6} {'SL':>6} {'Giá vốn':>9} {'Hiện tại':>9} {'P&L%':>8} {'Trạng thái'}")
        lines.append(f"  {'-'*55}")
        for sym, pos in portfolio.items():
            pnl = pos["pnl_pct"]
            avail = pos.get("available_quantity", 0)
            status = "✅ Bán được" if avail > 0 else "⏳ Chờ T+2"
            pnl_icon = "📈" if pnl > 0 else "📉"
            lines.append(
                f"  {sym:<6} {pos['quantity']:>6}  "
                f"{pos['avg_cost']/1000:>8.2f}  "
                f"{pos['current_price']/1000:>8.2f}  "
                f"{pnl_icon}{pnl:>+6.2f}%  {status}"
            )
    else:
        lines.append("  Danh mục trống — chưa có cổ phiếu nào.")

    lines.append(f"\n{'='*70}")
    lines.append("YÊU CẦU PHÂN TÍCH:")
    lines.append(
        "Dựa trên dữ liệu thực trên, áp dụng chiến lược của bạn để quyết định giao dịch NGAY BÂY GIỜ.\n"
        "Lưu ý:\n"
        "- Lô tối thiểu 100 cổ\n"
        "- Phí mua 0.15%, thuế bán 0.1%\n"
        "- Cổ phiếu vừa mua phải T+2 mới bán được\n"
        "- Chỉ bán những mã có trạng thái 'Bán được' trong danh mục\n"
        "- Không mua nếu tiền mặt không đủ"
    )

    return "\n".join(lines)


def _get_rsi(stock) -> float | None:
    """Helper lấy RSI cho 1 stock."""
    try:
        snaps = stock.snapshots.order_by("-timestamp")[:10]
        changes = [float(s.change_percent) for s in snaps]
        return _compute_rsi(changes)
    except Exception:
        return None


def get_portfolio_state(user) -> dict:
    """Lấy trạng thái danh mục của bot."""
    from trading.models import Portfolio

    result = {}
    for pos in Portfolio.objects.filter(user=user).select_related("stock"):
        try:
            snap = pos.stock.snapshots.latest("timestamp")
            cur = float(snap.current_price)
        except Exception:
            cur = float(pos.avg_cost)

        avg = float(pos.avg_cost)
        pnl_pct = (cur - avg) / avg * 100 if avg else 0
        result[pos.stock.symbol] = {
            "quantity": pos.quantity,
            "available_quantity": pos.available_quantity,
            "avg_cost": avg,
            "current_price": cur,
            "pnl_pct": round(pnl_pct, 2),
        }
    return result

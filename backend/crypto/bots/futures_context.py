from decimal import Decimal


def build_futures_context(positions: dict, balance_usd: Decimal) -> str:
    from crypto.models import CryptoAsset

    lines = [
        "=== FUTURES MARKET — LONG/SHORT (CRYPTO + COMMODITY) ===",
        f"Balance: ${float(balance_usd):.2f} USD",
        "",
    ]

    btc_chg = eth_chg = 0.0
    gainers, losers = [], []
    commodity_lines, crypto_lines = [], []

    for asset in CryptoAsset.objects.filter(is_active=True).order_by("rank"):
        try:
            snap = asset.snapshots.latest("timestamp")
            price = float(snap.price_usd)
            chg = snap.change_24h
            p_str = f"${price:,.2f}" if price >= 1000 else f"${price:.4f}" if price >= 1 else f"${price:.6f}"
            row = f"  {asset.symbol:8}: {p_str:>14} ({chg:+.2f}%)"

            if asset.category == "COMMODITY":
                commodity_lines.append(row)
            else:
                crypto_lines.append(row)
                if asset.symbol == "BTC":
                    btc_chg = chg
                elif asset.symbol == "ETH":
                    eth_chg = chg
                if chg >= 5:
                    gainers.append((asset.symbol, chg))
                elif chg <= -5:
                    losers.append((asset.symbol, chg))
        except Exception:
            pass

    # Commodities đầu tiên để LLM chú ý
    lines.append("--- HANG HOA (COMMODITY) — LONG/SHORT duoc ---")
    lines.append("  XAU=Vang | XAG=Bac | XPT=Platinum | COPPER=Dong")
    lines.append("  WTI=Dau My | BRENT=Dau QT | NATGAS=Khi gas")
    lines.append("  WHEAT=Lua mi | CORN=Ngo | COFFEE | SUGAR | COTTON")
    lines += commodity_lines

    lines += ["", "--- CRYPTO ---"]
    lines += crypto_lines

    if btc_chg > 2 and eth_chg > 1:
        sentiment = "BULLISH — xem xet LONG crypto + commodity cyclical (COPPER, OIL)"
    elif btc_chg < -2 and eth_chg < -1:
        sentiment = "BEARISH — xem xet SHORT crypto, LONG safe-haven (XAU, XAG)"
    else:
        sentiment = "SIDEWAYS — tim co hoi o commodity hoac altcoin bien dong cao"

    lines += [
        "",
        f"--- THI TRUONG: {sentiment} ---",
        f"  BTC: {btc_chg:+.2f}% | ETH: {eth_chg:+.2f}%",
    ]

    if gainers:
        lines.append("Overbought (SHORT?): " + ", ".join(f"{s}({c:+.1f}%)" for s, c in sorted(gainers, key=lambda x: -x[1])[:5]))
    if losers:
        lines.append("Oversold (LONG?): " + ", ".join(f"{s}({c:.1f}%)" for s, c in sorted(losers, key=lambda x: x[1])[:5]))

    # Open positions
    lines += ["", "--- VI TRI DANG MO ---"]
    if positions:
        total_upnl = 0.0
        for key, pos in positions.items():
            upnl = pos["unrealized_pnl"]
            total_upnl += upnl
            lines.append(
                f"  {pos['direction']} {pos['symbol']}: entry=${pos['entry_price']:.4f} | now=${pos['current_price']:.4f} | "
                f"margin=${pos['margin_usd']:.0f} x{pos['leverage']} | uPnL: {'+' if upnl >= 0 else ''}{upnl:.2f}$ | liq=${pos['liq_price']:.2f}"
            )
        lines.append(f"  Tong unrealized PnL: {'+' if total_upnl >= 0 else ''}{total_upnl:.2f}$")
    else:
        lines.append("  Khong co vi tri nao dang mo.")

    # News context
    try:
        from crypto.services.news_feed import get_news_context
        lines += ["", "=" * 50]
        lines.append(get_news_context(limit=12))
    except Exception:
        pass

    lines.append("\nHay quyet dinh LONG/SHORT/CLOSE/HOLD cho vong nay.")
    return "\n".join(lines)

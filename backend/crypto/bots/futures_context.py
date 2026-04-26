"""
Futures market context builder.
Preprocesses raw market data into ranked trading opportunities for the AI.
Key insight: give the AI conclusions, not raw data — like a trading desk analyst.
"""
from decimal import Decimal
from datetime import datetime, timezone as tz

# Liquidity tier weights — higher = more reliable momentum signal
TIER_WEIGHT = {
    "BTC": 1.5, "ETH": 1.4, "SOL": 1.3, "XAU": 1.3, "XAG": 1.2,
    "BNB": 1.2, "XRP": 1.1, "AVAX": 1.1, "LINK": 1.1, "ATOM": 1.1,
    "TON": 1.0, "NEAR": 1.0, "OP": 1.0, "ARB": 1.0, "INJ": 1.0,
    "WTI": 1.1, "BRENT": 1.1, "COPPER": 1.0, "NATGAS": 0.9,
    "WHEAT": 0.9, "CORN": 0.9, "COFFEE": 0.9,
}
DEFAULT_WEIGHT   = 0.85
MIN_MOVE_FOR_OPP = 2.5   # minimum 24h % move to be listed as opportunity


def get_session() -> tuple:
    h = datetime.now(tz.utc).hour
    if 0 <= h < 8:
        return "ASIA (00–08 UTC)", "low volume, ranging expected — prefer tighter leverage (8–12x)"
    elif 8 <= h < 13:
        return "LONDON (08–13 UTC)", "medium volume, liquidity sweeps common at open — wait for confirmation"
    else:
        return "US (13–22 UTC)", "highest volume, strongest trends — breakouts more reliable, use full leverage"


def portfolio_heat(positions: dict, balance_usd: Decimal) -> tuple:
    used = sum(Decimal(str(p["margin_usd"])) for p in positions.values())
    total = balance_usd + used
    pct = float(used / total * 100) if total else 0
    if pct > 65:
        return pct, "🔴 HOT — >65% deployed. CLOSE positions or HOLD only. No new entries."
    elif pct > 45:
        return pct, f"🟡 WARM — {pct:.0f}% deployed. Max 1 new position, margin ≤ $400."
    else:
        return pct, f"🟢 COOL — {pct:.0f}% deployed. OK to open 1–2 positions."


def leverage_hint(score: float) -> str:
    if score >= 6.0: return "15–20x"
    if score >= 4.0: return "12–15x"
    if score >= 2.5: return "8–12x"
    return "skip"


def get_futures_lessons(bot_username: str) -> str:
    """Lấy lessons liên quan đến futures trading để inject vào context của phi4."""
    try:
        from crypto.models import LearnedLesson
        from django.db.models import Q

        # Futures-relevant tags
        FUTURES_TAGS = ["universal", "momentum", "timing", "macro", "scalper", "contrarian"]

        tag_filter = Q()
        for tag in FUTURES_TAGS:
            tag_filter |= Q(tags__icontains=tag)

        lessons = list(
            LearnedLesson.objects.filter(is_active=True).filter(tag_filter)
            .order_by("-quality_score", "-created_at")[:8]
        )

        if not lessons:
            return ""

        lines = ["", "--- LESSONS FROM PAST TRADES (apply if relevant) ---"]
        for lesson in lessons:
            pnl = f" | PnL: {lesson.pnl_at_extraction:+.1f}%" if lesson.pnl_at_extraction is not None else ""
            prefix = "+" if lesson.polarity == "GOOD" else "!"
            lines.append(f"  [{prefix}] [{lesson.source_bot}{pnl}] {lesson.lesson_text}")
        return "\n".join(lines)
    except Exception:
        return ""


def build_futures_context(positions: dict, balance_usd: Decimal, bot_username: str = "") -> str:
    from crypto.models import CryptoAsset

    session_name, session_note = get_session()
    _, heat_label = portfolio_heat(positions, balance_usd)

    lines = [
        "=== TRADING DESK BRIEFING ===",
        f"Session   : {session_name}",
        f"Note      : {session_note}",
        f"Heat      : {heat_label}",
        f"Balance   : ${float(balance_usd):.2f} free  |  {len(positions)}/10 slots used",
        "",
    ]

    # ── Collect market data ───────────────────────────────────────────────────
    btc_chg = eth_chg = 0.0
    long_opps  = []   # (score, symbol, chg, price)
    short_opps = []
    all_rows   = {"COMMODITY": [], "CRYPTO": []}

    for asset in CryptoAsset.objects.filter(is_active=True).order_by("rank"):
        try:
            snap  = asset.snapshots.latest("timestamp")
            price = float(snap.price_usd)
            chg   = snap.change_24h
            w     = TIER_WEIGHT.get(asset.symbol, DEFAULT_WEIGHT)
            score = abs(chg) * w

            p_str = (f"${price:,.2f}"  if price >= 1000 else
                     f"${price:.4f}"   if price >= 1    else
                     f"${price:.6f}")
            row = f"  {asset.symbol:8}: {p_str:>14}  {chg:+.2f}%"
            cat = "COMMODITY" if asset.category == "COMMODITY" else "CRYPTO"
            all_rows[cat].append(row)

            if asset.symbol == "BTC": btc_chg = chg
            if asset.symbol == "ETH": eth_chg = chg

            if abs(chg) >= MIN_MOVE_FOR_OPP:
                if chg < 0: long_opps.append((score, asset.symbol, chg, price))
                else:       short_opps.append((score, asset.symbol, chg, price))
        except Exception:
            pass

    # ── Market regime ────────────────────────────────────────────────────────
    if btc_chg > 3 and eth_chg > 2:
        regime      = "BULL TREND"
        regime_note = "Strong upward momentum — LONG bias. Avoid counter-trend SHORTs."
    elif btc_chg < -3 and eth_chg < -2:
        regime      = "BEAR TREND"
        regime_note = "Strong downward momentum — SHORT bias. LONG only XAU/safe-haven."
    elif abs(btc_chg) < 1 and abs(eth_chg) < 1:
        regime      = "RANGING"
        regime_note = "Low vol — trade commodities or high-vol alts only. Reduce leverage."
    else:
        regime      = "MIXED"
        regime_note = "No clear macro direction — trade individual asset momentum."

    lines += [
        f"--- REGIME: {regime} ---",
        f"  BTC {btc_chg:+.2f}%  ETH {eth_chg:+.2f}%  |  {regime_note}",
        "",
    ]

    # ── Ranked opportunities (core intelligence) ──────────────────────────────
    lines.append("--- RANKED OPPORTUNITIES (pre-scored, act on these) ---")

    long_opps  = sorted(long_opps,  reverse=True)[:6]
    short_opps = sorted(short_opps, reverse=True)[:6]

    if long_opps:
        lines.append("  LONG — oversold (sorted by opportunity score):")
        for rank, (score, sym, chg, price) in enumerate(long_opps, 1):
            lev = leverage_hint(score)
            already = any(p["symbol"] == sym and p["direction"] == "LONG"
                          for p in positions.values())
            tag = "  [already open]" if already else ""
            lines.append(f"    #{rank} {sym:8} {chg:+.2f}%  score={score:.1f}  → {lev}{tag}")
    else:
        lines.append("  LONG candidates: none clearing threshold today")

    if short_opps:
        lines.append("  SHORT — overbought (sorted by opportunity score):")
        for rank, (score, sym, chg, price) in enumerate(short_opps, 1):
            lev = leverage_hint(score)
            already = any(p["symbol"] == sym and p["direction"] == "SHORT"
                          for p in positions.values())
            tag = "  [already open]" if already else ""
            lines.append(f"    #{rank} {sym:8} {chg:+.2f}%  score={score:.1f}  → {lev}{tag}")
    else:
        lines.append("  SHORT candidates: none clearing threshold today")

    # ── Price tables — commodities full, crypto top-15 only ─────────────────
    # Full ranked opportunities already listed above — only reference prices needed here
    lines += ["", "--- COMMODITIES ---"]
    lines += all_rows["COMMODITY"]
    lines += ["", "--- CRYPTO (top 15 by rank) ---"]
    lines += all_rows["CRYPTO"][:15]   # BTC ETH BNB SOL XRP DOGE ADA AVAX SHIB TRX TON LINK DOT POL LTC
    lines.append("  ... (others in ranked opportunities above)")

    # ── Open positions with management hints ─────────────────────────────────
    lines += ["", "--- OPEN POSITIONS ---"]
    if positions:
        total_upnl = 0.0
        for pos in positions.values():
            upnl     = pos["unrealized_pnl"]
            gain_pct = pos["gain_pct_of_margin"]
            loss_pct = pos["loss_pct_of_margin"]
            age_h    = pos["age_hours"]
            total_upnl += upnl
            sgn = "+" if upnl >= 0 else ""

            # Management recommendation
            if loss_pct >= 25:
                mgmt = "⚠ CLOSE IMMEDIATELY — approaching -30% auto stop-loss"
            elif loss_pct >= 20:
                mgmt = "⚠ CLOSE — hit -20% manual cut threshold"
            elif gain_pct >= 40:
                mgmt = "✓ AUTO TAKE-PROFIT will trigger this round"
            elif gain_pct >= 30:
                mgmt = "✓ CLOSE — lock in profit (>+30% margin)"
            elif gain_pct >= 15:
                mgmt = "~ Let it run OR close to protect profit"
            elif age_h > 2.0 and -20 < gain_pct < 5:
                mgmt = f"⏱ TIME-STOP — {age_h:.1f}h open, not profitable, consider closing"
            else:
                mgmt = f"Holding {age_h:.1f}h"

            lines.append(
                f"  {pos['direction']:5} {pos['symbol']:8}  "
                f"margin=${pos['margin_usd']:.0f} x{pos['leverage']}  "
                f"entry=${pos['entry_price']:.4f} → now=${pos['current_price']:.4f}  "
                f"uPnL: {sgn}${upnl:.2f} ({gain_pct:+.1f}%)  "
                f"liq=${pos['liq_price']:.2f}  |  {mgmt}"
            )
        lines.append(f"  Σ unrealized: {'+' if total_upnl >= 0 else ''}${total_upnl:.2f}")
        lines.append(
            "  [Auto-managed: stop-loss -30%, take-profit +40%, time-stop 2h. "
            "Max 10 positions, no duplicate symbol+direction, heat cap 70%.]"
        )
    else:
        lines.append("  No open positions — deploy capital into top opportunities above.")

    # ── News ─────────────────────────────────────────────────────────────────
    try:
        from crypto.services.news_feed import get_news_context
        news = get_news_context(limit=8)
        if news and news.strip():
            lines += ["", "--- MARKET NEWS (factor into decisions) ---", news]
    except Exception:
        pass

    # ── Learned lessons ───────────────────────────────────────────────────────
    if bot_username:
        lesson_block = get_futures_lessons(bot_username)
        if lesson_block:
            lines.append(lesson_block)

    lines += [
        "",
        "Your turn: output LONG/SHORT/CLOSE/HOLD decisions.",
        "Prioritize the ranked opportunities. Match leverage to score. Respect heat level.",
    ]
    return "\n".join(lines)

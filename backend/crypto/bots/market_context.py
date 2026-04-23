from decimal import Decimal


def get_crypto_portfolio_state(user) -> dict:
    from crypto.models import CryptoPortfolio

    portfolio = {}
    for pos in CryptoPortfolio.objects.filter(user=user).select_related("asset"):
        try:
            snap = pos.asset.snapshots.latest("timestamp")
            cur = float(snap.price_usd)
        except Exception:
            cur = float(pos.avg_cost_usd)
        portfolio[pos.asset.symbol] = {
            "quantity": float(pos.quantity),
            "avg_cost": float(pos.avg_cost_usd),
            "current_price": cur,
        }
    return portfolio


def build_crypto_context(portfolio: dict, balance_usd: Decimal) -> str:
    from crypto.models import CryptoAsset

    lines = [
        "=== CRYPTO & COMMODITY MARKET DATA ===",
        f"USD balance: ${float(balance_usd):.2f}",
        "",
    ]

    gainers, losers = [], []
    btc_chg = eth_chg = 0.0
    crypto_lines, commodity_lines = [], []

    for asset in CryptoAsset.objects.filter(is_active=True).order_by("rank"):
        try:
            snap = asset.snapshots.latest("timestamp")
            price = float(snap.price_usd)
            chg = snap.change_24h
            p_str = f"${price:,.2f}" if price >= 1000 else f"${price:.4f}" if price >= 1 else f"${price:.8f}"
            sign = "+" if chg >= 0 else ""
            row = f"  {asset.symbol:8}: {p_str:>14} ({sign}{chg:.2f}%)"

            if asset.category == "COMMODITY":
                commodity_lines.append(row)
            else:
                crypto_lines.append(row)
                if asset.symbol == "BTC":
                    btc_chg = chg
                elif asset.symbol == "ETH":
                    eth_chg = chg
                if chg >= 4:
                    gainers.append((asset.symbol, chg))
                elif chg <= -4:
                    losers.append((asset.symbol, chg))
        except Exception:
            pass

    # Commodities nổi bật lên đầu để LLM chú ý
    lines.append("--- HANG HOA (COMMODITY) — co the mua/ban truc tiep ---")
    lines.append("  [Kim loai quy] XAU=Vang | XAG=Bac | XPT=Platinum | COPPER=Dong")
    lines.append("  [Nang luong]   WTI=Dau Tho My | BRENT=Dau Tho QT | NATGAS=Khi Tu Nhien")
    lines.append("  [Nong san]     WHEAT=Lua Mi | CORN=Ngo | COFFEE=Ca Phe | SUGAR=Duong | COTTON=Bong")
    lines += commodity_lines

    # Crypto
    lines += ["", "--- CRYPTO (60 ma) ---"]
    lines += crypto_lines

    # Sentiment
    if btc_chg > 2 and eth_chg > 1:
        sentiment = "BULLISH"
    elif btc_chg < -2 and eth_chg < -1:
        sentiment = "BEARISH"
    else:
        sentiment = "MIXED/SIDEWAYS"

    lines += [
        "",
        f"--- XU HUONG: BTC {btc_chg:+.2f}% | ETH {eth_chg:+.2f}% | {sentiment} ---",
    ]

    if gainers:
        lines.append("Top tang manh: " + ", ".join(f"{s}({c:+.1f}%)" for s, c in sorted(gainers, key=lambda x: -x[1])[:5]))
    if losers:
        lines.append("Top giam manh: " + ", ".join(f"{s}({c:.1f}%)" for s, c in sorted(losers, key=lambda x: x[1])[:5]))

    # Portfolio
    lines += ["", "--- DANH MUC CUA BAN ---"]
    if portfolio:
        total_value = Decimal("0")
        for sym, pos in portfolio.items():
            val = Decimal(str(pos["current_price"])) * Decimal(str(pos["quantity"]))
            total_value += val
            pnl = (pos["current_price"] - pos["avg_cost"]) / pos["avg_cost"] * 100 if pos["avg_cost"] else 0
            qty_str = f"{pos['quantity']:.6f}" if pos["quantity"] < 1 else f"{pos['quantity']:.4f}"
            lines.append(
                f"  {sym}: {qty_str} don vi @ ${pos['avg_cost']:.4f} | hien tai ${pos['current_price']:.4f} | PnL: {pnl:+.2f}% | Gia tri: ${float(val):.2f}"
            )
        total_assets = float(balance_usd) + float(total_value)
        lines.append(f"  Tong danh muc: ${float(total_value):.2f} | Tong tai san: ${total_assets:.2f}")
    else:
        lines.append("  Khong co tai san, toan bo la USD.")

    # News context
    try:
        from crypto.services.news_feed import get_news_context
        lines += ["", "=" * 50]
        lines.append(get_news_context(limit=12))
    except Exception:
        pass

    lines.append("\nHay dua ra quyet dinh giao dich cho vong nay.")
    return "\n".join(lines)

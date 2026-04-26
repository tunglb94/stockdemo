import json
import time
from decimal import Decimal, InvalidOperation
from zoneinfo import ZoneInfo
from django.http import StreamingHttpResponse
from django.views import View
from django.db.models import Subquery, OuterRef
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import get_user_model

User = get_user_model()
START_CAPITAL_USD = Decimal("5000")
_VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")


def _fmt_vn(dt) -> str:
    """Format UTC datetime → Vietnam time (UTC+7) string."""
    if not dt:
        return ""
    return dt.astimezone(_VN_TZ).strftime("%d/%m %H:%M")


def _fetch_market_data():
    """Single efficient query — returns all asset prices (no N+1)."""
    from crypto.models import CryptoAsset, CryptoSnapshot

    latest = CryptoSnapshot.objects.filter(
        asset=OuterRef("pk")
    ).order_by("-timestamp")

    rows = list(
        CryptoAsset.objects.filter(is_active=True)
        .annotate(
            snap_price=Subquery(latest.values("price_usd")[:1]),
            snap_change=Subquery(latest.values("change_24h")[:1]),
            snap_volume=Subquery(latest.values("volume_24h")[:1]),
            snap_mcap=Subquery(latest.values("market_cap")[:1]),
            snap_ts=Subquery(latest.values("timestamp")[:1]),
        )
        .order_by("rank")
        .values("symbol", "name", "category", "rank",
                "snap_price", "snap_change", "snap_volume", "snap_mcap", "snap_ts")
    )

    result = []
    for r in rows:
        result.append({
            "symbol":     r["symbol"],
            "name":       r["name"],
            "category":   r["category"],
            "rank":       r["rank"],
            "price":      float(r["snap_price"])  if r["snap_price"]  else 0,
            "change_24h": round(float(r["snap_change"]), 4) if r["snap_change"] else 0,
            "volume_24h": float(r["snap_volume"]) if r["snap_volume"] else 0,
            "market_cap": float(r["snap_mcap"])   if r["snap_mcap"]   else 0,
            "updated_at": r["snap_ts"].strftime("%H:%M:%S") if r["snap_ts"] else None,
        })
    return result


class CryptoMarketView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response(_fetch_market_data())


class CryptoPriceStreamView(View):
    """SSE — pushes price updates every 2s. Only sends when data changes."""

    def get(self, request):
        def stream():
            last_json = None
            while True:
                try:
                    data = _fetch_market_data()
                    # Send only prices + change (lightweight diff payload)
                    prices = [
                        {"symbol": d["symbol"], "price": d["price"],
                         "change_24h": d["change_24h"], "updated_at": d["updated_at"]}
                        for d in data
                    ]
                    serialized = json.dumps(prices)
                    if serialized != last_json:
                        last_json = serialized
                        yield f"data: {serialized}\n\n"
                    else:
                        yield ": heartbeat\n\n"   # keep connection alive
                except Exception as e:
                    yield f": error {e}\n\n"
                time.sleep(2)

        resp = StreamingHttpResponse(stream(), content_type="text/event-stream; charset=utf-8")
        resp["Cache-Control"] = "no-cache, no-store"
        resp["X-Accel-Buffering"] = "no"   # disable nginx buffering
        return resp


class CryptoPortfolioView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from crypto.models import CryptoWallet, CryptoPortfolio, CryptoOrder

        wallet, _ = CryptoWallet.objects.get_or_create(
            user=request.user, defaults={"balance_usd": Decimal("0")}
        )

        holdings = []
        asset_value = Decimal("0")
        for pos in CryptoPortfolio.objects.filter(user=request.user).select_related("asset"):
            try:
                snap = pos.asset.snapshots.latest("timestamp")
                cur = snap.price_usd
            except Exception:
                cur = pos.avg_cost_usd

            value = cur * pos.quantity
            asset_value += value
            pnl_pct = float((cur - pos.avg_cost_usd) / pos.avg_cost_usd * 100) if pos.avg_cost_usd else 0
            holdings.append({
                "symbol": pos.asset.symbol,
                "name": pos.asset.name,
                "quantity": float(pos.quantity),
                "avg_cost": float(pos.avg_cost_usd),
                "current_price": float(cur),
                "value_usd": float(value),
                "pnl_pct": round(pnl_pct, 2),
            })

        orders = CryptoOrder.objects.filter(user=request.user).select_related("asset")[:30]

        return Response({
            "balance_usd": float(wallet.balance_usd),
            "frozen_usd": float(wallet.frozen_usd),
            "available_usd": float(wallet.available),
            "asset_value_usd": float(asset_value),
            "total_usd": float(wallet.balance_usd + asset_value),
            "holdings": sorted(holdings, key=lambda x: -x["value_usd"]),
            "orders": [
                {
                    "symbol": o.asset.symbol,
                    "side": o.side,
                    "quantity": float(o.quantity),
                    "price": float(o.price_usd),
                    "total": float(o.total_usd),
                    "status": o.status,
                    "created_at": o.created_at.strftime("%d/%m %H:%M"),
                }
                for o in orders
            ],
        })


class CryptoTradeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from crypto.models import CryptoAsset, CryptoWallet, CryptoPortfolio, CryptoOrder

        symbol = str(request.data.get("symbol", "")).upper()
        side = str(request.data.get("side", "")).upper()
        try:
            quantity = Decimal(str(request.data.get("quantity", 0)))
        except (InvalidOperation, TypeError):
            return Response({"error": "Invalid quantity"}, status=400)

        if side not in ("BUY", "SELL") or quantity <= 0:
            return Response({"error": "Invalid input"}, status=400)

        try:
            asset = CryptoAsset.objects.get(symbol=symbol, is_active=True)
        except CryptoAsset.DoesNotExist:
            return Response({"error": "Asset not found"}, status=404)

        try:
            snap = asset.snapshots.latest("timestamp")
            price = snap.price_usd
        except Exception:
            return Response({"error": "No price data"}, status=400)

        total = price * quantity
        wallet, _ = CryptoWallet.objects.get_or_create(
            user=request.user, defaults={"balance_usd": Decimal("0")}
        )

        if side == "BUY":
            if total > wallet.available:
                return Response({"error": f"Khong du USD. Can ${float(total):.2f}, co ${float(wallet.available):.2f}"}, status=400)
            wallet.balance_usd -= total
            wallet.save(update_fields=["balance_usd"])

            pos, _ = CryptoPortfolio.objects.get_or_create(
                user=request.user, asset=asset,
                defaults={"quantity": Decimal("0"), "avg_cost_usd": price},
            )
            new_qty = pos.quantity + quantity
            pos.avg_cost_usd = (pos.avg_cost_usd * pos.quantity + price * quantity) / new_qty
            pos.quantity = new_qty
            pos.save()

        elif side == "SELL":
            try:
                pos = CryptoPortfolio.objects.get(user=request.user, asset=asset)
            except CryptoPortfolio.DoesNotExist:
                return Response({"error": "Khong co tai san de ban"}, status=400)
            if quantity > pos.quantity:
                return Response({"error": f"Khong du tai san. Co {float(pos.quantity):.8f}"}, status=400)

            wallet.balance_usd += total
            wallet.save(update_fields=["balance_usd"])
            pos.quantity -= quantity
            if pos.quantity <= Decimal("0.00000001"):
                pos.delete()
            else:
                pos.save(update_fields=["quantity"])

        CryptoOrder.objects.create(
            user=request.user, asset=asset, side=side,
            quantity=quantity, price_usd=price, total_usd=total,
        )
        return Response({
            "ok": True, "symbol": symbol, "side": side,
            "quantity": float(quantity), "price": float(price), "total": float(total),
        })


class CryptoBotLeaderboardView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        from crypto.bots.definitions import CRYPTO_BOTS
        from crypto.models import CryptoWallet, CryptoPortfolio, CryptoOrder

        results = []
        for bot_def in CRYPTO_BOTS:
            try:
                user = User.objects.get(email=bot_def["email"])
                wallet = CryptoWallet.objects.get(user=user)
            except Exception:
                continue

            asset_value = Decimal("0")
            holdings = []
            for pos in CryptoPortfolio.objects.filter(user=user).select_related("asset"):
                try:
                    snap = pos.asset.snapshots.latest("timestamp")
                    cur = snap.price_usd
                except Exception:
                    cur = pos.avg_cost_usd

                value = cur * pos.quantity
                asset_value += value
                pnl_pct = float((cur - pos.avg_cost_usd) / pos.avg_cost_usd * 100) if pos.avg_cost_usd else 0
                holdings.append({
                    "symbol": pos.asset.symbol,
                    "quantity": float(pos.quantity),
                    "avg_cost": float(pos.avg_cost_usd),
                    "current_price": float(cur),
                    "value_usd": float(value),
                    "pnl_pct": round(pnl_pct, 2),
                })

            total = wallet.balance_usd + asset_value
            pnl = total - START_CAPITAL_USD
            pnl_pct = float(pnl / START_CAPITAL_USD * 100)

            recent = CryptoOrder.objects.filter(user=user).select_related("asset", "analysis")[:5]

            results.append({
                "username": bot_def["username"],
                "display_name": bot_def["display_name"],
                "model": bot_def["model"],
                "strategy": bot_def["system_prompt"][:100] + "...",
                "total_value_usd": float(total),
                "cash_usd": float(wallet.balance_usd),
                "asset_value_usd": float(asset_value),
                "pnl_usd": float(pnl),
                "pnl_pct": round(pnl_pct, 2),
                "holdings": sorted(holdings, key=lambda x: -x["value_usd"]),
                "matched_orders": CryptoOrder.objects.filter(user=user, status="MATCHED").count(),
                "recent_orders": [
                    {
                        "id": o.id,
                        "symbol": o.asset.symbol,
                        "side": o.side,
                        "quantity": float(o.quantity),
                        "price": float(o.price_usd),
                        "total": float(o.total_usd),
                        "pnl_usd": float(o.pnl_usd) if o.pnl_usd is not None else None,
                        "pnl_pct": o.pnl_pct,
                        "has_analysis": bool(getattr(o, 'analysis', None)),
                        "created_at": o.created_at.strftime("%d/%m %H:%M"),
                    }
                    for o in recent
                ],
            })

        results.sort(key=lambda x: -x["pnl_pct"])
        return Response(results)


class FuturesBotLeaderboardView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        from crypto.bots.futures_definitions import FUTURES_BOTS
        from crypto.models import FuturesWallet, FuturesPosition
        from django.utils import timezone
        from datetime import timedelta

        START = Decimal("5000")
        results = []

        for bot_def in FUTURES_BOTS:
            try:
                user = User.objects.get(email=bot_def["email"])
                wallet = FuturesWallet.objects.get(user=user)
            except Exception:
                continue

            # ── Open positions + uPnL ────────────────────────────────────────
            open_positions = []
            total_upnl = Decimal("0")

            for pos in FuturesPosition.objects.filter(user=user, status="OPEN").select_related("asset"):
                try:
                    snap = pos.asset.snapshots.latest("timestamp")
                    cur = snap.price_usd
                except Exception:
                    cur = pos.entry_price

                upnl = pos.unrealized_pnl(cur)
                total_upnl += upnl
                liq = pos.liq_price()
                cur_f = float(cur)
                liq_dist_pct = abs(cur_f - liq) / cur_f * 100 if cur_f else 0
                open_positions.append({
                    "symbol": pos.asset.symbol,
                    "direction": pos.direction,
                    "entry_price": float(pos.entry_price),
                    "current_price": cur_f,
                    "margin_usd": float(pos.margin_usd),
                    "leverage": pos.leverage,
                    "unrealized_pnl": float(upnl),
                    "liq_price": liq,
                    "liq_dist_pct": round(liq_dist_pct, 1),
                })

            # ── Closed positions ─────────────────────────────────────────────
            closed_qs = list(
                FuturesPosition.objects.filter(user=user, status__in=["CLOSED", "LIQUIDATED"])
                .exclude(realized_pnl=None)
                .select_related("asset")
                .order_by("closed_at")
            )
            total_realized = sum(p.realized_pnl for p in closed_qs)

            # ── Stats ────────────────────────────────────────────────────────
            wins  = [p for p in closed_qs if p.realized_pnl > 0]
            losses = [p for p in closed_qs if p.realized_pnl <= 0]
            total_closed = len(closed_qs)
            win_rate   = round(len(wins) / total_closed * 100, 1) if total_closed else 0
            avg_win    = float(sum(p.realized_pnl for p in wins)   / len(wins))   if wins   else 0
            avg_loss   = float(sum(p.realized_pnl for p in losses) / len(losses)) if losses else 0
            profit_factor = round(abs(avg_win * len(wins)) / abs(avg_loss * len(losses)), 2) \
                            if losses and avg_loss != 0 else 0

            # Max drawdown from equity curve
            peak, running, max_dd = float(START), float(START), 0.0
            for p in closed_qs:
                running += float(p.realized_pnl)
                peak = max(peak, running)
                max_dd = max(max_dd, (peak - running) / peak * 100)

            # Trades opened in last 1h
            one_hour_ago = timezone.now() - timedelta(hours=1)
            trades_1h = FuturesPosition.objects.filter(user=user, opened_at__gte=one_hour_ago).count()

            # Total positions ever opened
            total_opened = FuturesPosition.objects.filter(user=user).count()

            # ── Equity curve (one point per closed trade) ────────────────────
            cum = Decimal("0")
            equity_curve = []
            for p in closed_qs:
                cum += p.realized_pnl
                equity_curve.append({
                    "t": p.closed_at.strftime("%d/%m %H:%M") if p.closed_at else "",
                    "v": float(START + cum),
                })

            # ── Summary — PnL = sum of all realized trades (simple, accurate) ──
            pnl = total_realized
            equity = START + pnl  # for equity_curve reference only

            recent = FuturesPosition.objects.filter(
                user=user, status__in=["CLOSED", "LIQUIDATED"]
            ).select_related("asset", "analysis").order_by("-closed_at")[:30]

            results.append({
                "username": bot_def["username"],
                "display_name": bot_def["display_name"],
                "model": bot_def["model"],
                "balance_usd": float(wallet.balance_usd),
                "used_margin_usd": float(wallet.used_margin_usd),
                "available_usd": float(wallet.available),
                "unrealized_pnl": float(total_upnl),
                "realized_pnl": float(total_realized),
                "equity_usd": float(equity),
                "pnl_usd": float(pnl),
                "pnl_pct": round(float(pnl / START * 100), 2),
                "open_count": len(open_positions),
                "open_positions": sorted(open_positions, key=lambda x: x["liq_dist_pct"]),
                "equity_curve": equity_curve[-120:],
                "stats": {
                    "total_trades": total_opened,
                    "closed_trades": total_closed,
                    "win_rate": win_rate,
                    "avg_win": round(avg_win, 2),
                    "avg_loss": round(avg_loss, 2),
                    "max_drawdown": round(max_dd, 1),
                    "profit_factor": profit_factor,
                    "trades_1h": trades_1h,
                },
                "recent_closed": [
                    {
                        "id":           p.id,
                        "symbol":       p.asset.symbol,
                        "direction":    p.direction,
                        "entry":        float(p.entry_price),
                        "exit":         float(p.exit_price or 0),
                        "pnl":          float(p.realized_pnl or 0),
                        "margin_usd":   float(p.margin_usd),
                        "leverage":     p.leverage,
                        "status":       p.status,
                        "opened_at":    _fmt_vn(p.opened_at),
                        "closed_at":    _fmt_vn(p.closed_at),
                        "has_analysis": hasattr(p, "analysis"),
                    }
                    for p in recent
                ],
            })

        results.sort(key=lambda x: -x["pnl_pct"])
        return Response(results)


class AnalyzeTradeView(APIView):
    """
    POST /crypto/bots/analyze-trade/<order_id>/
    Qwen 3.5 phân tích sâu 1 lệnh trade. Cache vào TradeAnalysis.
    Auto-extract LearnedLesson nếu |PnL| > 5%.
    """
    permission_classes = [AllowAny]

    def post(self, request, order_id: int):
        from crypto.models import CryptoOrder, TradeAnalysis
        from crypto.bots.analyzer import analyze_trade, should_extract_lesson, save_learned_lesson, _get_username_from_user

        try:
            order = CryptoOrder.objects.select_related("user", "asset").get(id=order_id)
        except CryptoOrder.DoesNotExist:
            return Response({"error": "Order not found"}, status=404)

        # Trả cache nếu đã analyze rồi
        try:
            cached = order.analysis
            return Response({
                "cached": True,
                "order_id": order_id,
                "analysis": cached.analysis_text,
                "quality_score": cached.quality_score,
            })
        except TradeAnalysis.DoesNotExist:
            pass

        # Gọi Qwen 3.5
        result = analyze_trade(order)
        if not result:
            return Response({"error": "Analyzer LLM không phản hồi. Kiểm tra Ollama."}, status=503)

        # Lưu cache
        TradeAnalysis.objects.create(
            order=order,
            analysis_text=result.get("why", ""),
            quality_score=result.get("quality_score", 0.5),
        )

        # Auto-extract lesson nếu đủ điều kiện
        lesson_saved = False
        bot_username = _get_username_from_user(order.user)
        if bot_username and should_extract_lesson(order, result):
            save_learned_lesson(order, bot_username, result)
            lesson_saved = True

        return Response({
            "cached": False,
            "order_id": order_id,
            "symbol": order.asset.symbol,
            "side": order.side,
            "why": result.get("why"),
            "verdict": result.get("verdict"),
            "quality_score": result.get("quality_score"),
            "lesson": result.get("lesson"),
            "lesson_tags": result.get("lesson_tags"),
            "lesson_polarity": result.get("lesson_polarity"),
            "lesson_saved": lesson_saved,
        })


class AnalyzeFuturesTradeView(APIView):
    """
    POST /crypto/futures/analyze-trade/<position_id>/
    Qwen phân tích 1 lệnh futures đã đóng.
    """
    permission_classes = [AllowAny]

    def post(self, request, position_id: int):
        from crypto.models import FuturesPosition, FuturesTradeAnalysis
        from bots.ollama_client import ask_llm

        try:
            pos = FuturesPosition.objects.select_related("user", "asset").get(
                id=position_id, status__in=["CLOSED", "LIQUIDATED"]
            )
        except FuturesPosition.DoesNotExist:
            return Response({"error": "Position not found"}, status=404)

        # Trả cache nếu đã phân tích rồi
        try:
            cached = pos.analysis
            import json as _json
            cached_data = _json.loads(cached.analysis_text)
            return Response({
                "cached": True,
                "position_id": position_id,
                "symbol": pos.asset.symbol,
                "direction": pos.direction,
                **cached_data,
                "lesson_saved": True,
            })
        except FuturesTradeAnalysis.DoesNotExist:
            pass

        pnl = float(pos.realized_pnl or 0)
        entry = float(pos.entry_price)
        exit_p = float(pos.exit_price or entry)
        notional = float(pos.margin_usd) * pos.leverage
        pnl_pct = (pnl / float(pos.margin_usd) * 100) if pos.margin_usd else 0
        verdict = "WIN" if pnl > 0 else ("LOSS" if pnl < 0 else "BREAKEVEN")
        if pos.status == "LIQUIDATED":
            verdict = "LIQUIDATED"

        system_prompt = "Bạn là chuyên gia phân tích giao dịch futures crypto. Hãy phân tích lệnh trade và đưa ra nhận xét thực tế, ngắn gọn bằng tiếng Việt."
        user_message = f"""Phân tích lệnh futures sau:
- Bot: {pos.user.username}
- Mã: {pos.asset.symbol} | Hướng: {pos.direction}
- Entry: ${entry:.4f} → Exit: ${exit_p:.4f}
- Margin: ${float(pos.margin_usd):.0f} × {pos.leverage}x | Notional: ${notional:.0f}
- PnL thực: ${pnl:+.2f} ({pnl_pct:+.1f}% trên margin)
- Trạng thái: {pos.status}
- Mở: {pos.opened_at} | Đóng: {pos.closed_at}

Trả về JSON:
{{
  "why": "Phân tích 2-3 câu: entry đúng xu hướng không, leverage phù hợp không, exit đúng lúc không",
  "verdict": "{verdict}",
  "quality_score": 0.0,
  "lesson": "bài học rút ra hoặc null",
  "lesson_tags": ["tag"],
  "lesson_polarity": "positive hoặc negative"
}}"""

        data = ask_llm("phi4:14b", system_prompt, user_message, num_ctx=2048, num_predict=400)
        if not data:
            return Response({"error": "LLM không phản hồi. Kiểm tra Ollama."}, status=503)

        # Lưu lesson nếu đủ điều kiện (|PnL| > 5% và có lesson text)
        lesson_saved = False
        lesson_text = data.get("lesson")
        quality = float(data.get("quality_score") or 0.5)
        if lesson_text and abs(pnl_pct) > 5.0 and quality >= 0.55:
            try:
                from crypto.models import LearnedLesson
                tags = data.get("lesson_tags", ["universal"])
                tags_str = ",".join(str(t).strip() for t in tags) if isinstance(tags, list) else str(tags)
                polarity = data.get("lesson_polarity", "")
                if polarity not in ("GOOD", "WARNING"):
                    polarity = "WARNING" if pnl < 0 else "GOOD"
                LearnedLesson.objects.create(
                    source_order=None,
                    source_bot=pos.user.username,
                    lesson_text=lesson_text,
                    polarity=polarity,
                    tags=tags_str,
                    quality_score=quality,
                    pnl_at_extraction=pnl_pct,
                )
                lesson_saved = True
            except Exception as e:
                logger.warning(f"Could not save futures lesson: {e}")

        # Lưu cache kết quả phân tích
        result_payload = {
            "why": data.get("why", ""),
            "verdict": data.get("verdict", verdict),
            "quality_score": quality,
            "lesson": lesson_text,
            "lesson_tags": data.get("lesson_tags", []),
            "lesson_polarity": data.get("lesson_polarity", ""),
        }
        try:
            import json as _json
            FuturesTradeAnalysis.objects.create(
                position=pos,
                analysis_text=_json.dumps(result_payload, ensure_ascii=False),
                quality_score=quality,
            )
        except Exception as e:
            logger.warning(f"Could not cache futures analysis: {e}")

        return Response({
            "cached": False,
            "position_id": position_id,
            "symbol": pos.asset.symbol,
            "direction": pos.direction,
            **result_payload,
            "lesson_saved": lesson_saved,
        })


class FuturesCloseAllView(APIView):
    """Emergency: close ALL open futures positions across all bots. Call before shutdown."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from crypto.models import FuturesPosition, FuturesWallet
        from crypto.bots.futures_executor import _close_position

        logs = []
        positions = (
            FuturesPosition.objects
            .filter(status="OPEN")
            .select_related("asset", "user")
        )

        for pos in positions:
            try:
                cur_price = pos.asset.snapshots.latest("timestamp").price_usd
                wallet = FuturesWallet.objects.get(user=pos.user)
                wallet.refresh_from_db()
                log = _close_position(pos, cur_price, wallet, "EMERGENCY CLOSE")
                logs.append({"ok": True,  "msg": log.strip()})
            except Exception as e:
                logs.append({"ok": False, "msg": f"ERROR {pos.asset.symbol}: {e}"})

        return Response({
            "closed": sum(1 for l in logs if l["ok"]),
            "errors": sum(1 for l in logs if not l["ok"]),
            "logs":   logs,
        })

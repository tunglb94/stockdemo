from decimal import Decimal, InvalidOperation
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import get_user_model

User = get_user_model()
START_CAPITAL_USD = Decimal("5000")


class CryptoMarketView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        from crypto.models import CryptoAsset

        result = []
        for asset in CryptoAsset.objects.filter(is_active=True).order_by("rank"):
            try:
                snap = asset.snapshots.latest("timestamp")
                result.append({
                    "symbol": asset.symbol,
                    "name": asset.name,
                    "category": asset.category,
                    "rank": asset.rank,
                    "price": float(snap.price_usd),
                    "change_24h": round(snap.change_24h, 4),
                    "volume_24h": float(snap.volume_24h),
                    "market_cap": float(snap.market_cap),
                    "updated_at": snap.timestamp.strftime("%H:%M:%S"),
                })
            except Exception:
                result.append({
                    "symbol": asset.symbol,
                    "name": asset.name,
                    "category": asset.category,
                    "rank": asset.rank,
                    "price": 0,
                    "change_24h": 0,
                    "volume_24h": 0,
                    "market_cap": 0,
                    "updated_at": None,
                })
        return Response(result)


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

            recent = CryptoOrder.objects.filter(user=user).select_related("asset")[:5]

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
                        "symbol": o.asset.symbol,
                        "side": o.side,
                        "quantity": float(o.quantity),
                        "price": float(o.price_usd),
                        "total": float(o.total_usd),
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

        START = Decimal("5000")
        results = []

        for bot_def in FUTURES_BOTS:
            try:
                user = User.objects.get(email=bot_def["email"])
                wallet = FuturesWallet.objects.get(user=user)
            except Exception:
                continue

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
                open_positions.append({
                    "symbol": pos.asset.symbol,
                    "direction": pos.direction,
                    "entry_price": float(pos.entry_price),
                    "current_price": float(cur),
                    "margin_usd": float(pos.margin_usd),
                    "leverage": pos.leverage,
                    "unrealized_pnl": float(upnl),
                    "liq_price": pos.liq_price(),
                })

            realized_pnl = FuturesPosition.objects.filter(
                user=user, status__in=["CLOSED", "LIQUIDATED"]
            ).exclude(realized_pnl=None)
            total_realized = sum(p.realized_pnl for p in realized_pnl)

            equity = wallet.balance_usd + total_upnl
            pnl = equity - START
            pnl_pct = float(pnl / START * 100)

            recent = FuturesPosition.objects.filter(
                user=user, status__in=["CLOSED", "LIQUIDATED"]
            ).select_related("asset").order_by("-closed_at")[:20]

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
                "pnl_pct": round(pnl_pct, 2),
                "open_positions": sorted(open_positions, key=lambda x: -abs(x["unrealized_pnl"])),
                "open_count": len(open_positions),
                "recent_closed": [
                    {
                        "symbol": p.asset.symbol,
                        "direction": p.direction,
                        "entry": float(p.entry_price),
                        "exit": float(p.exit_price or 0),
                        "pnl": float(p.realized_pnl or 0),
                        "status": p.status,
                        "closed_at": p.closed_at.strftime("%d/%m %H:%M") if p.closed_at else "",
                    }
                    for p in recent
                ],
            })

        results.sort(key=lambda x: -x["pnl_pct"])
        return Response(results)

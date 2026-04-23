"use client";
import { useState, useEffect, useCallback } from "react";
import apiClient from "@/services/apiClient";

interface Asset {
  symbol: string; name: string; category: string; rank: number;
  price: number; change_24h: number; volume_24h: number; market_cap: number; updated_at: string | null;
}
interface CryptoBot {
  username: string; display_name: string; model: string;
  total_value_usd: number; cash_usd: number; asset_value_usd: number;
  pnl_usd: number; pnl_pct: number; matched_orders: number;
  holdings: { symbol: string; quantity: number; avg_cost: number; current_price: number; value_usd: number; pnl_pct: number }[];
  recent_orders: { symbol: string; side: string; quantity: number; price: number; total: number; created_at: string }[];
}
interface FuturesBot {
  username: string; display_name: string; model: string;
  balance_usd: number; used_margin_usd: number; available_usd: number;
  unrealized_pnl: number; realized_pnl: number; equity_usd: number;
  pnl_usd: number; pnl_pct: number; open_count: number;
  open_positions: { symbol: string; direction: string; entry_price: number; current_price: number; margin_usd: number; leverage: number; unrealized_pnl: number; liq_price: number }[];
  recent_closed: { symbol: string; direction: string; entry: number; exit: number; pnl: number; status: string; closed_at: string }[];
}

const MEDALS = ["🥇", "🥈", "🥉", "4.", "5.", "6.", "7.", "8.", "9.", "10."];
const fmtPrice = (p: number) => p >= 1000 ? p.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : p >= 1 ? p.toFixed(4) : p >= 0.001 ? p.toFixed(6) : p.toFixed(8);
const fmtQty = (q: number) => q >= 1 ? q.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 4 }) : q.toFixed(6);
const fmtMcap = (n: number) => n >= 1e12 ? `$${(n/1e12).toFixed(2)}T` : n >= 1e9 ? `$${(n/1e9).toFixed(2)}B` : n >= 1e6 ? `$${(n/1e6).toFixed(1)}M` : `$${n.toFixed(0)}`;
const fmtUsd = (n: number) => n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

export default function CryptoPage() {
  const [tab, setTab] = useState<"market" | "bots" | "futures">("market");
  const [assets, setAssets] = useState<Asset[]>([]);
  const [bots, setBots] = useState<CryptoBot[]>([]);
  const [futuresBots, setFuturesBots] = useState<FuturesBot[]>([]);
  const [detail, setDetail] = useState<CryptoBot | null>(null);
  const [fDetail, setFDetail] = useState<FuturesBot | null>(null);
  const [filter, setFilter] = useState<"ALL" | "CRYPTO" | "COMMODITY">("ALL");
  const [sortBy, setSortBy] = useState<"rank" | "change_up" | "change_down" | "mcap">("rank");
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState("");

  const loadMarket = useCallback(async () => {
    try {
      const r = await apiClient.get("/crypto/market/");
      setAssets(r.data);
      setLastUpdate(new Date().toLocaleTimeString("vi-VN"));
    } catch {}
    setLoading(false);
  }, []);

  const loadBots = useCallback(async () => {
    try {
      const r = await apiClient.get("/crypto/bots/");
      const data: CryptoBot[] = r.data;
      setBots(data);
      if (data.length > 0) setDetail(p => !p ? data[0] : (data.find(b => b.username === p.username) ?? data[0]));
    } catch {}
  }, []);

  const loadFutures = useCallback(async () => {
    try {
      const r = await apiClient.get("/crypto/futures/bots/");
      const data: FuturesBot[] = r.data;
      setFuturesBots(data);
      if (data.length > 0) setFDetail(p => !p ? data[0] : (data.find(b => b.username === p.username) ?? data[0]));
    } catch {}
  }, []);

  useEffect(() => {
    loadMarket(); loadBots(); loadFutures();
    const id = setInterval(() => { loadMarket(); loadBots(); loadFutures(); }, 15000);
    return () => clearInterval(id);
  }, [loadMarket, loadBots, loadFutures]);

  const displayed = assets
    .filter(a => filter === "ALL" || a.category === filter)
    .sort((a, b) => sortBy === "change_up" ? b.change_24h - a.change_24h : sortBy === "change_down" ? a.change_24h - b.change_24h : sortBy === "mcap" ? b.market_cap - a.market_cap : a.rank - b.rank);

  const btc = assets.find(a => a.symbol === "BTC");
  const eth = assets.find(a => a.symbol === "ETH");
  const xau = assets.find(a => a.symbol === "XAU");
  const wti = assets.find(a => a.symbol === "WTI");

  return (
    <div className="h-full flex flex-col bg-dark-bg text-white overflow-hidden">
      {/* Header */}
      <div className="px-4 py-2 border-b border-dark-border bg-dark-surface flex items-center justify-between flex-shrink-0">
        <div className="flex items-center gap-6">
          <div>
            <div className="font-bold text-lg flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse inline-block" />
              CryptoSim Exchange
            </div>
            <div className="text-[11px] text-gray-500">24/7 · Top 30 Crypto + Vàng + Dầu · Spot & Futures</div>
          </div>
          <div className="flex gap-5 text-xs">
            {[btc, eth, xau, wti].filter(Boolean).map(a => a && (
              <div key={a.symbol}>
                <span className="text-gray-400">{a.symbol} </span>
                <span className="font-mono font-semibold">${fmtPrice(a.price)}</span>
                <span className={`ml-1 font-semibold ${a.change_24h >= 0 ? "text-price-up" : "text-price-down"}`}>
                  {a.change_24h >= 0 ? "+" : ""}{a.change_24h.toFixed(2)}%
                </span>
              </div>
            ))}
          </div>
        </div>
        <div className="text-[11px] text-gray-500">Cập nhật: {lastUpdate || "..."}</div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 px-4 pt-2 border-b border-dark-border flex-shrink-0">
        {([["market", "📈 Bảng giá"], ["bots", "🤖 Spot Bots"], ["futures", "⚡ Long/Short Bots"]] as const).map(([t, l]) => (
          <button key={t} onClick={() => setTab(t)}
            className={`px-5 py-1.5 text-sm rounded-t-md transition ${tab === t ? "bg-dark-surface text-white border border-b-dark-surface border-dark-border border-b-0" : "text-gray-500 hover:text-white"}`}>
            {l}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-hidden">

        {/* ── MARKET TAB ── */}
        {tab === "market" && (
          <div className="h-full flex flex-col">
            <div className="px-4 py-2 flex items-center gap-3 text-xs border-b border-dark-border flex-shrink-0">
              <span className="text-gray-500">Lọc:</span>
              {(["ALL", "CRYPTO", "COMMODITY"] as const).map(f => (
                <button key={f} onClick={() => setFilter(f)} className={`px-2.5 py-0.5 rounded text-xs ${filter === f ? "bg-blue-600 text-white" : "text-gray-400 hover:text-white"}`}>
                  {f === "ALL" ? "Tất cả (32)" : f === "CRYPTO" ? "Crypto (30)" : "Vàng & Dầu"}
                </button>
              ))}
              <span className="text-gray-500 ml-3">Sắp xếp:</span>
              {([["rank", "Xếp hạng"], ["change_up", "Tăng nhất"], ["change_down", "Giảm nhất"], ["mcap", "Vốn hóa"]] as const).map(([s, l]) => (
                <button key={s} onClick={() => setSortBy(s)} className={`px-2.5 py-0.5 rounded text-xs ${sortBy === s ? "bg-blue-600 text-white" : "text-gray-400 hover:text-white"}`}>{l}</button>
              ))}
            </div>
            <div className="flex-1 overflow-auto">
              <table className="w-full text-sm">
                <thead className="sticky top-0 bg-dark-surface text-gray-400 text-xs z-10">
                  <tr>
                    <th className="text-left px-4 py-2 w-10">#</th>
                    <th className="text-left px-4 py-2">Tài sản</th>
                    <th className="text-right px-4 py-2">Giá (USD)</th>
                    <th className="text-right px-4 py-2">24h %</th>
                    <th className="text-right px-4 py-2">Khối lượng 24h</th>
                    <th className="text-right px-4 py-2">Vốn hóa</th>
                    <th className="text-right px-4 py-2">Cập nhật</th>
                  </tr>
                </thead>
                <tbody>
                  {loading && <tr><td colSpan={7} className="text-center py-12 text-gray-500">Đang tải...</td></tr>}
                  {!loading && displayed.length === 0 && <tr><td colSpan={7} className="text-center py-12 text-gray-500">Chưa có dữ liệu (CoinGecko cập nhật mỗi 60s)</td></tr>}
                  {displayed.map(a => (
                    <tr key={a.symbol} className="border-t border-dark-border hover:bg-dark-surface/40 transition">
                      <td className="px-4 py-2.5 text-gray-500 text-xs">{a.rank}</td>
                      <td className="px-4 py-2.5">
                        <div className="flex items-center gap-2">
                          <span className={`text-[10px] px-1.5 py-0.5 rounded font-bold ${a.category === "COMMODITY" ? "bg-yellow-900/60 text-yellow-400" : "bg-blue-900/60 text-blue-300"}`}>
                            {a.category === "COMMODITY" ? "CMD" : "CRYPTO"}
                          </span>
                          <span className="font-bold">{a.symbol}</span>
                          <span className="text-gray-400 text-xs">{a.name}</span>
                        </div>
                      </td>
                      <td className="px-4 py-2.5 text-right font-mono font-semibold">{a.price === 0 ? <span className="text-gray-600">—</span> : `$${fmtPrice(a.price)}`}</td>
                      <td className={`px-4 py-2.5 text-right font-bold ${a.change_24h > 0 ? "text-price-up" : a.change_24h < 0 ? "text-price-down" : "text-gray-500"}`}>
                        {a.change_24h === 0 ? "—" : `${a.change_24h > 0 ? "▲" : "▼"} ${Math.abs(a.change_24h).toFixed(2)}%`}
                      </td>
                      <td className="px-4 py-2.5 text-right text-gray-400 text-xs">{a.volume_24h > 0 ? fmtMcap(a.volume_24h) : "—"}</td>
                      <td className="px-4 py-2.5 text-right text-gray-400 text-xs">{a.market_cap > 0 ? fmtMcap(a.market_cap) : "—"}</td>
                      <td className="px-4 py-2.5 text-right text-gray-500 text-xs">{a.updated_at || "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* ── SPOT BOTS TAB ── */}
        {tab === "bots" && (
          <div className="h-full flex overflow-hidden">
            <div className="w-64 border-r border-dark-border overflow-y-auto flex-shrink-0 bg-dark-surface">
              <div className="p-3 border-b border-dark-border">
                <div className="text-xs font-semibold text-gray-300">SPOT BOT LEADERBOARD</div>
                <div className="text-[10px] text-gray-600 mt-0.5">Mua/Bán · $5,000 USD · 24/7</div>
              </div>
              {bots.length === 0 ? (
                <div className="p-4 text-xs text-gray-500">Chưa có bot. Chạy: <code className="bg-dark-bg px-1 rounded">create_crypto_bots</code></div>
              ) : bots.map((bot, i) => {
                const up = bot.pnl_pct >= 0;
                return (
                  <div key={bot.username} onClick={() => setDetail(bot)}
                    className={`p-3 cursor-pointer border-b border-dark-border transition ${detail?.username === bot.username ? "bg-dark-bg" : "hover:bg-dark-bg/50"}`}>
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-2">
                        <span className="text-base">{MEDALS[i] ?? `${i + 1}.`}</span>
                        <div>
                          <div className="text-sm font-semibold leading-tight">{bot.display_name}</div>
                          <div className="text-[10px] text-gray-500">{bot.model}</div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className={`text-sm font-bold ${up ? "text-price-up" : "text-price-down"}`}>{up ? "+" : ""}{bot.pnl_pct.toFixed(2)}%</div>
                        <div className={`text-[11px] font-semibold ${up ? "text-price-up" : "text-price-down"}`}>{up ? "+" : "-"}${fmtUsd(Math.abs(bot.pnl_usd))}</div>
                      </div>
                    </div>
                    <div className="mt-2 h-1 bg-dark-border rounded-full overflow-hidden">
                      <div className={`h-full rounded-full ${up ? "bg-price-up" : "bg-price-down"}`} style={{ width: `${Math.min(100, Math.abs(bot.pnl_pct) * 5)}%` }} />
                    </div>
                  </div>
                );
              })}
            </div>
            {detail ? (
              <div className="flex-1 overflow-y-auto p-5">
                <div className="flex items-start justify-between mb-5">
                  <div>
                    <h2 className="text-2xl font-bold">{detail.display_name}</h2>
                    <span className="text-xs bg-dark-surface border border-dark-border px-2 py-0.5 rounded text-gray-400">{detail.model}</span>
                  </div>
                  <div className="text-right">
                    <div className={`text-3xl font-bold ${detail.pnl_pct >= 0 ? "text-price-up" : "text-price-down"}`}>{detail.pnl_pct >= 0 ? "+" : ""}{detail.pnl_pct.toFixed(2)}%</div>
                    <div className={`text-base font-semibold ${detail.pnl_usd >= 0 ? "text-price-up" : "text-price-down"}`}>{detail.pnl_usd >= 0 ? "Lời " : "Lỗ "}${fmtUsd(Math.abs(detail.pnl_usd))}</div>
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-3 mb-5">
                  {[
                    { label: "Tổng tài sản", value: `$${fmtUsd(detail.total_value_usd)}`, sub: "USD" },
                    { label: "Tiền mặt", value: `$${fmtUsd(detail.cash_usd)}`, sub: `${detail.total_value_usd > 0 ? ((detail.cash_usd / detail.total_value_usd) * 100).toFixed(0) : 0}% danh mục` },
                    { label: "Crypto", value: `$${fmtUsd(detail.asset_value_usd)}`, sub: `${detail.holdings.length} mã` },
                    { label: detail.pnl_usd >= 0 ? "💰 Lời" : "📉 Lỗ", value: `${detail.pnl_usd >= 0 ? "+" : "-"}$${fmtUsd(Math.abs(detail.pnl_usd))}`, sub: "so với vốn $5,000", color: detail.pnl_usd >= 0 ? "text-price-up" : "text-price-down" },
                    { label: "Lệnh khớp", value: detail.matched_orders.toString(), sub: "tổng cộng" },
                    { label: "Vốn ban đầu", value: "$5,000", sub: "USD" },
                  ].map((s, i) => (
                    <div key={i} className="bg-dark-surface rounded-xl p-3 border border-dark-border">
                      <div className="text-xs text-gray-400">{s.label}</div>
                      <div className={`text-xl font-bold mt-1 ${s.color ?? "text-white"}`}>{s.value}</div>
                      <div className="text-xs text-gray-500 mt-0.5">{s.sub}</div>
                    </div>
                  ))}
                </div>
                {detail.holdings.length > 0 && (
                  <div className="mb-5">
                    <div className="text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">Danh mục</div>
                    <table className="w-full text-sm">
                      <thead className="text-xs text-gray-500"><tr><th className="text-left pb-1.5">Mã</th><th className="text-right pb-1.5">Số lượng</th><th className="text-right pb-1.5">Giá vốn</th><th className="text-right pb-1.5">Giá hiện tại</th><th className="text-right pb-1.5">Giá trị</th><th className="text-right pb-1.5">P&L%</th></tr></thead>
                      <tbody>{detail.holdings.map(h => (
                        <tr key={h.symbol} className="border-t border-dark-border">
                          <td className="py-1.5 font-bold">{h.symbol}</td>
                          <td className="py-1.5 text-right font-mono text-xs">{fmtQty(h.quantity)}</td>
                          <td className="py-1.5 text-right text-xs">${fmtPrice(h.avg_cost)}</td>
                          <td className="py-1.5 text-right text-xs">${fmtPrice(h.current_price)}</td>
                          <td className="py-1.5 text-right text-xs font-semibold">${fmtUsd(h.value_usd)}</td>
                          <td className={`py-1.5 text-right font-bold text-xs ${h.pnl_pct >= 0 ? "text-price-up" : "text-price-down"}`}>{h.pnl_pct >= 0 ? "+" : ""}{h.pnl_pct.toFixed(2)}%</td>
                        </tr>
                      ))}</tbody>
                    </table>
                  </div>
                )}
                {detail.recent_orders.length > 0 && (
                  <div>
                    <div className="text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">Lệnh gần đây</div>
                    <div className="space-y-1.5">{detail.recent_orders.map((o, i) => (
                      <div key={i} className="flex items-center gap-2 text-xs bg-dark-surface rounded-lg px-3 py-2 border border-dark-border">
                        <span className={`font-bold px-2 py-0.5 rounded text-[10px] ${o.side === "BUY" ? "bg-price-up/20 text-price-up" : "bg-price-down/20 text-price-down"}`}>{o.side}</span>
                        <span className="font-bold">{o.symbol}</span>
                        <span className="text-gray-400">{fmtQty(o.quantity)} @ ${fmtPrice(o.price)}</span>
                        <span className="text-gray-500 font-semibold">= ${fmtUsd(o.total)}</span>
                        <span className="ml-auto text-gray-600">{o.created_at}</span>
                      </div>
                    ))}</div>
                  </div>
                )}
              </div>
            ) : <div className="flex-1 flex items-center justify-center text-gray-500 text-sm">Chọn một bot</div>}
          </div>
        )}

        {/* ── FUTURES BOTS TAB ── */}
        {tab === "futures" && (
          <div className="h-full flex overflow-hidden">
            <div className="w-64 border-r border-dark-border overflow-y-auto flex-shrink-0 bg-dark-surface">
              <div className="p-3 border-b border-dark-border">
                <div className="text-xs font-semibold text-gray-300">⚡ LONG/SHORT LEADERBOARD</div>
                <div className="text-[10px] text-gray-600 mt-0.5">Futures · $5,000 USD · Leverage 1-5x</div>
              </div>
              {futuresBots.length === 0 ? (
                <div className="p-4 text-xs text-gray-500">Chưa có bot. Chạy: <code className="bg-dark-bg px-1 rounded">create_futures_bots</code></div>
              ) : futuresBots.map((bot, i) => {
                const up = bot.pnl_pct >= 0;
                return (
                  <div key={bot.username} onClick={() => setFDetail(bot)}
                    className={`p-3 cursor-pointer border-b border-dark-border transition ${fDetail?.username === bot.username ? "bg-dark-bg" : "hover:bg-dark-bg/50"}`}>
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-2">
                        <span className="text-base">{MEDALS[i] ?? `${i + 1}.`}</span>
                        <div>
                          <div className="text-sm font-semibold leading-tight">{bot.display_name}</div>
                          <div className="text-[10px] text-gray-500">{bot.model}</div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className={`text-sm font-bold ${up ? "text-price-up" : "text-price-down"}`}>{up ? "+" : ""}{bot.pnl_pct.toFixed(2)}%</div>
                        <div className={`text-[11px] font-semibold ${up ? "text-price-up" : "text-price-down"}`}>{up ? "+" : "-"}${fmtUsd(Math.abs(bot.pnl_usd))}</div>
                        {bot.open_count > 0 && <div className="text-[10px] text-yellow-400">{bot.open_count} vị trí mở</div>}
                      </div>
                    </div>
                    <div className="mt-2 h-1 bg-dark-border rounded-full overflow-hidden">
                      <div className={`h-full rounded-full ${up ? "bg-price-up" : "bg-price-down"}`} style={{ width: `${Math.min(100, Math.abs(bot.pnl_pct) * 5)}%` }} />
                    </div>
                  </div>
                );
              })}
            </div>

            {fDetail ? (
              <div className="flex-1 overflow-y-auto p-5">
                <div className="flex items-start justify-between mb-5">
                  <div>
                    <h2 className="text-2xl font-bold">{fDetail.display_name}</h2>
                    <span className="text-xs bg-dark-surface border border-dark-border px-2 py-0.5 rounded text-gray-400">{fDetail.model}</span>
                    <span className="ml-2 text-xs bg-yellow-900/40 border border-yellow-700/40 text-yellow-400 px-2 py-0.5 rounded">Futures · Long/Short</span>
                  </div>
                  <div className="text-right">
                    <div className={`text-3xl font-bold ${fDetail.pnl_pct >= 0 ? "text-price-up" : "text-price-down"}`}>{fDetail.pnl_pct >= 0 ? "+" : ""}{fDetail.pnl_pct.toFixed(2)}%</div>
                    <div className={`text-base font-semibold ${fDetail.pnl_usd >= 0 ? "text-price-up" : "text-price-down"}`}>{fDetail.pnl_usd >= 0 ? "Lời " : "Lỗ "}${fmtUsd(Math.abs(fDetail.pnl_usd))}</div>
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-3 mb-5">
                  {[
                    { label: "Equity (vốn thực)", value: `$${fmtUsd(fDetail.equity_usd)}`, sub: "balance + uPnL" },
                    { label: "Balance USD", value: `$${fmtUsd(fDetail.balance_usd)}`, sub: `Margin đang dùng: $${fmtUsd(fDetail.used_margin_usd)}` },
                    { label: "Khả dụng", value: `$${fmtUsd(fDetail.available_usd)}`, sub: `${fDetail.open_count} vị trí mở` },
                    { label: fDetail.pnl_usd >= 0 ? "💰 Tổng lời" : "📉 Tổng lỗ", value: `${fDetail.pnl_usd >= 0 ? "+" : "-"}$${fmtUsd(Math.abs(fDetail.pnl_usd))}`, sub: `= Equity $${fmtUsd(fDetail.equity_usd)} − vốn $5,000`, color: fDetail.pnl_usd >= 0 ? "text-price-up" : "text-price-down" },
                    { label: "uPnL (vị trí đang mở)", value: `${fDetail.unrealized_pnl >= 0 ? "+" : ""}$${fmtUsd(fDetail.unrealized_pnl)}`, sub: "lãi/lỗ chưa chốt", color: fDetail.unrealized_pnl >= 0 ? "text-price-up" : "text-price-down" },
                    { label: "Realized PnL (đã chốt)", value: `${fDetail.realized_pnl >= 0 ? "+" : ""}$${fmtUsd(fDetail.realized_pnl)}`, sub: "tổng lãi/lỗ từ các phiên đã đóng", color: fDetail.realized_pnl >= 0 ? "text-price-up" : "text-price-down" },
                  ].map((s, i) => (
                    <div key={i} className="bg-dark-surface rounded-xl p-3 border border-dark-border">
                      <div className="text-xs text-gray-400">{s.label}</div>
                      <div className={`text-xl font-bold mt-1 ${s.color ?? "text-white"}`}>{s.value}</div>
                      <div className="text-xs text-gray-500 mt-0.5">{s.sub}</div>
                    </div>
                  ))}
                </div>

                {fDetail.open_positions.length > 0 && (
                  <div className="mb-5">
                    <div className="text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">Vị trí đang mở</div>
                    <table className="w-full text-sm">
                      <thead className="text-xs text-gray-500">
                        <tr><th className="text-left pb-1.5">Hướng</th><th className="text-left pb-1.5">Mã</th><th className="text-right pb-1.5">Entry</th><th className="text-right pb-1.5">Giá hiện tại</th><th className="text-right pb-1.5">Margin×Lev</th><th className="text-right pb-1.5">uPnL</th><th className="text-right pb-1.5">Liq Price</th></tr>
                      </thead>
                      <tbody>
                        {fDetail.open_positions.map((p, i) => (
                          <tr key={i} className="border-t border-dark-border">
                            <td className="py-1.5">
                              <span className={`font-bold px-2 py-0.5 rounded text-[11px] ${p.direction === "LONG" ? "bg-price-up/20 text-price-up" : "bg-price-down/20 text-price-down"}`}>{p.direction}</span>
                            </td>
                            <td className="py-1.5 font-bold">{p.symbol}</td>
                            <td className="py-1.5 text-right text-xs">${fmtPrice(p.entry_price)}</td>
                            <td className="py-1.5 text-right text-xs">${fmtPrice(p.current_price)}</td>
                            <td className="py-1.5 text-right text-xs">${fmtUsd(p.margin_usd)} ×{p.leverage}</td>
                            <td className={`py-1.5 text-right font-bold text-xs ${p.unrealized_pnl >= 0 ? "text-price-up" : "text-price-down"}`}>{p.unrealized_pnl >= 0 ? "+" : ""}${fmtUsd(p.unrealized_pnl)}</td>
                            <td className="py-1.5 text-right text-xs text-red-400">${fmtPrice(p.liq_price)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}

                {fDetail.recent_closed.length > 0 && (
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
                        Lịch sử giao dịch ({fDetail.recent_closed.length} gần nhất)
                      </div>
                      <div className="text-xs text-gray-500">
                        Tổng realized: <span className={`font-bold ${fDetail.realized_pnl >= 0 ? "text-price-up" : "text-price-down"}`}>
                          {fDetail.realized_pnl >= 0 ? "+" : ""}${fmtUsd(fDetail.realized_pnl)}
                        </span>
                      </div>
                    </div>
                    <div className="space-y-1.5">
                      {(() => {
                        // Tính cumulative từ cũ → mới (list đang sort mới → cũ)
                        const reversed = [...fDetail.recent_closed].reverse();
                        let cum = 0;
                        const cumList = reversed.map(p => { cum += p.pnl; return cum; });
                        return fDetail.recent_closed.map((p, i) => {
                          const cumPnl = cumList[fDetail.recent_closed.length - 1 - i];
                          return (
                            <div key={i} className="flex items-center gap-2 text-xs bg-dark-surface rounded-lg px-3 py-2 border border-dark-border">
                              <span className={`font-bold px-2 py-0.5 rounded text-[10px] ${p.direction === "LONG" ? "bg-price-up/20 text-price-up" : "bg-price-down/20 text-price-down"}`}>{p.direction}</span>
                              <span className="font-bold w-10">{p.symbol}</span>
                              <span className="text-gray-400">${fmtPrice(p.entry)} → ${fmtPrice(p.exit)}</span>
                              {/* P&L của phiên này */}
                              <span className={`font-bold min-w-[70px] text-right ${p.pnl >= 0 ? "text-price-up" : "text-price-down"}`}>
                                {p.pnl >= 0 ? "+" : ""}${fmtUsd(p.pnl)}
                              </span>
                              {/* Cumulative */}
                              <span className="text-gray-600 text-[10px]">
                                tổng: <span className={cumPnl >= 0 ? "text-green-600" : "text-red-600"}>{cumPnl >= 0 ? "+" : ""}${fmtUsd(cumPnl)}</span>
                              </span>
                              {p.status === "LIQUIDATED" && <span className="text-red-400 font-bold text-[10px] ml-1">LIQ</span>}
                              <span className="ml-auto text-gray-600">{p.closed_at}</span>
                            </div>
                          );
                        });
                      })()}
                    </div>
                  </div>
                )}
              </div>
            ) : <div className="flex-1 flex items-center justify-center text-gray-500 text-sm">Chọn một bot để xem chi tiết</div>}
          </div>
        )}
      </div>
    </div>
  );
}

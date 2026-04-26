"use client";
import { useState, useEffect, useCallback, useRef } from "react";
import apiClient from "@/services/apiClient";
import CryptoAssetRow from "@/components/market/CryptoAssetRow";
import type { Asset } from "@/components/market/CryptoAssetRow";

interface BotOrder {
  id: number;
  symbol: string; side: string; quantity: number; price: number;
  total: number; created_at: string;
  pnl_usd: number | null; pnl_pct: number | null;
  has_analysis: boolean;
}
interface CryptoBot {
  username: string; display_name: string; model: string;
  total_value_usd: number; cash_usd: number; asset_value_usd: number;
  pnl_usd: number; pnl_pct: number; matched_orders: number;
  holdings: { symbol: string; quantity: number; avg_cost: number; current_price: number; value_usd: number; pnl_pct: number }[];
  recent_orders: BotOrder[];
}
interface TradeAnalysisResult {
  cached: boolean;
  order_id: number;
  symbol: string; side: string;
  why: string; verdict: string; quality_score: number;
  lesson: string | null; lesson_tags: string[]; lesson_polarity: string;
  lesson_saved: boolean;
}
interface FuturesStats {
  total_trades: number; closed_trades: number; win_rate: number;
  avg_win: number; avg_loss: number; max_drawdown: number;
  profit_factor: number; trades_1h: number;
}
interface OpenPosition {
  symbol: string; direction: string; entry_price: number; current_price: number;
  margin_usd: number; leverage: number; unrealized_pnl: number;
  liq_price: number; liq_dist_pct: number;
}
interface FuturesBot {
  username: string; display_name: string; model: string;
  balance_usd: number; used_margin_usd: number; available_usd: number;
  unrealized_pnl: number; realized_pnl: number; equity_usd: number;
  pnl_usd: number; pnl_pct: number; open_count: number;
  open_positions: OpenPosition[];
  equity_curve: { t: string; v: number }[];
  stats: FuturesStats;
  recent_closed: { id: number; symbol: string; direction: string; entry: number; exit: number; pnl: number; margin_usd: number; leverage: number; status: string; opened_at: string; closed_at: string; has_analysis: boolean }[];
}

const MEDALS = ["🥇", "🥈", "🥉", "4.", "5.", "6.", "7.", "8.", "9.", "10."];
const fmtPrice = (p: number) => p >= 1000 ? p.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : p >= 1 ? p.toFixed(4) : p >= 0.001 ? p.toFixed(6) : p.toFixed(8);
const fmtQty = (q: number) => q >= 1 ? q.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 4 }) : q.toFixed(6);
const fmtMcap = (n: number) => n >= 1e12 ? `$${(n/1e12).toFixed(2)}T` : n >= 1e9 ? `$${(n/1e9).toFixed(2)}B` : n >= 1e6 ? `$${(n/1e6).toFixed(1)}M` : `$${n.toFixed(0)}`;
const fmtUsd = (n: number) => n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const clr = (v: number) => v >= 0 ? "text-price-up" : "text-price-down";
const sign = (v: number) => v >= 0 ? "+" : "";

// ── Trade Analysis Result ─────────────────────────────────────────────────────
function AnalysisResult({ r }: { r: TradeAnalysisResult }) {
  const scoreColor = r.quality_score >= 0.7 ? "text-price-up" : r.quality_score >= 0.4 ? "text-yellow-400" : "text-price-down";
  const verdictIcon = r.verdict === "Quyết định tốt" ? "✅" : r.verdict === "Quyết định sai" ? "❌" : "⚠️";
  const scoreBarColor = r.quality_score >= 0.7 ? "bg-price-up" : r.quality_score >= 0.4 ? "bg-yellow-500" : "bg-price-down";

  return (
    <>
      {r.cached && (
        <div className="text-[10px] text-gray-600 flex items-center gap-1">
          <span className="w-1.5 h-1.5 rounded-full bg-gray-600 inline-block" />
          Kết quả đã lưu từ lần phân tích trước
        </div>
      )}
      <div className="bg-dark-bg rounded-xl p-4 border border-dark-border">
        <div className="flex items-center justify-between mb-3">
          <span className="text-sm font-bold">{verdictIcon} {r.verdict}</span>
          <span className={`text-sm font-bold ${scoreColor}`}>
            Chất lượng: {(r.quality_score * 10).toFixed(1)}/10
          </span>
        </div>
        <div className="h-1.5 bg-dark-border rounded-full overflow-hidden">
          <div className={`h-full rounded-full transition-all ${scoreBarColor}`} style={{ width: `${r.quality_score * 100}%` }} />
        </div>
      </div>
      <div>
        <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Vì sao bot quyết định thế này?</div>
        <p className="text-sm text-gray-200 leading-relaxed bg-dark-bg rounded-lg p-3 border border-dark-border">{r.why}</p>
      </div>
      {r.lesson && (
        <div className={`rounded-xl p-4 border ${r.lesson_polarity === "GOOD" ? "bg-price-up/10 border-price-up/30" : "bg-orange-950/30 border-orange-700/40"}`}>
          <div className="flex items-center gap-2 mb-2">
            <span className="text-xs font-bold">
              {r.lesson_polarity === "GOOD" ? "💡 Bài học tích cực" : "⚠️ Bài học cảnh báo"}
            </span>
            {r.lesson_saved && (
              <span className="text-[10px] bg-blue-900/50 text-blue-400 border border-blue-700/40 px-1.5 py-0.5 rounded">
                Đã lưu vào kho kiến thức
              </span>
            )}
          </div>
          <p className="text-sm text-gray-200 leading-relaxed">{r.lesson}</p>
          <div className="flex gap-1.5 mt-2 flex-wrap">
            {r.lesson_tags?.map(tag => (
              <span key={tag} className="text-[10px] bg-dark-surface border border-dark-border px-2 py-0.5 rounded text-gray-400">#{tag}</span>
            ))}
          </div>
        </div>
      )}
    </>
  );
}

// ── Equity Curve SVG ──────────────────────────────────────────────────────────
function EquityChart({ data, start = 5000 }: { data: { t: string; v: number }[]; start?: number }) {
  if (data.length < 2) {
    return (
      <div className="flex items-center justify-center h-24 text-gray-600 text-xs border border-dark-border rounded-lg">
        Chưa có dữ liệu — cần ít nhất 2 lệnh đã đóng
      </div>
    );
  }
  const W = 600, H = 96, PX = 6, PY = 8;
  const vals = data.map(d => d.v);
  const minV = Math.min(...vals, start) * 0.998;
  const maxV = Math.max(...vals, start) * 1.002;
  const range = maxV - minV || 1;
  const px = (i: number) => PX + (i / (data.length - 1)) * (W - PX * 2);
  const py = (v: number) => H - PY - ((v - minV) / range) * (H - PY * 2);
  const linePts = data.map((d, i) => `${px(i)},${py(d.v)}`).join(" ");
  const areaPts = `${px(0)},${H} ` + data.map((d, i) => `${px(i)},${py(d.v)}`).join(" ") + ` ${px(data.length - 1)},${H}`;
  const last = vals[vals.length - 1];
  const isUp = last >= start;
  const color = isUp ? "#22c55e" : "#ef4444";
  const gradId = `eq-${isUp ? "up" : "dn"}`;
  const startY = py(start);

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full" style={{ height: 96 }} preserveAspectRatio="none">
      <defs>
        <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.25" />
          <stop offset="100%" stopColor={color} stopOpacity="0.01" />
        </linearGradient>
      </defs>
      {/* baseline at start capital */}
      <line x1={PX} y1={startY} x2={W - PX} y2={startY} stroke="#374151" strokeWidth="1" strokeDasharray="4 3" />
      {/* area fill */}
      <polygon points={areaPts} fill={`url(#${gradId})`} />
      {/* line */}
      <polyline points={linePts} fill="none" stroke={color} strokeWidth="1.8" strokeLinejoin="round" />
      {/* last point dot */}
      <circle cx={px(data.length - 1)} cy={py(last)} r="3" fill={color} />
    </svg>
  );
}

// ── Liq Distance badge ────────────────────────────────────────────────────────
function LiqBadge({ pct }: { pct: number }) {
  const danger = pct < 10;
  const warn = pct < 20;
  return (
    <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ml-1 ${
      danger ? "bg-red-900/60 text-red-400 animate-pulse" :
      warn   ? "bg-yellow-900/50 text-yellow-400" :
               "bg-dark-border text-gray-500"
    }`}>
      {pct.toFixed(1)}% to liq
    </span>
  );
}

export default function CryptoPage() {
  const [tab, setTab] = useState<"market" | "bots" | "futures">("futures");
  const [assets, setAssets] = useState<Asset[]>([]);
  const [bots, setBots] = useState<CryptoBot[]>([]);
  const [futuresBots, setFuturesBots] = useState<FuturesBot[]>([]);
  const [detail, setDetail] = useState<CryptoBot | null>(null);
  const [fDetail, setFDetail] = useState<FuturesBot | null>(null);
  const [filter, setFilter] = useState<"ALL" | "CRYPTO" | "COMMODITY">("ALL");
  const [sortBy, setSortBy] = useState<"rank" | "change_up" | "change_down" | "mcap">("rank");
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState("");
  const [mobileFDetail, setMobileFDetail] = useState(false);
  const [mobileBotDetail, setMobileBotDetail] = useState(false);
  const [closingAll, setClosingAll] = useState(false);
  const [analyzeModal, setAnalyzeModal] = useState<{
    order: BotOrder;
    loading: boolean;
    result: TradeAnalysisResult | null;
    error: string | null;
  } | null>(null);

  const [futuresAnalyzeModal, setFuturesAnalyzeModal] = useState<{
    pos: FuturesBot["recent_closed"][number];
    loading: boolean;
    result: TradeAnalysisResult | null;
    error: string | null;
  } | null>(null);

  async function analyzeFuturesTrade(pos: FuturesBot["recent_closed"][number]) {
    setFuturesAnalyzeModal({ pos, loading: true, result: null, error: null });
    try {
      const r = await apiClient.post(`/crypto/futures/analyze-trade/${pos.id}/`, {}, { timeout: 120000 });
      setFuturesAnalyzeModal(prev => prev ? { ...prev, loading: false, result: r.data } : null);
      // Cập nhật has_analysis trong danh sách
      setFuturesBots(prev => prev.map(bot => ({
        ...bot,
        recent_closed: bot.recent_closed.map(p =>
          p.id === pos.id ? { ...p, has_analysis: true } : p
        ),
      })));
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { error?: string } } })?.response?.data?.error ?? "Không thể kết nối. Kiểm tra Ollama đang chạy.";
      setFuturesAnalyzeModal(prev => prev ? { ...prev, loading: false, error: msg } : null);
    }
  }

  async function analyzeOrder(order: BotOrder) {
    setAnalyzeModal({ order, loading: true, result: null, error: null });
    try {
      const r = await apiClient.post(`/crypto/bots/analyze-trade/${order.id}/`, {}, { timeout: 120000 });
      setAnalyzeModal(prev => prev ? { ...prev, loading: false, result: r.data } : null);
      // Cập nhật has_analysis trong danh sách
      setBots(prev => prev.map(bot => ({
        ...bot,
        recent_orders: bot.recent_orders.map(o =>
          o.id === order.id ? { ...o, has_analysis: true } : o
        ),
      })));
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { error?: string } } })?.response?.data?.error ?? "Không thể kết nối. Kiểm tra Ollama đang chạy.";
      setAnalyzeModal(prev => prev ? { ...prev, loading: false, error: msg } : null);
    }
  }

  async function handleCloseAll() {
    if (!confirm("⚠️ Đóng TẤT CẢ lệnh đang mở của mọi bot?\nDùng khi tắt server để tránh mất kiểm soát vị thế.")) return;
    setClosingAll(true);
    try {
      const r = await apiClient.post("/crypto/futures/close-all/");
      alert(`✅ Đã đóng ${r.data.closed} lệnh${r.data.errors ? ` (${r.data.errors} lỗi)` : ""}`);
      await loadFutures();
    } catch {
      alert("❌ Lỗi khi đóng lệnh. Kiểm tra server.");
    } finally {
      setClosingAll(false);
    }
  }

  const assetsRef = useRef<Asset[]>([]);

  const loadMarket = useCallback(async () => {
    try {
      const r = await apiClient.get("/crypto/market/");
      assetsRef.current = r.data;
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

  // Initial load + slow refresh for bots (15s)
  useEffect(() => {
    loadMarket(); loadBots(); loadFutures();
    const id = setInterval(() => { loadBots(); loadFutures(); }, 15000);
    return () => clearInterval(id);
  }, [loadMarket, loadBots, loadFutures]);

  // SSE — live price stream for market tab
  useEffect(() => {
    const baseUrl = (apiClient.defaults.baseURL ?? "").replace(/\/$/, "");
    const es = new EventSource(`${baseUrl}/crypto/prices/stream/`);

    es.onmessage = (e) => {
      try {
        const prices: Array<{ symbol: string; price: number; change_24h: number; updated_at: string }> = JSON.parse(e.data);
        setAssets(prev => {
          const map = new Map(prices.map(p => [p.symbol, p]));
          let changed = false;
          const next = prev.map(a => {
            const u = map.get(a.symbol);
            if (!u || (u.price === a.price && u.change_24h === a.change_24h)) return a;
            changed = true;
            return { ...a, price: u.price, change_24h: u.change_24h, updated_at: u.updated_at };
          });
          if (!changed) return prev;
          setLastUpdate(new Date().toLocaleTimeString("vi-VN"));
          return next;
        });
      } catch {}
    };

    es.onerror = () => {
      // EventSource auto-reconnects, no action needed
    };

    return () => es.close();
  }, []);

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
      <div className="px-3 md:px-4 py-2 border-b border-dark-border bg-dark-surface flex items-center justify-between flex-shrink-0 gap-2">
        <div className="flex items-center gap-3 md:gap-6 min-w-0">
          <div className="shrink-0">
            <div className="font-bold text-sm md:text-lg flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse inline-block" />
              CryptoSim
            </div>
            <div className="hidden md:block text-[11px] text-gray-500">24/7 · Top 30 Crypto + Vàng + Dầu · Spot & Futures</div>
          </div>
          <div className="flex gap-2 md:gap-5 text-[10px] md:text-xs overflow-x-auto">
            {[btc, eth, xau, wti].filter(Boolean).map(a => a && (
              <div key={a.symbol} className="shrink-0">
                <span className="text-gray-400">{a.symbol} </span>
                <span className="font-mono font-semibold">${fmtPrice(a.price)}</span>
                <span className={`ml-0.5 font-semibold ${a.change_24h >= 0 ? "text-price-up" : "text-price-down"}`}>
                  {a.change_24h >= 0 ? "+" : ""}{a.change_24h.toFixed(2)}%
                </span>
              </div>
            ))}
          </div>
        </div>
        <div className="text-[10px] md:text-[11px] text-gray-500 shrink-0">{lastUpdate || "..."}</div>
      </div>

      {/* Tabs */}
      <div className="flex gap-0.5 md:gap-1 px-2 md:px-4 pt-2 border-b border-dark-border flex-shrink-0">
        {([["market", "📈 Bảng giá", "📈 Giá"], ["bots", "🤖 Spot Bots", "🤖 Spot"], ["futures", "⚡ Long/Short Bots", "⚡ L/S"]] as const).map(([t, l, lMobile]) => (
          <button key={t} onClick={() => { setTab(t); setMobileFDetail(false); setMobileBotDetail(false); }}
            className={`px-3 md:px-5 py-1.5 text-xs md:text-sm rounded-t-md transition ${tab === t ? "bg-dark-surface text-white border border-b-dark-surface border-dark-border border-b-0" : "text-gray-500 hover:text-white"}`}>
            <span className="hidden md:inline">{l}</span>
            <span className="md:hidden">{lMobile}</span>
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-hidden">

        {/* ── MARKET TAB ── */}
        {tab === "market" && (
          <div className="h-full flex flex-col">
            <div className="px-2 md:px-4 py-2 flex items-center gap-1.5 md:gap-3 text-xs border-b border-dark-border flex-shrink-0 overflow-x-auto">
              <span className="text-gray-500 shrink-0">Lọc:</span>
              {(["ALL", "CRYPTO", "COMMODITY"] as const).map(f => (
                <button key={f} onClick={() => setFilter(f)} className={`px-2 md:px-2.5 py-0.5 rounded text-xs shrink-0 ${filter === f ? "bg-blue-600 text-white" : "text-gray-400 hover:text-white"}`}>
                  {f === "ALL" ? "Tất cả" : f === "CRYPTO" ? "Crypto" : "Hàng hóa"}
                </button>
              ))}
              <span className="text-gray-500 ml-1 md:ml-3 shrink-0">Sắp:</span>
              {([["rank", "Rank"], ["change_up", "Tăng"], ["change_down", "Giảm"], ["mcap", "Vốn hóa"]] as const).map(([s, l]) => (
                <button key={s} onClick={() => setSortBy(s)} className={`px-2 md:px-2.5 py-0.5 rounded text-xs shrink-0 ${sortBy === s ? "bg-blue-600 text-white" : "text-gray-400 hover:text-white"}`}>{l}</button>
              ))}
            </div>
            <div className="flex-1 overflow-auto">
              <table className="w-full">
                <thead className="sticky top-0 bg-dark-surface text-gray-500 text-xs z-10 border-b border-dark-border">
                  <tr>
                    <th className="text-right px-2 md:px-3 py-2 w-8">#</th>
                    <th className="text-left px-2 md:px-3 py-2">Tài sản</th>
                    <th className="text-right px-2 md:px-3 py-2">Giá (USD)</th>
                    <th className="text-right px-2 md:px-3 py-2">24h</th>
                    <th className="hidden md:table-cell text-right px-3 py-2">KL 24h</th>
                    <th className="hidden md:table-cell text-right px-3 py-2">Vốn hóa</th>
                    <th className="hidden lg:table-cell text-right px-3 py-2">Cập nhật</th>
                  </tr>
                </thead>
                <tbody>
                  {loading && (
                    <tr><td colSpan={7} className="text-center py-16 text-gray-600 text-sm">Đang tải...</td></tr>
                  )}
                  {!loading && displayed.length === 0 && (
                    <tr><td colSpan={7} className="text-center py-16 text-gray-600 text-sm">Chưa có dữ liệu</td></tr>
                  )}
                  {displayed.map(a => (
                    <CryptoAssetRow key={a.symbol} asset={a} />
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* ── SPOT BOTS TAB ── */}
        {tab === "bots" && (
          <div className="h-full flex overflow-hidden">
            <div className={`${mobileBotDetail ? "hidden md:flex" : "flex"} flex-col w-full md:w-64 border-r border-dark-border overflow-y-auto flex-shrink-0 bg-dark-surface`}>
              <div className="p-3 border-b border-dark-border">
                <div className="text-xs font-semibold text-gray-300">SPOT BOT LEADERBOARD</div>
                <div className="text-[10px] text-gray-600 mt-0.5">Mua/Bán · $5,000 USD · 24/7</div>
              </div>
              {bots.length === 0 ? (
                <div className="p-4 text-xs text-gray-500">Chưa có bot.</div>
              ) : bots.map((bot, i) => {
                const up = bot.pnl_pct >= 0;
                return (
                  <div key={bot.username} onClick={() => { setDetail(bot); setMobileBotDetail(true); }}
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
              <div className={`${!mobileBotDetail ? "hidden md:flex" : "flex"} flex-col flex-1 overflow-y-auto p-3 md:p-5`}>
                <button className="md:hidden mb-3 text-sm text-gray-400 flex items-center gap-1 hover:text-white transition" onClick={() => setMobileBotDetail(false)}>
                  ← Quay lại
                </button>
                <div className="flex items-start justify-between mb-4 md:mb-5">
                  <div>
                    <h2 className="text-xl md:text-2xl font-bold">{detail.display_name}</h2>
                    <span className="text-xs bg-dark-surface border border-dark-border px-2 py-0.5 rounded text-gray-400">{detail.model}</span>
                  </div>
                  <div className="text-right">
                    <div className={`text-3xl font-bold ${clr(detail.pnl_pct)}`}>{sign(detail.pnl_pct)}{detail.pnl_pct.toFixed(2)}%</div>
                    <div className={`text-base font-semibold ${clr(detail.pnl_usd)}`}>{detail.pnl_usd >= 0 ? "Lời " : "Lỗ "}${fmtUsd(Math.abs(detail.pnl_usd))}</div>
                  </div>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-2 md:gap-3 mb-4 md:mb-5">
                  {[
                    { label: "Tổng tài sản", value: `$${fmtUsd(detail.total_value_usd)}`, sub: "USD" },
                    { label: "Tiền mặt", value: `$${fmtUsd(detail.cash_usd)}`, sub: `${detail.total_value_usd > 0 ? ((detail.cash_usd / detail.total_value_usd) * 100).toFixed(0) : 0}% danh mục` },
                    { label: "Crypto", value: `$${fmtUsd(detail.asset_value_usd)}`, sub: `${detail.holdings.length} mã` },
                    { label: detail.pnl_usd >= 0 ? "💰 Lời" : "📉 Lỗ", value: `${sign(detail.pnl_usd)}$${fmtUsd(Math.abs(detail.pnl_usd))}`, sub: "so với vốn $5,000", color: clr(detail.pnl_usd) },
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
                          <td className={`py-1.5 text-right font-bold text-xs ${clr(h.pnl_pct)}`}>{sign(h.pnl_pct)}{h.pnl_pct.toFixed(2)}%</td>
                        </tr>
                      ))}</tbody>
                    </table>
                  </div>
                )}
                {detail.recent_orders.length > 0 && (
                  <div>
                    <div className="text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">
                      Lệnh gần đây
                      <span className="ml-2 text-gray-600 font-normal normal-case">Bấm 🔍 để Qwen 3.5 phân tích</span>
                    </div>
                    <div className="space-y-1.5">{detail.recent_orders.map((o) => (
                      <div key={o.id} className="flex items-center gap-2 text-xs bg-dark-surface rounded-lg px-3 py-2 border border-dark-border">
                        <span className={`font-bold px-2 py-0.5 rounded text-[10px] shrink-0 ${o.side === "BUY" ? "bg-price-up/20 text-price-up" : "bg-price-down/20 text-price-down"}`}>{o.side}</span>
                        <span className="font-bold shrink-0">{o.symbol}</span>
                        <span className="text-gray-400 hidden sm:inline">{fmtQty(o.quantity)} @ ${fmtPrice(o.price)}</span>
                        <span className="text-gray-500 font-semibold shrink-0">= ${fmtUsd(o.total)}</span>
                        {o.side === "SELL" && o.pnl_pct !== null && (
                          <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded shrink-0 ${
                            Math.abs(o.pnl_pct) < 0.01 ? "bg-gray-700 text-gray-400" :
                            o.pnl_pct > 0 ? "bg-price-up/20 text-price-up" : "bg-price-down/20 text-price-down"
                          }`}>
                            {Math.abs(o.pnl_pct) < 0.01 ? "Hòa" : `${o.pnl_pct > 0 ? "+" : ""}${o.pnl_pct.toFixed(1)}%`}
                          </span>
                        )}
                        <span className="ml-auto text-gray-600 shrink-0">{o.created_at}</span>
                        <button
                          onClick={() => analyzeOrder(o)}
                          title={o.has_analysis ? "Xem lại phân tích" : "Phân tích lệnh này bằng Qwen 3.5"}
                          className={`shrink-0 text-sm px-1.5 py-0.5 rounded transition hover:scale-110 ${
                            o.has_analysis ? "text-yellow-400 hover:text-yellow-300" : "text-gray-500 hover:text-blue-400"
                          }`}
                        >
                          {o.has_analysis ? "✨" : "🔍"}
                        </button>
                      </div>
                    ))}</div>
                  </div>
                )}
              </div>
            ) : <div className="hidden md:flex flex-1 items-center justify-center text-gray-500 text-sm">Chọn một bot</div>}
          </div>
        )}

        {/* ── FUTURES BOTS TAB ── */}
        {tab === "futures" && (
          <div className="h-full flex flex-col overflow-hidden">

            {/* ── Emergency Close All bar ── */}
            <div className="flex items-center justify-between px-3 py-1.5 bg-dark-surface border-b border-dark-border flex-shrink-0">
              <div className="flex items-center gap-2 text-xs text-gray-500">
                <span className="w-2 h-2 rounded-full bg-orange-400 animate-pulse inline-block" />
                {futuresBots.reduce((s, b) => s + b.open_count, 0)} lệnh đang mở ·
                tổng uPnL: <span className={clr(futuresBots.reduce((s, b) => s + b.unrealized_pnl, 0))}>
                  {sign(futuresBots.reduce((s, b) => s + b.unrealized_pnl, 0))}
                  ${fmtUsd(Math.abs(futuresBots.reduce((s, b) => s + b.unrealized_pnl, 0)))}
                </span>
              </div>
              <button
                onClick={handleCloseAll}
                disabled={closingAll || futuresBots.every(b => b.open_count === 0)}
                className={`flex items-center gap-1.5 px-3 py-1 rounded text-xs font-bold transition border ${
                  closingAll || futuresBots.every(b => b.open_count === 0)
                    ? "border-gray-700 text-gray-600 cursor-not-allowed"
                    : "border-red-700 text-red-400 hover:bg-red-950/40 hover:text-red-300"
                }`}
              >
                {closingAll ? (
                  <><span className="animate-spin inline-block">⟳</span> Đang đóng...</>
                ) : (
                  <>⛔ Đóng tất cả lệnh</>
                )}
              </button>
            </div>

            {/* ── Comparison strip (always visible) ── */}
            {futuresBots.length > 0 && (
              <div className="flex-shrink-0 border-b border-dark-border bg-dark-surface overflow-x-auto">
                <table className="w-full text-xs min-w-[700px]">
                  <thead>
                    <tr className="text-gray-500 border-b border-dark-border">
                      <th className="text-left px-3 py-1.5">Bot / Model</th>
                      <th className="text-right px-3 py-1.5">P&L%</th>
                      <th className="text-right px-3 py-1.5">Realized</th>
                      <th className="text-right px-3 py-1.5">Win rate</th>
                      <th className="text-right px-3 py-1.5">PF</th>
                      <th className="text-right px-3 py-1.5">Avg Win</th>
                      <th className="text-right px-3 py-1.5">Avg Loss</th>
                      <th className="text-right px-3 py-1.5">Lệnh</th>
                      <th className="text-right px-3 py-1.5">Lệnh/1h</th>
                      <th className="text-right px-3 py-1.5">Max DD</th>
                    </tr>
                  </thead>
                  <tbody>
                    {futuresBots.map((bot, i) => {
                      const up = bot.pnl_pct >= 0;
                      const s = bot.stats;
                      return (
                        <tr key={bot.username}
                          onClick={() => setFDetail(bot)}
                          className={`border-b border-dark-border cursor-pointer transition ${fDetail?.username === bot.username ? "bg-dark-bg" : "hover:bg-dark-bg/60"}`}>
                          <td className="px-3 py-1.5">
                            <span className="mr-1.5">{MEDALS[i]}</span>
                            <span className="font-semibold">{bot.display_name}</span>
                            <span className="ml-1.5 text-gray-600">{bot.model}</span>
                          </td>
                          <td className={`px-3 py-1.5 text-right font-bold ${up ? "text-price-up" : "text-price-down"}`}>
                            {sign(bot.pnl_pct)}{bot.pnl_pct.toFixed(2)}%
                          </td>
                          <td className={`px-3 py-1.5 text-right font-semibold ${clr(bot.realized_pnl)}`}>
                            {sign(bot.realized_pnl)}${fmtUsd(Math.abs(bot.realized_pnl))}
                          </td>
                          <td className="px-3 py-1.5 text-right">
                            <span className={s.win_rate >= 50 ? "text-price-up font-bold" : "text-gray-400"}>
                              {s.closed_trades > 0 ? `${s.win_rate}%` : "—"}
                            </span>
                          </td>
                          <td className="px-3 py-1.5 text-right">
                            <span className={s.profit_factor >= 1 ? "text-price-up" : "text-gray-400"}>
                              {s.closed_trades > 0 ? s.profit_factor.toFixed(2) : "—"}
                            </span>
                          </td>
                          <td className={`px-3 py-1.5 text-right ${s.avg_win > 0 ? "text-price-up" : "text-gray-500"}`}>
                            {s.avg_win !== 0 ? `+$${fmtUsd(s.avg_win)}` : "—"}
                          </td>
                          <td className={`px-3 py-1.5 text-right ${s.avg_loss < 0 ? "text-price-down" : "text-gray-500"}`}>
                            {s.avg_loss !== 0 ? `$${fmtUsd(s.avg_loss)}` : "—"}
                          </td>
                          <td className="px-3 py-1.5 text-right text-gray-400">{s.closed_trades}/{s.total_trades}</td>
                          <td className="px-3 py-1.5 text-right">
                            <span className={s.trades_1h > 0 ? "text-yellow-400 font-semibold" : "text-gray-600"}>
                              {s.trades_1h > 0 ? `${s.trades_1h}/h` : "—"}
                            </span>
                          </td>
                          <td className={`px-3 py-1.5 text-right ${s.max_drawdown > 20 ? "text-price-down" : "text-gray-400"}`}>
                            {s.max_drawdown > 0 ? `-${s.max_drawdown.toFixed(1)}%` : "—"}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}

            {/* ── Main panel: sidebar + detail ── */}
            <div className="flex-1 flex overflow-hidden">
              {/* Sidebar */}
              <div className={`${mobileFDetail ? "hidden md:flex" : "flex"} flex-col w-full md:w-56 border-r border-dark-border overflow-y-auto flex-shrink-0 bg-dark-surface`}>
                <div className="p-3 border-b border-dark-border">
                  <div className="text-xs font-semibold text-gray-300">⚡ LONG/SHORT</div>
                  <div className="text-[10px] text-gray-600 mt-0.5">Vốn $5,000 · Leverage 1–20x</div>
                </div>
                {futuresBots.length === 0 ? (
                  <div className="p-4 text-xs text-gray-500">Chưa có bot.</div>
                ) : futuresBots.map((bot, i) => {
                  const up = bot.pnl_pct >= 0;
                  return (
                    <div key={bot.username} onClick={() => { setFDetail(bot); setMobileFDetail(true); }}
                      className={`p-3 cursor-pointer border-b border-dark-border transition ${fDetail?.username === bot.username ? "bg-dark-bg" : "hover:bg-dark-bg/50"}`}>
                      <div className="flex items-start justify-between">
                        <div className="flex items-center gap-1.5">
                          <span className="text-sm">{MEDALS[i] ?? `${i + 1}.`}</span>
                          <div>
                            <div className="text-xs font-semibold leading-tight">{bot.display_name}</div>
                            <div className="text-[10px] text-gray-500">{bot.model}</div>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className={`text-sm font-bold ${up ? "text-price-up" : "text-price-down"}`}>{sign(bot.pnl_pct)}{bot.pnl_pct.toFixed(2)}%</div>
                          {bot.open_count > 0 && <div className="text-[10px] text-yellow-400">{bot.open_count} mở</div>}
                          {bot.stats.trades_1h > 0 && (
                            <div className="text-[10px] text-blue-400">{bot.stats.trades_1h}/h</div>
                          )}
                        </div>
                      </div>
                      <div className="mt-1.5 h-0.5 bg-dark-border rounded-full overflow-hidden">
                        <div className={`h-full rounded-full ${up ? "bg-price-up" : "bg-price-down"}`}
                          style={{ width: `${Math.min(100, Math.abs(bot.pnl_pct) * 5)}%` }} />
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Detail panel */}
              {fDetail ? (
                <div className={`${!mobileFDetail ? "hidden md:flex" : "flex"} flex-col flex-1 overflow-y-auto p-3 md:p-5`}>
                  {/* Back button - mobile only */}
                  <button className="md:hidden mb-3 text-sm text-gray-400 flex items-center gap-1 hover:text-white transition shrink-0" onClick={() => setMobileFDetail(false)}>
                    ← Quay lại
                  </button>
                  {/* Header */}
                  <div className="flex items-start justify-between mb-3 md:mb-4">
                    <div>
                      <h2 className="text-xl font-bold">{fDetail.display_name}</h2>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="text-xs bg-dark-surface border border-dark-border px-2 py-0.5 rounded text-gray-400">{fDetail.model}</span>
                        <span className="text-xs bg-yellow-900/40 border border-yellow-700/40 text-yellow-400 px-2 py-0.5 rounded">Futures · L/S</span>
                        {fDetail.stats.trades_1h > 0 && (
                          <span className="text-xs bg-blue-900/40 border border-blue-700/40 text-blue-400 px-2 py-0.5 rounded">
                            {fDetail.stats.trades_1h} lệnh/h
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className={`text-3xl font-bold ${clr(fDetail.pnl_pct)}`}>{sign(fDetail.pnl_pct)}{fDetail.pnl_pct.toFixed(2)}%</div>
                      <div className={`text-sm font-semibold ${clr(fDetail.pnl_usd)}`}>{fDetail.pnl_usd >= 0 ? "Lời " : "Lỗ "}${fmtUsd(Math.abs(fDetail.pnl_usd))}</div>
                    </div>
                  </div>

                  {/* Stats grid */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mb-3 md:mb-4">
                    {[
                      { label: "Equity", value: `$${fmtUsd(fDetail.equity_usd)}`, sub: "balance + uPnL", color: clr(fDetail.equity_usd - 5000) },
                      { label: "Realized P&L", value: `${sign(fDetail.realized_pnl)}$${fmtUsd(Math.abs(fDetail.realized_pnl))}`, sub: `${fDetail.stats.closed_trades} lệnh đã đóng`, color: clr(fDetail.realized_pnl) },
                      { label: "uPnL", value: `${sign(fDetail.unrealized_pnl)}$${fmtUsd(Math.abs(fDetail.unrealized_pnl))}`, sub: `${fDetail.open_count} vị trí mở`, color: clr(fDetail.unrealized_pnl) },
                      { label: "Margin đang dùng", value: `$${fmtUsd(fDetail.used_margin_usd)}`, sub: `Khả dụng $${fmtUsd(fDetail.available_usd)}` },
                    ].map((s, i) => (
                      <div key={i} className="bg-dark-surface rounded-lg p-3 border border-dark-border">
                        <div className="text-[11px] text-gray-500">{s.label}</div>
                        <div className={`text-base font-bold mt-0.5 ${s.color ?? "text-white"}`}>{s.value}</div>
                        <div className="text-[10px] text-gray-600">{s.sub}</div>
                      </div>
                    ))}
                  </div>

                  {/* Performance stats */}
                  <div className="grid grid-cols-3 md:grid-cols-5 gap-2 mb-3 md:mb-4">
                    {[
                      { label: "Win Rate", value: fDetail.stats.closed_trades > 0 ? `${fDetail.stats.win_rate}%` : "—", color: fDetail.stats.win_rate >= 50 ? "text-price-up" : "text-gray-300" },
                      { label: "Profit Factor", value: fDetail.stats.closed_trades > 0 ? fDetail.stats.profit_factor.toFixed(2) : "—", color: fDetail.stats.profit_factor >= 1 ? "text-price-up" : "text-gray-300" },
                      { label: "Avg Win", value: fDetail.stats.avg_win !== 0 ? `+$${fmtUsd(fDetail.stats.avg_win)}` : "—", color: "text-price-up" },
                      { label: "Avg Loss", value: fDetail.stats.avg_loss !== 0 ? `$${fmtUsd(fDetail.stats.avg_loss)}` : "—", color: "text-price-down" },
                      { label: "Max Drawdown", value: fDetail.stats.max_drawdown > 0 ? `-${fDetail.stats.max_drawdown.toFixed(1)}%` : "—", color: fDetail.stats.max_drawdown > 20 ? "text-price-down" : "text-gray-300" },
                    ].map((s, i) => (
                      <div key={i} className="bg-dark-surface rounded-lg p-2.5 border border-dark-border text-center">
                        <div className="text-[10px] text-gray-500">{s.label}</div>
                        <div className={`text-sm font-bold mt-0.5 ${s.color}`}>{s.value}</div>
                      </div>
                    ))}
                  </div>

                  {/* Equity Curve */}
                  <div className="bg-dark-surface rounded-lg border border-dark-border p-3 mb-3 md:mb-4">
                    <div className="flex items-center justify-between mb-2">
                      <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Equity Curve</div>
                      <div className="text-[10px] text-gray-600">{fDetail.equity_curve.length} điểm · mỗi điểm = 1 lệnh đóng</div>
                    </div>
                    <EquityChart data={fDetail.equity_curve} start={5000} />
                    {fDetail.equity_curve.length >= 2 && (
                      <div className="flex justify-between text-[10px] text-gray-600 mt-1">
                        <span>{fDetail.equity_curve[0]?.t}</span>
                        <span>{fDetail.equity_curve[fDetail.equity_curve.length - 1]?.t}</span>
                      </div>
                    )}
                  </div>

                  {/* Open Positions */}
                  {fDetail.open_positions.length > 0 && (
                    <div className="mb-4">
                      <div className="text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">
                        Vị trí đang mở ({fDetail.open_positions.length})
                      </div>
                      <table className="w-full text-xs">
                        <thead className="text-gray-500">
                          <tr>
                            <th className="text-left pb-1.5">Hướng</th>
                            <th className="text-left pb-1.5">Mã</th>
                            <th className="text-right pb-1.5">Entry</th>
                            <th className="text-right pb-1.5">Hiện tại</th>
                            <th className="hidden sm:table-cell text-right pb-1.5">Margin×Lev</th>
                            <th className="text-right pb-1.5">uPnL</th>
                            <th className="text-right pb-1.5">Liq</th>
                          </tr>
                        </thead>
                        <tbody>
                          {fDetail.open_positions.map((p, i) => {
                            const liqDanger = p.liq_dist_pct < 10;
                            const liqWarn  = p.liq_dist_pct < 20;
                            return (
                              <tr key={i} className={`border-t border-dark-border ${liqDanger ? "bg-red-950/30" : ""}`}>
                                <td className="py-1.5">
                                  <span className={`font-bold px-1.5 py-0.5 rounded text-[10px] ${p.direction === "LONG" ? "bg-price-up/20 text-price-up" : "bg-price-down/20 text-price-down"}`}>{p.direction}</span>
                                </td>
                                <td className="py-1.5 font-bold">{p.symbol}</td>
                                <td className="py-1.5 text-right">${fmtPrice(p.entry_price)}</td>
                                <td className="py-1.5 text-right">${fmtPrice(p.current_price)}</td>
                                <td className="hidden sm:table-cell py-1.5 text-right">${fmtUsd(p.margin_usd)} ×{p.leverage}</td>
                                <td className={`py-1.5 text-right font-bold ${clr(p.unrealized_pnl)}`}>
                                  {sign(p.unrealized_pnl)}${fmtUsd(Math.abs(p.unrealized_pnl))}
                                </td>
                                <td className="py-1.5 text-right">
                                  <span className={liqDanger ? "text-red-400 font-bold animate-pulse" : liqWarn ? "text-yellow-400" : "text-gray-500"}>
                                    <span className="hidden sm:inline">${fmtPrice(p.liq_price)} </span>
                                  </span>
                                  <LiqBadge pct={p.liq_dist_pct} />
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  )}

                  {/* Trade History */}
                  {fDetail.recent_closed.length > 0 && (
                    <div>
                      <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
                        Lịch sử ({fDetail.recent_closed.length} gần nhất)
                      </div>
                      {/* P&L summary bar */}
                      {(() => {
                        const total = fDetail.pnl_usd;
                        const pct = fDetail.pnl_pct;
                        const wins = fDetail.stats.closed_trades > 0 ? Math.round(fDetail.stats.win_rate / 100 * fDetail.stats.closed_trades) : 0;
                        const losses = fDetail.stats.closed_trades - wins;
                        return (
                          <div className={`flex items-center justify-between px-3 py-2 rounded-lg mb-2 border ${total >= 0 ? "bg-price-up/10 border-price-up/30" : "bg-price-down/10 border-price-down/30"}`}>
                            <div className="flex items-center gap-3">
                              <span className="text-xs text-gray-400">{fDetail.stats.closed_trades} lệnh đã đóng</span>
                              <span className="text-xs text-gray-600">·</span>
                              <span className="text-xs text-price-up">{wins}W</span>
                              <span className="text-xs text-price-down">{losses}L</span>
                            </div>
                            <div className="flex items-center gap-2">
                              <span className="text-xs text-gray-400">Tổng lời/lỗ</span>
                              <span className={`font-bold text-sm ${clr(total)}`}>{sign(total)}${fmtUsd(Math.abs(total))}</span>
                              <span className={`text-xs ${clr(pct)}`}>({sign(pct)}{pct.toFixed(2)}%)</span>
                            </div>
                          </div>
                        );
                      })()}

                      <div className="space-y-1">
                        {(() => {
                          const rev = [...fDetail.recent_closed].reverse();
                          let cum = 0;
                          const cumList = rev.map(p => { cum += p.pnl; return cum; });
                          return fDetail.recent_closed.map((p, i) => {
                            const cumPnl = cumList[fDetail.recent_closed.length - 1 - i];
                            return (
                              <div key={i} className="flex flex-col bg-dark-surface rounded-lg px-2 md:px-3 py-2 border border-dark-border gap-1">
                                {/* Row 1: direction, symbol, entry→exit, pnl */}
                                <div className="flex items-center gap-1.5 text-xs">
                                  <span className={`font-bold px-1.5 py-0.5 rounded text-[10px] shrink-0 ${p.direction === "LONG" ? "bg-price-up/20 text-price-up" : "bg-price-down/20 text-price-down"}`}>{p.direction}</span>
                                  <span className="font-bold shrink-0">{p.symbol}</span>
                                  <span className="text-gray-600 text-[10px] shrink-0">×{p.leverage}</span>
                                  <span className="hidden sm:inline text-gray-500 text-[10px]">${fmtPrice(p.entry)} → ${fmtPrice(p.exit)}</span>
                                  <span className={`font-bold ml-auto shrink-0 ${clr(p.pnl)}`}>{sign(p.pnl)}${fmtUsd(Math.abs(p.pnl))}</span>
                                  {p.status === "LIQUIDATED" && <span className="text-red-400 font-bold text-[10px] shrink-0">LIQ</span>}
                                </div>
                                {/* Row 2: timestamps + cumulative + analyze */}
                                <div className="flex items-center gap-2 text-[10px] text-gray-600">
                                  <span>Mở: <span className="text-gray-400">{p.opened_at}</span></span>
                                  <span>→</span>
                                  <span>Đóng: <span className="text-gray-400">{p.closed_at}</span></span>
                                  <span className="ml-auto flex items-center gap-2">
                                    Σ <span className={clr(cumPnl)}>{sign(cumPnl)}${fmtUsd(Math.abs(cumPnl))}</span>
                                    <button
                                      onClick={() => analyzeFuturesTrade(p)}
                                      title={p.has_analysis ? "Xem lại phân tích" : "Phân tích lệnh này"}
                                      className={`text-sm px-1.5 py-0.5 rounded transition hover:scale-110 ${p.has_analysis ? "text-yellow-400 hover:text-yellow-300" : "text-gray-500 hover:text-blue-400"}`}
                                    >{p.has_analysis ? "✨" : "🔍"}</button>
                                  </span>
                                </div>
                              </div>
                            );
                          });
                        })()}
                      </div>
                    </div>
                  )}
                </div>
              ) : <div className="hidden md:flex flex-1 items-center justify-center text-gray-500 text-sm">Chọn một bot để xem chi tiết</div>}
            </div>
          </div>
        )}
      </div>

      {/* ── Trade Analysis Modal ── */}
      {analyzeModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-3 md:p-6" onClick={() => !analyzeModal.loading && setAnalyzeModal(null)}>
          <div className="bg-dark-surface border border-dark-border rounded-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto shadow-2xl" onClick={e => e.stopPropagation()}>
            {/* Header */}
            <div className="flex items-center justify-between px-5 py-4 border-b border-dark-border">
              <div>
                <div className="font-bold text-base flex items-center gap-2">
                  🔍 Phân tích lệnh
                  <span className={`font-bold px-2 py-0.5 rounded text-xs ${analyzeModal.order.side === "BUY" ? "bg-price-up/20 text-price-up" : "bg-price-down/20 text-price-down"}`}>
                    {analyzeModal.order.side}
                  </span>
                  <span className="font-bold">{analyzeModal.order.symbol}</span>
                </div>
                <div className="text-[11px] text-gray-500 mt-0.5">
                  {fmtQty(analyzeModal.order.quantity)} @ ${fmtPrice(analyzeModal.order.price)} · {analyzeModal.order.created_at}
                </div>
              </div>
              {!analyzeModal.loading && (
                <button onClick={() => setAnalyzeModal(null)} className="text-gray-500 hover:text-white text-xl leading-none transition shrink-0 ml-3">×</button>
              )}
            </div>

            <div className="px-5 py-4 space-y-4">
              {/* Loading */}
              {analyzeModal.loading && (
                <div className="flex flex-col items-center justify-center py-10 gap-4">
                  <div className="w-10 h-10 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
                  <div className="text-sm text-gray-400 text-center">
                    Qwen 3.5 đang phân tích...<br />
                    <span className="text-xs text-gray-600">Có thể mất 30–60 giây</span>
                  </div>
                </div>
              )}

              {/* Error */}
              {analyzeModal.error && (
                <div className="bg-red-950/40 border border-red-800/50 rounded-lg px-4 py-3 text-sm text-red-400">
                  ❌ {analyzeModal.error}
                </div>
              )}

              {/* Result */}
              {analyzeModal.result && <AnalysisResult r={analyzeModal.result} />}
            </div>
          </div>
        </div>
      )}

      {/* ── Futures Trade Analysis Modal ── */}
      {futuresAnalyzeModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-3 md:p-6" onClick={() => !futuresAnalyzeModal.loading && setFuturesAnalyzeModal(null)}>
          <div className="bg-dark-surface border border-dark-border rounded-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto shadow-2xl" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between px-5 py-4 border-b border-dark-border">
              <div>
                <div className="font-bold text-base flex items-center gap-2">
                  🔍 Phân tích lệnh Futures
                  <span className={`font-bold px-2 py-0.5 rounded text-xs ${futuresAnalyzeModal.pos.direction === "LONG" ? "bg-price-up/20 text-price-up" : "bg-price-down/20 text-price-down"}`}>
                    {futuresAnalyzeModal.pos.direction}
                  </span>
                  <span className="font-bold">{futuresAnalyzeModal.pos.symbol}</span>
                  <span className="text-xs text-gray-500">×{futuresAnalyzeModal.pos.leverage}</span>
                </div>
                <div className="text-xs text-gray-500 mt-0.5">
                  ${futuresAnalyzeModal.pos.entry.toFixed(4)} → ${futuresAnalyzeModal.pos.exit.toFixed(4)} ·{" "}
                  <span className={clr(futuresAnalyzeModal.pos.pnl)}>{sign(futuresAnalyzeModal.pos.pnl)}${fmtUsd(Math.abs(futuresAnalyzeModal.pos.pnl))}</span>
                </div>
              </div>
              {!futuresAnalyzeModal.loading && (
                <button onClick={() => setFuturesAnalyzeModal(null)} className="text-gray-500 hover:text-white text-xl leading-none transition shrink-0 ml-3">×</button>
              )}
            </div>

            <div className="px-5 py-4 space-y-4">
              {futuresAnalyzeModal.loading && (
                <div className="flex flex-col items-center justify-center py-10 gap-4">
                  <div className="w-10 h-10 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
                  <div className="text-sm text-gray-400 text-center">
                    Qwen đang phân tích...<br />
                    <span className="text-xs text-gray-600">Có thể mất 30–60 giây</span>
                  </div>
                </div>
              )}
              {futuresAnalyzeModal.error && (
                <div className="bg-red-950/40 border border-red-800/50 rounded-lg px-4 py-3 text-sm text-red-400">
                  ❌ {futuresAnalyzeModal.error}
                </div>
              )}
              {futuresAnalyzeModal.result && <AnalysisResult r={futuresAnalyzeModal.result} />}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

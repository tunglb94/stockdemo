"use client";
import { useEffect, useState } from "react";
import apiClient from "@/services/apiClient";

interface BotResult {
  username: string;
  display_name: string;
  model: string;
  total_value: number;
  cash: number;
  stock_value: number;
  pnl: number;
  pnl_pct: number;
  matched_orders: number;
  pending_orders: number;
  holdings: { symbol: string; quantity: number; avg_cost: number; current_price: number; pnl_pct: number }[];
  recent_orders: { symbol: string; side: string; quantity: number; price: number; status: string; created_at: string }[];
}

interface Analysis {
  created_at: string;
  market_outlook: "BULLISH" | "BEARISH" | "NEUTRAL";
  summary: string;
  evaluations: { bot: string; verdict: "WINNING" | "LOSING" | "NEUTRAL"; score: number; comment: string }[];
  best_strategy: string;
  warning: string | null;
}

const MEDALS = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"];
const MODEL_SHORT: Record<string, string> = {
  "qwen3:30b-a3b": "Qwen3-30B",
  "gemma3:12b": "Gemma3-12B",
  "qwen2.5:7b": "Qwen2.5-7B",
  "hermes3": "Hermes3",
};

const OUTLOOK_CFG = {
  BULLISH:  { label: "TĂNG",    cls: "text-price-up  bg-price-up/10  border-price-up/30"  },
  BEARISH:  { label: "GIẢM",   cls: "text-price-down bg-price-down/10 border-price-down/30" },
  NEUTRAL:  { label: "SIDEWAY", cls: "text-yellow-400 bg-yellow-400/10 border-yellow-400/30" },
};
const VERDICT_CFG = {
  WINNING: { label: "WINNING", cls: "text-price-up  bg-price-up/10"  },
  LOSING:  { label: "LOSING",  cls: "text-price-down bg-price-down/10" },
  NEUTRAL: { label: "NEUTRAL", cls: "text-gray-400  bg-gray-400/10"  },
};

function fmt(n: number) { return new Intl.NumberFormat("vi-VN").format(Math.round(n)); }

export default function BotsPage() {
  const [bots, setBots] = useState<BotResult[]>([]);
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<string | null>(null);

  async function load() {
    try {
      const [lb, an] = await Promise.all([
        apiClient.get("/bots/leaderboard/"),
        apiClient.get("/bots/analysis/"),
      ]);
      setBots(lb.data);
      setAnalysis(an.data);
      if (lb.data.length && !selected) setSelected(lb.data[0].username);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  }

  useEffect(() => { load(); const t = setInterval(load, 30_000); return () => clearInterval(t); }, []);

  const detail = bots.find(b => b.username === selected);

  if (loading) return <div className="flex items-center justify-center h-64 text-gray-500">Đang tải...</div>;

  return (
    <div className="flex h-full gap-0 overflow-hidden">
      {/* Left: Leaderboard */}
      <div className="w-72 border-r border-dark-border flex flex-col shrink-0">
        <div className="px-4 py-3 border-b border-dark-border">
          <h1 className="text-sm font-bold text-white">🏆 AI Bot Leaderboard</h1>
          <p className="text-xs text-gray-500 mt-0.5">Vốn ban đầu: 100,000,000đ / bot</p>
        </div>
        <div className="flex-1 overflow-y-auto">
          {bots.map((bot, i) => {
            const up = bot.pnl_pct >= 0;
            const active = selected === bot.username;
            // Tìm evaluation của bot này từ Hermes
            const ev = analysis?.evaluations?.find(e => e.bot === bot.display_name);
            return (
              <button key={bot.username} onClick={() => setSelected(bot.username)}
                className={`w-full text-left px-4 py-3 border-b border-dark-border/50 transition ${
                  active ? "bg-dark-bg" : "hover:bg-dark-bg/50"
                }`}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-base">{MEDALS[i]}</span>
                    <div>
                      <div className="text-xs font-semibold text-white">{bot.display_name}</div>
                      <div className="text-[10px] text-gray-500">{MODEL_SHORT[bot.model] || bot.model}</div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className={`text-sm font-bold ${up ? "text-price-up" : "text-price-down"}`}>
                      {up ? "+" : ""}{bot.pnl_pct.toFixed(2)}%
                    </div>
                    {ev && (
                      <div className={`text-[10px] px-1 rounded ${VERDICT_CFG[ev.verdict]?.cls}`}>
                        {ev.verdict} {ev.score}/10
                      </div>
                    )}
                  </div>
                </div>
                <div className="mt-1.5 bg-dark-surface rounded-full h-1">
                  <div className={`h-1 rounded-full ${up ? "bg-price-up" : "bg-price-down"}`}
                    style={{ width: `${Math.min(100, Math.abs(bot.pnl_pct) * 10)}%` }} />
                </div>
              </button>
            );
          })}
        </div>
        <div className="px-4 py-2 border-t border-dark-border">
          <p className="text-[10px] text-gray-600">Cập nhật 30s • Bot chạy liên tục</p>
        </div>
      </div>

      {/* Right: Detail + Hermes Panel */}
      <div className="flex-1 flex flex-col overflow-hidden">

        {/* Hermes3 Analyst Banner */}
        {analysis && (
          <div className="border-b border-dark-border bg-dark-surface shrink-0">
            <div className="px-4 py-3">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1.5">
                    <span className="text-xs font-bold text-purple-400">🔮 Hermes3 Analyst</span>
                    <span className={`text-[10px] px-1.5 py-0.5 rounded border font-bold ${
                      OUTLOOK_CFG[analysis.market_outlook]?.cls
                    }`}>
                      {OUTLOOK_CFG[analysis.market_outlook]?.label}
                    </span>
                    <span className="text-[10px] text-gray-600">{analysis.created_at}</span>
                  </div>
                  <p className="text-xs text-gray-300 leading-relaxed">{analysis.summary}</p>
                  {analysis.best_strategy && (
                    <p className="text-[11px] text-purple-300 mt-1">
                      ⭐ {analysis.best_strategy}
                    </p>
                  )}
                  {analysis.warning && (
                    <p className="text-[11px] text-yellow-400 mt-1">
                      ⚠️ {analysis.warning}
                    </p>
                  )}
                </div>
                {/* Mini score cards */}
                <div className="flex gap-1.5 shrink-0">
                  {analysis.evaluations?.map(ev => (
                    <div key={ev.bot} className={`text-center px-2 py-1 rounded border text-[10px] ${
                      VERDICT_CFG[ev.verdict]?.cls
                    } border-current/20`}>
                      <div className="font-bold">{ev.score}/10</div>
                      <div className="text-gray-400 truncate max-w-[60px]">{ev.bot.split(" ")[0]}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Bot detail */}
        <div className="flex-1 overflow-y-auto p-4">
          {detail ? (
            <div className="space-y-4">
              {/* Header */}
              <div className="flex items-start justify-between">
                <div>
                  <h2 className="text-lg font-bold text-white">{detail.display_name}</h2>
                  <span className="text-xs text-gray-400 bg-dark-surface border border-dark-border px-2 py-0.5 rounded">
                    {MODEL_SHORT[detail.model] || detail.model}
                  </span>
                </div>
                <div className="text-right">
                  <div className={`text-2xl font-bold ${detail.pnl >= 0 ? "text-price-up" : "text-price-down"}`}>
                    {detail.pnl >= 0 ? "+" : ""}{detail.pnl_pct.toFixed(2)}%
                  </div>
                  {/* Hermes comment for this bot */}
                  {(() => {
                    const ev = analysis?.evaluations?.find(e => e.bot === detail.display_name);
                    if (!ev) return null;
                    return (
                      <div className={`mt-1 text-[11px] px-2 py-1 rounded text-left max-w-[260px] ${VERDICT_CFG[ev.verdict]?.cls}`}>
                        {ev.comment}
                      </div>
                    );
                  })()}
                </div>
              </div>

              {/* Stats */}
              <div className="grid grid-cols-3 gap-3">
                {[
                  { label: "Tổng tài sản", value: fmt(detail.total_value) + "đ", sub: "" },
                  { label: "Tiền mặt", value: fmt(detail.cash) + "đ", sub: `${(detail.cash/detail.total_value*100).toFixed(1)}% danh mục` },
                  { label: "Cổ phiếu", value: fmt(detail.stock_value) + "đ", sub: `${detail.holdings.length} mã` },
                  { label: "P&L", value: (detail.pnl >= 0 ? "+" : "") + fmt(detail.pnl) + "đ",
                    sub: "", color: detail.pnl >= 0 ? "text-price-up" : "text-price-down" },
                  { label: "Lệnh khớp", value: detail.matched_orders.toString(), sub: "" },
                  { label: "Đang chờ", value: detail.pending_orders.toString(), sub: "" },
                ].map(s => (
                  <div key={s.label} className="bg-dark-surface border border-dark-border rounded-lg p-3">
                    <div className="text-xs text-gray-500">{s.label}</div>
                    <div className={`text-sm font-bold mt-1 ${(s as any).color || "text-white"}`}>{s.value}</div>
                    {s.sub && <div className="text-[10px] text-gray-600 mt-0.5">{s.sub}</div>}
                  </div>
                ))}
              </div>

              {/* Holdings */}
              {detail.holdings.length > 0 && (
                <div className="bg-dark-surface border border-dark-border rounded-lg p-3">
                  <h3 className="text-xs font-semibold text-gray-400 mb-2">DANH MỤC ĐANG GIỮ</h3>
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="text-gray-500 border-b border-dark-border">
                        <th className="text-left pb-1">Mã</th>
                        <th className="text-right pb-1">SL</th>
                        <th className="text-right pb-1">Giá vốn</th>
                        <th className="text-right pb-1">Giá hiện tại</th>
                        <th className="text-right pb-1">P&L%</th>
                      </tr>
                    </thead>
                    <tbody>
                      {detail.holdings.map(h => (
                        <tr key={h.symbol} className="border-b border-dark-border/30">
                          <td className="py-1 font-bold text-white">{h.symbol}</td>
                          <td className="py-1 text-right text-gray-400">{h.quantity}</td>
                          <td className="py-1 text-right text-gray-400">{(h.avg_cost/1000).toFixed(2)}</td>
                          <td className="py-1 text-right text-gray-400">{(h.current_price/1000).toFixed(2)}</td>
                          <td className={`py-1 text-right font-semibold ${h.pnl_pct >= 0 ? "text-price-up" : "text-price-down"}`}>
                            {h.pnl_pct >= 0 ? "+" : ""}{h.pnl_pct.toFixed(2)}%
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {/* Recent orders */}
              {detail.recent_orders.length > 0 && (
                <div className="bg-dark-surface border border-dark-border rounded-lg p-3">
                  <h3 className="text-xs font-semibold text-gray-400 mb-2">LỆNH GẦN ĐÂY</h3>
                  <div className="space-y-1">
                    {detail.recent_orders.map((o, i) => (
                      <div key={i} className="flex items-center justify-between text-xs py-1 border-b border-dark-border/30">
                        <div className="flex items-center gap-2">
                          <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                            o.side === "BUY" ? "bg-price-up/20 text-price-up" : "bg-price-down/20 text-price-down"
                          }`}>{o.side}</span>
                          <span className="font-bold text-white">{o.symbol}</span>
                          <span className="text-gray-500">{o.quantity} cổ @ {(o.price/1000).toFixed(2)}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className={`text-[10px] ${o.status === "MATCHED" ? "text-price-up" : "text-gray-500"}`}>
                            {o.status === "MATCHED" ? "✅ Khớp" : "⏳ Chờ"}
                          </span>
                          <span className="text-gray-600">{o.created_at}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {detail.holdings.length === 0 && detail.matched_orders === 0 && (
                <div className="text-center py-12 text-gray-600">
                  <div className="text-4xl mb-3">🤖</div>
                  <div className="text-sm">Bot chưa giao dịch lần nào</div>
                  <div className="text-xs mt-1">Bot chạy liên tục, kiểm tra lại sau vài phút</div>
                </div>
              )}
            </div>
          ) : (
            <div className="flex items-center justify-center h-64 text-gray-600">Chọn bot để xem chi tiết</div>
          )}
        </div>
      </div>
    </div>
  );
}

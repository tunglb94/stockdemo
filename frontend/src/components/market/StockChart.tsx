"use client";
import { useEffect, useRef, useState } from "react";
import { marketService } from "@/services/marketService";
import { CandleData } from "@/types/market";
import { format, subMonths } from "date-fns";

interface Props {
  symbol: string;
}

const INTERVALS = [
  { label: "1T", months: 1, interval: "1D" },
  { label: "3T", months: 3, interval: "1D" },
  { label: "6T", months: 6, interval: "1W" },
  { label: "1N", months: 12, interval: "1M" },
];

export default function StockChart({ symbol }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<unknown>(null);
  const seriesRef = useRef<unknown>(null);
  const [activeInterval, setActiveInterval] = useState(0);
  const [data, setData] = useState<CandleData[]>([]);

  async function loadData(monthIdx: number) {
    const cfg = INTERVALS[monthIdx];
    const end = format(new Date(), "yyyy-MM-dd");
    const start = format(subMonths(new Date(), cfg.months), "yyyy-MM-dd");
    try {
      const history = await marketService.getHistory(symbol, start, end, cfg.interval);
      setData(history);
    } catch (err) {
      console.error("Lỗi load chart:", err);
    }
  }

  useEffect(() => {
    loadData(activeInterval);
  }, [symbol, activeInterval]);

  useEffect(() => {
    if (!containerRef.current || !data.length) return;

    let cleanup: (() => void) | undefined;

    import("lightweight-charts").then(({ createChart, ColorType }) => {
      if (!containerRef.current) return;

      if (chartRef.current) {
        (chartRef.current as { remove: () => void }).remove();
      }

      const chart = createChart(containerRef.current, {
        width: containerRef.current.clientWidth,
        height: 320,
        layout: {
          background: { type: ColorType.Solid, color: "#0a0e1a" },
          textColor: "#9ca3af",
        },
        grid: {
          vertLines: { color: "#1f2937" },
          horzLines: { color: "#1f2937" },
        },
        timeScale: {
          borderColor: "#1f2937",
          timeVisible: true,
        },
        rightPriceScale: { borderColor: "#1f2937" },
      });

      const candleSeries = chart.addCandlestickSeries({
        upColor: "#00b050",
        downColor: "#ff0000",
        borderUpColor: "#00b050",
        borderDownColor: "#ff0000",
        wickUpColor: "#00b050",
        wickDownColor: "#ff0000",
      });

      const chartData = data.map((d) => ({
        time: d.time as `${number}-${number}-${number}`,
        open: d.open / 1000,
        high: d.high / 1000,
        low: d.low / 1000,
        close: d.close / 1000,
      }));

      candleSeries.setData(chartData);
      chart.timeScale().fitContent();

      chartRef.current = chart;
      seriesRef.current = candleSeries;

      const resizeObserver = new ResizeObserver(() => {
        if (containerRef.current) {
          chart.resize(containerRef.current.clientWidth, 320);
        }
      });
      resizeObserver.observe(containerRef.current);
      cleanup = () => {
        resizeObserver.disconnect();
        chart.remove();
      };
    });

    return () => cleanup?.();
  }, [data]);

  return (
    <div className="bg-dark-surface border border-dark-border rounded-xl overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 border-b border-dark-border">
        <span className="text-sm font-semibold text-white">Biểu đồ {symbol}</span>
        <div className="flex gap-1">
          {INTERVALS.map((item, idx) => (
            <button
              key={item.label}
              onClick={() => setActiveInterval(idx)}
              className={`px-3 py-1 rounded text-xs transition ${
                activeInterval === idx
                  ? "bg-price-up text-white"
                  : "text-gray-400 hover:text-white"
              }`}
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>
      <div ref={containerRef} className="w-full" />
    </div>
  );
}

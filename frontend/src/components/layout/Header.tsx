"use client";
import { useAuthStore } from "@/store/authStore";
import { useMarketStore } from "@/store/marketStore";
import { useRouter } from "next/navigation";
import { authService } from "@/services/authService";
import { formatCurrency } from "@/utils/formatters";

function IndexBadge({ label, value, change, changePct }: {
  label: string; value: number; change: number; changePct: number;
}) {
  const up = change >= 0;
  const color = up ? "text-price-up" : "text-price-down";
  return (
    <div className="flex items-center gap-2 pr-4 border-r border-dark-border">
      <span className="text-gray-400 text-xs">{label}</span>
      <span className={`text-sm font-bold ${color}`}>{value.toFixed(2)}</span>
      <span className={`text-xs ${color}`}>
        {up ? "▲" : "▼"} {Math.abs(changePct).toFixed(2)}%
      </span>
    </div>
  );
}

function MarketStatus() {
  const now = new Date();
  const h = now.getHours(), m = now.getMinutes(), day = now.getDay();
  const t = h * 60 + m;
  const inSession = day >= 1 && day <= 5 &&
    ((t >= 9 * 60 && t <= 11 * 60 + 30) || (t >= 13 * 60 && t <= 14 * 60 + 45));
  return (
    <div className={`flex items-center gap-1.5 text-xs font-medium px-2 py-0.5 rounded ml-4 ${
      inSession ? "bg-price-up/10 text-price-up" : "bg-dark-bg text-gray-500"
    }`}>
      <span className={`w-1.5 h-1.5 rounded-full ${inSession ? "bg-price-up animate-pulse" : "bg-gray-600"}`} />
      {inSession ? "Đang GD" : "Ngoài giờ"}
    </div>
  );
}

export default function Header() {
  const { user, logout, refreshToken } = useAuthStore();
  const stocks = useMarketStore((s) => s.stocks);
  const router = useRouter();

  async function handleLogout() {
    try { if (refreshToken) await authService.logout(refreshToken); } catch {}
    logout();
    router.push("/login");
  }

  const vn30 = stocks.filter(s => s.is_vn30 && s.latest_price);
  const avgPct = vn30.length
    ? vn30.reduce((sum, s) => sum + Number(s.latest_price!.change_percent), 0) / vn30.length
    : 0;
  const base = 1280;
  const vn30Val = base * (1 + avgPct / 100);

  const balance = user?.wallet?.available_balance;

  return (
    <header className="h-11 bg-dark-surface border-b border-dark-border flex items-center justify-between px-3 md:px-4 shrink-0">
      <div className="flex items-center gap-3 md:gap-4 min-w-0">
        <div className="hidden md:flex items-center gap-4">
          {vn30.length > 0 && (
            <IndexBadge label="VN30" value={vn30Val} change={vn30Val - base} changePct={avgPct} />
          )}
        </div>
        <MarketStatus />
      </div>

      <div className="flex items-center gap-2 md:gap-4 text-xs min-w-0">
        {balance !== undefined && (
          <span className="hidden sm:inline truncate">
            <span className="text-gray-500">Khả dụng: </span>
            <span className="text-price-up font-semibold">{formatCurrency(balance)}đ</span>
          </span>
        )}
        <span className="text-gray-500 hidden sm:inline truncate max-w-[80px]">{user?.username}</span>
        <button onClick={handleLogout} className="text-gray-500 hover:text-red-400 transition text-xs shrink-0">
          Đăng xuất
        </button>
      </div>
    </header>
  );
}

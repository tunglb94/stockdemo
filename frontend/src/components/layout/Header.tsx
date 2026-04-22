"use client";
import { useAuthStore } from "@/store/authStore";
import { formatCurrency } from "@/utils/formatters";

export default function Header() {
  const { user } = useAuthStore();
  const balance = user?.wallet?.available_balance;

  return (
    <header className="h-14 bg-dark-surface border-b border-dark-border flex items-center justify-between px-6">
      <div className="text-sm text-gray-500">
        Dữ liệu từ VN30 · Delay ~5 phút
      </div>
      <div className="flex items-center gap-4">
        {balance !== undefined && (
          <div className="text-sm">
            <span className="text-gray-500">Khả dụng: </span>
            <span className="text-price-up font-semibold">
              {formatCurrency(balance)} VNĐ
            </span>
          </div>
        )}
      </div>
    </header>
  );
}

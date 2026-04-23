"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuthStore } from "@/store/authStore";
import { useRouter } from "next/navigation";
import { authService } from "@/services/authService";
import toast from "react-hot-toast";

const navItems = [
  { href: "/dashboard", label: "Tổng quan", icon: "◻" },
  { href: "/market", label: "Bảng giá", icon: "◈" },
  { href: "/portfolio", label: "Danh mục", icon: "◉" },
  { href: "/orders", label: "Lịch sử lệnh", icon: "◎" },
  { href: "/bots", label: "AI Bot Race", icon: "🤖" },
];

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout, refreshToken } = useAuthStore();

  async function handleLogout() {
    try {
      if (refreshToken) await authService.logout(refreshToken);
    } catch {}
    logout();
    router.push("/login");
    toast.success("Đã đăng xuất.");
  }

  return (
    <aside className="w-56 bg-dark-surface border-r border-dark-border flex flex-col">
      <div className="p-4 border-b border-dark-border">
        <div className="text-white font-bold text-lg">StockSim</div>
        <div className="text-gray-500 text-xs mt-1">Mô phỏng sàn VN</div>
      </div>

      <nav className="flex-1 p-3 space-y-1">
        {navItems.map((item) => {
          const active = pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition ${
                active
                  ? "bg-price-up/10 text-price-up border border-price-up/20"
                  : "text-gray-400 hover:bg-dark-bg hover:text-white"
              }`}
            >
              <span className="text-base">{item.icon}</span>
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="p-4 border-t border-dark-border">
        <div className="text-sm text-gray-400 mb-3 truncate">{user?.username}</div>
        <button
          onClick={handleLogout}
          className="w-full text-sm text-gray-500 hover:text-red-400 transition text-left"
        >
          Đăng xuất
        </button>
      </div>
    </aside>
  );
}

"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";

const navItems = [
  { href: "/dashboard", label: "Tổng quan", icon: "◻" },
  { href: "/market",    label: "Bảng giá",  icon: "◈" },
  { href: "/portfolio", label: "Danh mục",  icon: "◉" },
  { href: "/orders",    label: "Lịch sử",   icon: "◎" },
  { href: "/bots",      label: "AI VN",     icon: "🤖" },
  { href: "/crypto",    label: "Crypto",    icon: "₿" },
];

export default function BottomNav() {
  const pathname = usePathname();
  return (
    <nav className="md:hidden fixed bottom-0 left-0 right-0 z-50 bg-dark-surface border-t border-dark-border flex safe-area-pb">
      {navItems.map(item => {
        const active = pathname.startsWith(item.href);
        return (
          <Link
            key={item.href}
            href={item.href}
            className={`flex-1 flex flex-col items-center justify-center py-2 gap-0.5 transition ${
              active ? "text-price-up" : "text-gray-500 hover:text-gray-300"
            }`}
          >
            <span className="text-lg leading-none">{item.icon}</span>
            <span className="text-[9px] leading-none">{item.label}</span>
          </Link>
        );
      })}
    </nav>
  );
}

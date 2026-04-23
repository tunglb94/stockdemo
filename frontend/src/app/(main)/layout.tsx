"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/authStore";
import { authService } from "@/services/authService";
import Sidebar from "@/components/layout/Sidebar";
import Header from "@/components/layout/Header";

export default function MainLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { isAuthenticated, setAuth, logout } = useAuthStore();

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      router.push("/login");
      return;
    }
    if (!isAuthenticated) {
      authService.getProfile()
        .then((profile) => setAuth(profile, token, localStorage.getItem("refresh_token") || ""))
        .catch(() => { logout(); router.push("/login"); });
    }
  }, [isAuthenticated]);

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-dark-bg flex items-center justify-center">
        <div className="text-gray-400">Đang tải...</div>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-dark-bg overflow-hidden">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header />
        <main className="flex-1 overflow-hidden">{children}</main>
      </div>
    </div>
  );
}

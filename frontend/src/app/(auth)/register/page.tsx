"use client";
import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import toast from "react-hot-toast";
import { authService } from "@/services/authService";
import { useAuthStore } from "@/store/authStore";

export default function RegisterPage() {
  const router = useRouter();
  const { setAuth } = useAuthStore();
  const [form, setForm] = useState({
    email: "", username: "", password: "", password_confirm: "", phone: "",
  });
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (form.password !== form.password_confirm) {
      toast.error("Mật khẩu xác nhận không khớp.");
      return;
    }
    setLoading(true);
    try {
      const res = await authService.register(form);
      setAuth(res.user, res.access, res.refresh);
      toast.success(res.message || "Đăng ký thành công! Bạn đã được cấp 50 triệu VNĐ.");
      router.push("/dashboard");
    } catch (err: unknown) {
      const errors = (err as { response?: { data?: Record<string, string[]> } })?.response?.data;
      const msg = errors ? Object.values(errors).flat().join(" ") : "Đăng ký thất bại.";
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  }

  const fields = [
    { key: "email", label: "Email", type: "email", placeholder: "your@email.com" },
    { key: "username", label: "Tên hiển thị", type: "text", placeholder: "Nguyễn Văn A" },
    { key: "phone", label: "Số điện thoại (tùy chọn)", type: "tel", placeholder: "0912345678" },
    { key: "password", label: "Mật khẩu", type: "password", placeholder: "Tối thiểu 8 ký tự" },
    { key: "password_confirm", label: "Xác nhận mật khẩu", type: "password", placeholder: "••••••••" },
  ] as const;

  return (
    <div className="bg-dark-surface border border-dark-border rounded-2xl p-8">
      <h2 className="text-xl font-semibold text-white mb-2">Tạo tài khoản</h2>
      <p className="text-gray-500 text-sm mb-6">Nhận ngay 50,000,000 VNĐ để bắt đầu giao dịch</p>
      <form onSubmit={handleSubmit} className="space-y-4">
        {fields.map((f) => (
          <div key={f.key}>
            <label className="text-sm text-gray-400 block mb-1">{f.label}</label>
            <input
              type={f.type}
              required={f.key !== "phone"}
              value={form[f.key]}
              onChange={(e) => setForm({ ...form, [f.key]: e.target.value })}
              className="w-full bg-dark-bg border border-dark-border rounded-lg px-4 py-3 text-white focus:outline-none focus:border-price-up"
              placeholder={f.placeholder}
            />
          </div>
        ))}
        <button
          type="submit"
          disabled={loading}
          className="w-full bg-price-up text-white font-semibold py-3 rounded-lg hover:bg-green-600 transition disabled:opacity-50 mt-2"
        >
          {loading ? "Đang tạo tài khoản..." : "Đăng ký & Nhận 50 triệu VNĐ"}
        </button>
      </form>
      <p className="text-center text-gray-500 text-sm mt-6">
        Đã có tài khoản?{" "}
        <Link href="/login" className="text-price-up hover:underline">Đăng nhập</Link>
      </p>
    </div>
  );
}

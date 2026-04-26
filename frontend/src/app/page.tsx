import { redirect } from "next/navigation";
import Link from "next/link";

export default function LandingPage() {
  redirect("/dashboard");
  return (
    <div className="min-h-screen bg-dark-bg flex flex-col items-center justify-center px-4">
      <div className="max-w-3xl text-center">
        <div className="mb-6 inline-flex items-center gap-2 bg-green-500/10 border border-green-500/20 rounded-full px-4 py-1 text-green-400 text-sm">
          Mô phỏng 100% sàn HOSE, HNX, UPCOM
        </div>

        <h1 className="text-5xl font-bold text-white mb-4">
          Học đầu tư chứng khoán
          <span className="text-price-up"> không rủi ro</span>
        </h1>

        <p className="text-gray-400 text-lg mb-8">
          Nhận ngay <span className="text-white font-semibold">50,000,000 VNĐ</span> ảo khi đăng ký.
          Giao dịch với dữ liệu giá thật từ HOSE — trải nghiệm thực tế trước khi bỏ tiền vào thị trường.
        </p>

        <div className="flex gap-4 justify-center flex-wrap">
          <Link
            href="/register"
            className="px-8 py-3 bg-price-up text-white font-semibold rounded-lg hover:bg-green-600 transition"
          >
            Bắt đầu miễn phí
          </Link>
          <Link
            href="/login"
            className="px-8 py-3 border border-dark-border text-gray-300 rounded-lg hover:border-gray-500 transition"
          >
            Đăng nhập
          </Link>
        </div>

        <div className="mt-16 grid grid-cols-3 gap-6 text-center">
          {[
            { label: "Dữ liệu giá", value: "Thật 100%", desc: "Từ VN30 — HOSE" },
            { label: "Vốn khởi đầu", value: "50 triệu", desc: "Cấp miễn phí" },
            { label: "Cơ chế T+2", value: "Đúng chuẩn", desc: "Như sàn thật" },
          ].map((item) => (
            <div key={item.label} className="bg-dark-surface border border-dark-border rounded-xl p-6">
              <div className="text-2xl font-bold text-white">{item.value}</div>
              <div className="text-gray-400 text-sm mt-1">{item.desc}</div>
              <div className="text-xs text-gray-600 mt-2">{item.label}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

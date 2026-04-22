import type { Metadata } from "next";
import { Toaster } from "react-hot-toast";
import "./globals.css";

export const metadata: Metadata = {
  title: "StockSim - Mô phỏng sàn chứng khoán Việt Nam",
  description: "Trải nghiệm giao dịch chứng khoán an toàn với 50 triệu VNĐ ảo. Học đầu tư trước khi bỏ tiền thật.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="vi">
      <body>
        {children}
        <Toaster
          position="top-right"
          toastOptions={{
            style: { background: "#111827", color: "#e5e7eb", border: "1px solid #1f2937" },
          }}
        />
      </body>
    </html>
  );
}

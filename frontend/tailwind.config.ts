import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // Màu sắc chuẩn sàn chứng khoán Việt Nam
        price: {
          up: "#00b050",       // Xanh lá: tăng giá
          down: "#ff0000",     // Đỏ: giảm giá
          ceiling: "#ff00ff",  // Tím: giá trần
          floor: "#00b0f0",    // Xanh dương: giá sàn
          ref: "#ffff00",      // Vàng: giá tham chiếu
        },
        dark: {
          bg: "#0a0e1a",
          surface: "#111827",
          border: "#1f2937",
          text: "#e5e7eb",
        },
      },
    },
  },
  plugins: [],
};

export default config;

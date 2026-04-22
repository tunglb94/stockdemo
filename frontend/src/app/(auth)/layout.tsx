export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-dark-bg flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-white">StockSim</h1>
          <p className="text-gray-500 text-sm mt-1">Sàn chứng khoán mô phỏng Việt Nam</p>
        </div>
        {children}
      </div>
    </div>
  );
}

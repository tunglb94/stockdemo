import Sidebar from "@/components/layout/Sidebar";
import Header from "@/components/layout/Header";
import BottomNav from "@/components/layout/BottomNav";

export default function MainLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen bg-dark-bg overflow-hidden">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden min-w-0">
        <Header />
        <main className="flex-1 overflow-hidden pb-16 md:pb-0">{children}</main>
      </div>
      <BottomNav />
    </div>
  );
}

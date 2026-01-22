import { Outlet } from 'react-router-dom';
import { Header } from '../components';

export function DashboardLayout() {
  return (
    <div className="min-h-screen">
      <Header />

      <main className="max-w-7xl mx-auto px-6 py-8">
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="border-t border-white/10 mt-12 py-6">
        <div className="max-w-7xl mx-auto px-6 text-center text-sm text-slate-500">
          probablyprofit v1.0 • Built with Claude
        </div>
      </footer>
    </div>
  );
}

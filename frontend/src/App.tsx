import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Header } from './components';
import { Dashboard, Settings, History, Strategy } from './pages';

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen">
        <Header />

        <main className="max-w-7xl mx-auto px-6 py-8">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/strategy" element={<Strategy />} />
            <Route path="/history" element={<History />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </main>

        {/* Footer */}
        <footer className="border-t border-white/10 mt-12 py-6">
          <div className="max-w-7xl mx-auto px-6 text-center text-sm text-slate-500">
            probablyprofit v1.0 • Built with Claude
          </div>
        </footer>
      </div>
    </BrowserRouter>
  );
}

export default App;

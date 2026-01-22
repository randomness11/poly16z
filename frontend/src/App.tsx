import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { LandingPage, Dashboard, Settings, History, Strategy } from './pages';
import { DashboardLayout } from './layouts/DashboardLayout';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Landing page */}
        <Route path="/" element={<LandingPage />} />

        {/* Dashboard routes */}
        <Route path="/app" element={<DashboardLayout />}>
          <Route index element={<Dashboard />} />
          <Route path="settings" element={<Settings />} />
          <Route path="history" element={<History />} />
          <Route path="strategy" element={<Strategy />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;

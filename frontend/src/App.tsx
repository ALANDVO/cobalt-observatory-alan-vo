import { Routes, Route, Link, useLocation } from 'react-router-dom';
import { ToastProvider } from './components/ui';
import { DashboardPage } from './pages/DashboardPage';
import { OCSFEventsPage } from './pages/OCSFEventsPage';
import { AgentsPage } from './pages/AgentsPage';
import { EvaluationsPage } from './pages/EvaluationsPage';

const navigation = [
  { path: '/', label: 'Dashboard' },
  { path: '/ocsf', label: 'OCSF Events' },
  { path: '/agents', label: 'Agents' },
  { path: '/evaluations', label: 'Evaluations' },
];

function Navigation() {
  const location = useLocation();
  return (
    <nav className="bg-white border-b border-slate-200 sticky top-0 z-40">
      <div className="container">
        <div className="flex items-center justify-between h-16">
          <Link to="/" className="flex items-center gap-2 font-bold text-slate-900 text-xl">
            <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            <span>Cobalt Observatory</span>
          </Link>
          <div className="flex items-center gap-6">
            {navigation.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={`px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
                  location.pathname === item.path
                    ? 'bg-blue-50 text-blue-700'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                }`}
              >
                {item.label}
              </Link>
            ))}
            <div className="hidden sm:block w-px h-6 bg-slate-200 mx-2" />
            <span className="text-xs text-slate-400 font-mono">v1.0.0</span>
          </div>
        </div>
      </div>
    </nav>
  );
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<DashboardPage />} />
      <Route path="/ocsf" element={<OCSFEventsPage />} />
      <Route path="/agents" element={<AgentsPage />} />
      <Route path="/evaluations" element={<EvaluationsPage />} />
    </Routes>
  );
}

function App() {
  return (
    <ToastProvider>
      <div className="min-h-screen bg-slate-50">
        <Navigation />
        <main className="pb-8">
          <AppRoutes />
        </main>
        <footer className="bg-white border-t border-slate-200 py-4">
          <div className="container text-center text-sm text-slate-500">
            Cobalt Observatory — Alan Vo | AI & Machine Learning — alanvo@gmail.com
          </div>
        </footer>
      </div>
    </ToastProvider>
  );
}

export default App;
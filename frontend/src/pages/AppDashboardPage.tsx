// ─────────────────────────────────────────────────────────────────────────────
// pages/AppDashboardPage.tsx
// Protected user dashboard — shown after sign-in.
// Tabs: "Playground" (authenticated AI analysis) and "History" (real API data).
// ─────────────────────────────────────────────────────────────────────────────

import { useState, useEffect, Component, type ReactNode } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../context/AuthContext';

// ── Error boundary — catches render crashes and shows a message ───────────────
class ErrorBoundary extends Component<{ children: ReactNode }, { error: string | null }> {
  state = { error: null };
  static getDerivedStateFromError(e: Error) { return { error: e.message }; }
  render() {
    if (this.state.error) {
      return (
        <div className="py-12 px-4 text-center">
          <div className="inline-flex items-center gap-3 p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300 text-sm max-w-lg">
            <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
            </svg>
            <span>Render error: {this.state.error}</span>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
import { fetchUserHistory, fetchUserPatterns } from '../lib/api';
import type { HistoryItem, PatternItem } from '../lib/api';
import Playground from '../components/playground/Playground';

// ── Score badge ────────────────────────────────────────────────────────────────

function ScoreBadge({ score }: { score: number }) {
  const color =
    score >= 80 ? 'text-green-300 bg-green-500/10 border-green-500/30'
    : score >= 50 ? 'text-amber-300 bg-amber-500/10 border-amber-500/30'
    : 'text-red-300 bg-red-500/10 border-red-500/30';
  return (
    <span className={`px-2 py-0.5 rounded-md border text-xs font-mono font-semibold ${color}`}>
      {score}
    </span>
  );
}

// ── Status badge ───────────────────────────────────────────────────────────────

function StatusBadge({ status }: { status: string }) {
  // Normalise: backend may store 'good' (older saves) or 'secure' (LLM output)
  const normalised = status === 'good' ? 'secure' : status;
  const map: Record<string, { cls: string; label: string }> = {
    secure:   { cls: 'text-green-300 bg-green-500/10 border-green-500/30',   label: 'Secure' },
    warning:  { cls: 'text-amber-300 bg-amber-500/10 border-amber-500/30',   label: 'Warning' },
    critical: { cls: 'text-red-300 bg-red-500/10 border-red-500/30',         label: 'Critical' },
  };
  const entry = map[normalised] ?? { cls: 'text-slate-300 bg-slate-500/10 border-slate-500/30', label: normalised };
  return (
    <span className={`px-2 py-0.5 rounded-md border text-xs font-mono font-semibold ${entry.cls}`}>
      {entry.label}
    </span>
  );
}

// ── History tab ────────────────────────────────────────────────────────────────

function HistoryTab({
  token,
}: {
  token: string;
}) {
  const [items, setItems] = useState<HistoryItem[]>([]);
  const [patterns, setPatterns] = useState<PatternItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setLoading(true);
    Promise.all([fetchUserHistory(token), fetchUserPatterns(token)])
      .then(([history, pats]) => {
        setItems(history);
        setPatterns(pats);
        setLoading(false);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : 'Failed to load history.');
        setLoading(false);
      });
  }, [token]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24 gap-3 text-slate-500">
        <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
        <span className="text-sm font-mono">Loading your history…</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="py-12 px-4 text-center">
        <div className="inline-flex items-center gap-3 p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300 text-sm">
          <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
          </svg>
          {error}
        </div>
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center gap-4 py-24 text-center">
        <div className="w-16 h-16 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center">
          <svg className="w-7 h-7 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <div>
          <p className="text-slate-300 font-semibold">No analyses yet</p>
          <p className="text-slate-500 text-sm mt-1">
            Switch to the Playground tab and run your first AI analysis.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto px-4 py-8 space-y-6">
      {/* Patterns row */}
      {patterns.length > 0 && (
        <div className="bg-slate-900 rounded-2xl border border-slate-800 p-5">
          <p className="text-slate-500 text-xs font-mono uppercase tracking-wider mb-4">
            Your Recurring Issues
          </p>
          <div className="flex flex-wrap gap-2">
            {patterns.map((p, i) => (
              <span
                key={i}
                className="px-3 py-1.5 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-xs font-mono"
              >
                {p.label || p.category} <span className="text-indigo-500">×{p.count}</span>
              </span>
            ))}
          </div>
        </div>
      )}

      {/* History list */}
      <div className="space-y-2">
        <p className="text-slate-500 text-xs font-mono uppercase tracking-wider px-1">
          Recent Analyses ({items.length})
        </p>
        {/* Plain div wrapper — no nested AnimatePresence to avoid framer-motion v12 context crashes */}
        <div className="space-y-2">
          {items.map((item, i) => (
            <motion.div
              key={item.id || `item-${i}`}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.2, delay: i * 0.04 }}
              className="flex items-center gap-4 p-4 rounded-xl bg-slate-900/50 border border-slate-800 hover:bg-slate-800/50 transition-colors"
            >
              {/* Config type icon */}
              <div className="w-9 h-9 rounded-lg bg-slate-800 border border-slate-700 flex items-center justify-center flex-shrink-0 text-base">
                {item.configType?.toLowerCase().includes('kubernetes') || item.configType?.toLowerCase().includes('k8s') ? '☸' : '🐳'}
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap mb-1">
                  <code className="text-slate-200 text-sm font-mono truncate">{item.filename || 'config'}</code>
                  <StatusBadge status={item.status} />
                </div>
                <div className="flex items-center gap-2 text-xs text-slate-500 font-mono">
                  <span>{item.configType || 'unknown'}</span>
                  <span>·</span>
                  <span>{new Date(item.createdAt).toLocaleString()}</span>
                  {item.issueCount > 0 && (
                    <>
                      <span>·</span>
                      <span className="text-amber-500">{item.issueCount} issue{item.issueCount !== 1 ? 's' : ''}</span>
                    </>
                  )}
                </div>
                {item.summary && (
                  <p className="text-slate-500 text-xs mt-1 truncate">{item.summary}</p>
                )}
              </div>

              <ScoreBadge score={item.score} />
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ── User menu ──────────────────────────────────────────────────────────────────

function UserMenu({ onLogout }: { onLogout: () => void }) {
  const { user } = useAuth();
  const [open, setOpen] = useState(false);

  if (!user) return null;

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(o => !o)}
        className="flex items-center gap-2 px-3 py-2 rounded-xl bg-slate-800/60 border border-slate-700 hover:border-slate-600 transition-all"
      >
        {user.avatarUrl ? (
          <img src={user.avatarUrl} alt={user.name} className="w-6 h-6 rounded-full" />
        ) : (
          <div className="w-6 h-6 rounded-full bg-indigo-500/40 border border-indigo-500/50 flex items-center justify-center text-xs font-bold text-indigo-200">
            {user.name?.[0]?.toUpperCase() ?? '?'}
          </div>
        )}
        <span className="text-slate-200 text-sm font-medium hidden sm:block max-w-[120px] truncate">
          {user.name}
        </span>
        <svg className={`w-3.5 h-3.5 text-slate-400 transition-transform ${open ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      <AnimatePresence>
        {open && (
          <>
            <div className="fixed inset-0 z-30" onClick={() => setOpen(false)} />
            <motion.div
              initial={{ opacity: 0, y: -8, scale: 0.97 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -8, scale: 0.97 }}
              transition={{ duration: 0.15 }}
              className="absolute right-0 mt-2 w-52 z-40 rounded-xl bg-slate-900 border border-slate-700/60 shadow-2xl overflow-hidden"
            >
              <div className="px-4 py-3 border-b border-slate-800">
                <p className="text-white text-sm font-medium truncate">{user.name}</p>
                <p className="text-slate-500 text-xs truncate">{user.email}</p>
                <p className="text-slate-600 text-[10px] font-mono mt-0.5 capitalize">{user.provider} account</p>
              </div>
              <div className="p-1.5">
                <button
                  onClick={onLogout}
                  className="w-full flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-sm text-red-400 hover:bg-red-500/10 hover:text-red-300 transition-colors"
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                  </svg>
                  Sign out
                </button>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}

// ── Main page ──────────────────────────────────────────────────────────────────

type Tab = 'playground' | 'history';

export default function AppDashboardPage() {
  const { user, token, logout } = useAuth();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<Tab>('playground');

  const handleLogout = () => {
    logout();
    navigate('/', { replace: true });
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200">
      {/* ── Top bar ──────────────────────────────────────────────────────── */}
      <header className="sticky top-0 z-40 border-b border-slate-800 bg-slate-950/80 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3.5 flex items-center justify-between gap-4">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2 flex-shrink-0">
            <img src="/favicon.svg" className="w-7 h-7" alt="checkDK" />
            <span className="font-bold text-white text-base hidden sm:block">checkDK</span>
          </Link>

          {/* Tabs */}
          <div className="flex items-center gap-1 bg-slate-900 border border-slate-800 rounded-xl p-1">
            {(['playground', 'history'] as Tab[]).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-all ${
                  activeTab === tab
                    ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {tab === 'playground' ? '⚡ Playground' : '📊 History'}
              </button>
            ))}
          </div>

          {/* User menu */}
          <UserMenu onLogout={handleLogout} />
        </div>
      </header>

      {/* ── Content ──────────────────────────────────────────────────────── */}
      <main>
        <AnimatePresence mode="wait">
          {activeTab === 'playground' && (
            <motion.div
              key="playground"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
            >
              {/* Welcome banner */}
              {user && (
                <div className="max-w-7xl mx-auto px-4 sm:px-6 pt-6 pb-2">
                  <div className="flex items-center gap-3 px-4 py-3 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-sm">
                    {user.avatarUrl && (
                      <img src={user.avatarUrl} alt="" className="w-7 h-7 rounded-full flex-shrink-0" />
                    )}
                    <span className="text-indigo-200">
                      Welcome back, <strong>{user.name.split(' ')[0]}</strong>! Full AI-powered analysis is active.
                    </span>
                    <span className="ml-auto text-green-400 text-xs font-mono flex items-center gap-1">
                      <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
                      AI Live
                    </span>
                  </div>
                </div>
              )}
              <Playground />
            </motion.div>
          )}

          {activeTab === 'history' && (
            <motion.div
              key="history"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
            >
              <div className="max-w-7xl mx-auto px-4 sm:px-6 pt-8 pb-4">
                <h2 className="text-2xl font-bold text-white mb-1">Analysis History</h2>
                <p className="text-slate-400 text-sm">
                  Your last 10 analyses run with AI-powered backend.
                </p>
              </div>
              <ErrorBoundary>
                {token && <HistoryTab token={token} />}
              </ErrorBoundary>
            </motion.div>
          )}
        </AnimatePresence>
      </main>
    </div>
  );
}

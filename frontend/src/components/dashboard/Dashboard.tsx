import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  fetchReports, fetchStats,
  formatRelativeTime,
  type AnalysisReport, type DashboardStats, type IssueSeverity
} from "../../lib/mockApi";

// ── Severity styling ──────────────────────────────────────────────────────────

const SEVERITY_STYLE: Record<IssueSeverity, { badge: string; dot: string }> = {
  critical: { badge: 'bg-red-500/15 text-red-300 border-red-500/30', dot: 'bg-red-400' },
  warning: { badge: 'bg-amber-500/15 text-amber-300 border-amber-500/30', dot: 'bg-amber-400' },
  info: { badge: 'bg-blue-500/15 text-blue-300 border-blue-500/30', dot: 'bg-blue-400' },
};

const STATUS_STYLE: Record<string, { badge: string; label: string; icon: string }> = {
  passed: { badge: 'bg-green-500/15 text-green-300 border-green-500/30', label: 'Passed', icon: '✓' },
  warnings: { badge: 'bg-amber-500/15 text-amber-300 border-amber-500/30', label: 'Warnings', icon: '⚠' },
  failed: { badge: 'bg-red-500/15 text-red-300 border-red-500/30', label: 'Failed', icon: '✗' },
};

// ── StatCard ──────────────────────────────────────────────────────────────────

function StatCard({ label, value, sub, color = 'text-white' }: {
  label: string; value: string | number; sub?: string; color?: string;
}) {
  return (
    <div className="bg-slate-900 rounded-2xl border border-slate-800 p-5">
      <p className="text-slate-500 text-xs font-mono uppercase tracking-wider mb-2">{label}</p>
      <p className={`text-3xl font-bold tabular-nums ${color}`}>{value}</p>
      {sub && <p className="text-slate-600 text-xs mt-1">{sub}</p>}
    </div>
  );
}

// ── Mini bar chart ────────────────────────────────────────────────────────────

function ActivityChart({ data }: { data: { date: string; count: number }[] }) {
  const max = Math.max(...data.map(d => d.count), 1);
  return (
    <div className="bg-slate-900 rounded-2xl border border-slate-800 p-5">
      <p className="text-slate-500 text-xs font-mono uppercase tracking-wider mb-4">Runs per Day</p>
      <div className="flex items-end gap-1.5 h-16">
        {data.map((d, i) => (
          <div key={i} className="flex-1 flex flex-col items-center gap-1 group">
            <div
              className="w-full bg-indigo-500/40 hover:bg-indigo-500/70 rounded-sm transition-colors relative"
              style={{ height: `${(d.count / max) * 100}%`, minHeight: 4 }}
              title={`${d.count} runs`}
            />
            <span className="text-slate-600 text-[9px] font-mono">{d.date}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Error frequency ───────────────────────────────────────────────────────────

function ErrorFrequency({ data }: { data: { type: string; count: number }[] }) {
  const max = Math.max(...data.map(d => d.count), 1);
  const LABELS: Record<string, string> = {
    port_conflict: 'Port conflict',
    no_resource_limits: 'No resource limits',
    missing_healthcheck: 'Missing healthcheck',
    latest_image_tag: 'Latest tag',
    hardcoded_secret: 'Hardcoded secret',
    missing_probes: 'Missing probes',
  };

  return (
    <div className="bg-slate-900 rounded-2xl border border-slate-800 p-5">
      <p className="text-slate-500 text-xs font-mono uppercase tracking-wider mb-4">Top Issues</p>
      <div className="space-y-3">
        {data.map((item, i) => (
          <div key={i} className="flex items-center gap-3">
            <span className="text-slate-400 text-xs w-32 flex-shrink-0 truncate">{LABELS[item.type] || item.type}</span>
            <div className="flex-1 h-1.5 bg-slate-800 rounded-full overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${(item.count / max) * 100}%` }}
                transition={{ delay: i * 0.08, duration: 0.5 }}
                className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full"
              />
            </div>
            <span className="text-slate-500 text-xs font-mono w-4 text-right">{item.count}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── ReportRow ─────────────────────────────────────────────────────────────────

function ReportRow({ report, onClick, selected }: {
  report: AnalysisReport;
  onClick: () => void;
  selected: boolean;
}) {
  const ss = STATUS_STYLE[report.status];
  const criticalCount = report.errors.filter(e => e.severity === 'critical').length;
  const warnCount = report.errors.filter(e => e.severity === 'warning').length;

  return (
    <button
      onClick={onClick}
      className={`w-full flex items-start gap-4 p-4 rounded-xl text-left transition-all border ${
        selected
          ? 'bg-indigo-500/10 border-indigo-500/30'
          : 'bg-slate-900/50 border-slate-800 hover:bg-slate-800/50 hover:border-slate-700'
      }`}
    >
      {/* Config type icon */}
      <div className="w-9 h-9 rounded-lg bg-slate-800 border border-slate-700 flex items-center justify-center flex-shrink-0 text-base">
        {report.configType === 'docker-compose' ? '🐳' : '☸'}
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1 flex-wrap">
          <code className="text-slate-200 text-sm font-mono font-medium truncate">
            {report.command}
          </code>
          <span className={`px-2 py-0.5 rounded-md border text-[10px] font-mono font-semibold flex-shrink-0 ${ss.badge}`}>
            {ss.icon} {ss.label}
          </span>
        </div>
        <div className="flex items-center gap-2 text-xs text-slate-500">
          <span>{report.files.join(', ')}</span>
          <span>·</span>
          <span>{formatRelativeTime(report.timestamp)}</span>
          <span>·</span>
          <span>{report.executionTimeMs}ms</span>
        </div>
      </div>

      {/* Issue counts */}
      {report.errors.length > 0 && (
        <div className="flex items-center gap-1.5 flex-shrink-0">
          {criticalCount > 0 && (
            <span className="px-2 py-0.5 rounded bg-red-500/15 border border-red-500/30 text-red-300 text-[10px] font-mono">
              {criticalCount} crit
            </span>
          )}
          {warnCount > 0 && (
            <span className="px-2 py-0.5 rounded bg-amber-500/15 border border-amber-500/30 text-amber-300 text-[10px] font-mono">
              {warnCount} warn
            </span>
          )}
        </div>
      )}
    </button>
  );
}

// ── ReportDetail ──────────────────────────────────────────────────────────────

function ReportDetail({ report, onClose }: { report: AnalysisReport; onClose: () => void }) {
  const ss = STATUS_STYLE[report.status];
  const [copiedFix, setCopiedFix] = useState<number | null>(null);

  const copyFix = (fix: string, i: number) => {
    navigator.clipboard.writeText(fix);
    setCopiedFix(i);
    setTimeout(() => setCopiedFix(null), 2000);
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 20 }}
      className="bg-slate-900 rounded-2xl border border-slate-800 overflow-hidden flex flex-col h-full"
    >
      {/* Header */}
      <div className="flex items-start gap-3 p-5 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            <code className="text-white font-mono text-sm font-medium">{report.command}</code>
            <span className={`px-2 py-0.5 rounded-md border text-[10px] font-mono font-semibold ${ss.badge}`}>
              {ss.icon} {ss.label}
            </span>
          </div>
          <p className="text-slate-500 text-xs font-mono">
            {report.files.join(', ')} · {new Date(report.timestamp).toLocaleString()} · {report.executionTimeMs}ms
          </p>
        </div>
        <button
          onClick={onClose}
          className="ml-auto p-1.5 rounded-lg hover:bg-slate-800 text-slate-500 hover:text-slate-300 transition-colors flex-shrink-0"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {/* Issues */}
      <div className="flex-1 overflow-y-auto p-5 space-y-4">
        {report.errors.length === 0 ? (
          <div className="flex flex-col items-center justify-center gap-3 py-12 text-center">
            <div className="w-12 h-12 rounded-xl bg-green-500/20 border border-green-500/30 flex items-center justify-center">
              <svg className="w-6 h-6 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <p className="text-green-400 font-medium">Clean run — no issues detected</p>
          </div>
        ) : (
          report.errors.map((issue, i) => {
            const sc = SEVERITY_STYLE[issue.severity];
            return (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.06 }}
                className={`rounded-xl border p-4 space-y-3 ${sc.badge.replace('text-', 'border-').replace('bg-', '').split(' ')[0]} bg-slate-950/50`}
                style={{ borderColor: undefined }}
              >
                <div className="flex items-start gap-3">
                  <span className={`w-2 h-2 rounded-full mt-1.5 flex-shrink-0 ${sc.dot}`} />
                  <div className="flex-1">
                    <div className="flex items-center gap-2 flex-wrap mb-1">
                      <span className={`text-xs font-mono font-bold px-2 py-0.5 rounded border ${sc.badge}`}>
                        {issue.severity.toUpperCase()}
                      </span>
                      {issue.line && (
                        <span className="text-slate-500 text-xs font-mono">Line {issue.line}</span>
                      )}
                      <span className="text-slate-600 text-xs font-mono">{issue.file}</span>
                    </div>
                    <p className="text-slate-100 font-medium text-sm">{issue.message}</p>
                  </div>
                </div>

                <div className="ml-5 space-y-3">
                  <div>
                    <p className="text-[10px] font-mono text-slate-500 uppercase tracking-wider mb-1">Explanation</p>
                    <p className="text-slate-300 text-sm leading-relaxed">{issue.explanation}</p>
                  </div>

                  {issue.fix && (
                    <div>
                      <div className="flex items-center justify-between mb-1">
                        <p className="text-[10px] font-mono text-slate-500 uppercase tracking-wider">Suggested Fix</p>
                        <button
                          onClick={() => copyFix(issue.fix!, i)}
                          className="text-[10px] font-mono text-indigo-400 hover:text-indigo-300 transition-colors"
                        >
                          {copiedFix === i ? '✓ Copied' : 'Copy'}
                        </button>
                      </div>
                      <div className="bg-slate-900 rounded-lg p-3 border border-slate-800">
                        <p className="text-cyan-300 text-xs font-mono leading-relaxed">{issue.fix}</p>
                      </div>
                    </div>
                  )}
                </div>
              </motion.div>
            );
          })
        )}
      </div>
    </motion.div>
  );
}

// ── Main Dashboard ────────────────────────────────────────────────────────────

const Dashboard = () => {
  const [reports, setReports] = useState<AnalysisReport[]>([]);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedReport, setSelectedReport] = useState<AnalysisReport | null>(null);
  const [filter, setFilter] = useState<'all' | 'passed' | 'warnings' | 'failed'>('all');

  useEffect(() => {
    Promise.all([fetchReports(), fetchStats()]).then(([r, s]) => {
      setReports(r);
      setStats(s);
      setLoading(false);
    });
  }, []);

  const filtered = filter === 'all' ? reports : reports.filter(r => r.status === filter);
  const passRate = stats ? Math.round((stats.passedRuns / stats.totalRuns) * 100) : 0;

  return (
    <section id="dashboard" className="py-24 px-4 sm:px-6 bg-slate-900/50 relative overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-0 right-0 w-96 h-96 bg-purple-500/5 rounded-full blur-[100px]" />
        <div className="absolute bottom-0 left-0 w-96 h-96 bg-indigo-500/5 rounded-full blur-[100px]" />
      </div>

      <div className="max-w-7xl mx-auto relative z-10">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="mb-12 text-center"
        >
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-purple-500/10 border border-purple-500/20 text-purple-300 text-sm font-medium mb-6">
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            Analysis Dashboard
          </div>
          <h2 className="text-4xl sm:text-5xl md:text-6xl font-bold tracking-tight mb-5 bg-clip-text text-transparent bg-gradient-to-r from-white via-purple-200 to-white">
            Your Analysis History
          </h2>
          <p className="text-slate-400 text-lg max-w-xl mx-auto">
            Track trends, spot recurring issues, and measure how much time checkDK has saved you.
          </p>
        </motion.div>

        {loading ? (
          <div className="flex items-center justify-center py-24">
            <div className="flex items-center gap-3 text-slate-500">
              <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Loading dashboard...
            </div>
          </div>
        ) : (
          <>
            {/* Stats row */}
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 mb-6"
            >
              {stats && (
                <>
                  <StatCard label="Total Runs" value={stats.totalRuns} />
                  <StatCard
                    label="Pass Rate"
                    value={`${passRate}%`}
                    color={passRate >= 70 ? 'text-green-400' : passRate >= 50 ? 'text-amber-400' : 'text-red-400'}
                  />
                  <StatCard label="Passed" value={stats.passedRuns} color="text-green-400" />
                  <StatCard label="Warnings" value={stats.warningRuns} color="text-amber-400" />
                  <StatCard label="Failed" value={stats.failedRuns} color="text-red-400" />
                </>
              )}
            </motion.div>

            {/* Charts row */}
            {stats && (
              <motion.div
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-6"
              >
                <ActivityChart data={stats.runsPerDay} />
                <ErrorFrequency data={stats.mostCommonErrors} />
              </motion.div>
            )}

            {/* Reports section */}
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
            >
              {/* Filter tabs */}
              <div className="flex items-center gap-2 mb-4 flex-wrap">
                <span className="text-slate-500 text-sm">Filter:</span>
                {(['all', 'failed', 'warnings', 'passed'] as const).map(f => (
                  <button
                    key={f}
                    onClick={() => { setFilter(f); setSelectedReport(null); }}
                    className={`px-3 py-1.5 rounded-lg text-xs font-mono font-medium transition-all border ${
                      filter === f
                        ? 'bg-indigo-500/20 text-indigo-300 border-indigo-500/30'
                        : 'bg-slate-800/50 text-slate-400 border-slate-700 hover:text-slate-200'
                    }`}
                  >
                    {f === 'all' ? `All (${reports.length})` : `${f.charAt(0).toUpperCase() + f.slice(1)} (${reports.filter(r => r.status === f).length})`}
                  </button>
                ))}
              </div>

              {/* Two-column: list + detail */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                {/* List */}
                <div className="space-y-2">
                  <AnimatePresence>
                    {filtered.map((r, i) => (
                      <motion.div
                        key={r.id}
                        initial={{ opacity: 0, y: 8 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0 }}
                        transition={{ delay: i * 0.05 }}
                      >
                        <ReportRow
                          report={r}
                          onClick={() => setSelectedReport(prev => prev?.id === r.id ? null : r)}
                          selected={selectedReport?.id === r.id}
                        />
                      </motion.div>
                    ))}
                  </AnimatePresence>
                </div>

                {/* Detail panel */}
                <div className="lg:sticky lg:top-24 lg:self-start">
                  <AnimatePresence mode="wait">
                    {selectedReport ? (
                      <ReportDetail
                        key={selectedReport.id}
                        report={selectedReport}
                        onClose={() => setSelectedReport(null)}
                      />
                    ) : (
                      <motion.div
                        key="empty"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="flex flex-col items-center justify-center gap-3 h-64 rounded-2xl border border-slate-800 border-dashed bg-slate-900/30 text-center p-8"
                      >
                        <svg className="w-8 h-8 text-slate-700" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5M7.188 2.239l.777 2.897M5.136 7.965l-2.898-.777M13.95 4.05l-2.122 2.122m-5.657 5.656l-2.12 2.122" />
                        </svg>
                        <p className="text-slate-600 text-sm">Select a report to see full details</p>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              </div>
            </motion.div>

            {/* API integration note */}
            <motion.div
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              viewport={{ once: true }}
              className="mt-8 flex items-center gap-3 p-4 rounded-xl bg-slate-900/50 border border-slate-800 text-sm"
            >
              <div className="w-8 h-8 rounded-lg bg-purple-500/20 border border-purple-500/30 flex items-center justify-center flex-shrink-0">
                <svg className="w-4 h-4 text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <p className="text-slate-400">
                Dashboard data is mocked. When the backend is ready, replace{' '}
                <code className="text-purple-300 bg-purple-500/10 px-1 py-0.5 rounded text-xs">fetchReports()</code>
                {' '}and{' '}
                <code className="text-purple-300 bg-purple-500/10 px-1 py-0.5 rounded text-xs">fetchStats()</code>
                {' '}in <code className="text-purple-300 bg-purple-500/10 px-1 py-0.5 rounded text-xs">lib/mockApi.ts</code> with real{' '}
                <code className="text-purple-300 bg-purple-500/10 px-1 py-0.5 rounded text-xs">fetch()</code> calls.
              </p>
            </motion.div>
          </>
        )}
      </div>
    </section>
  );
};

export default Dashboard;
import { useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { analyzeConfig, SAMPLE_CONFIGS, type AnalysisReport, type Issue, type Severity } from "../../lib/yamlValidator";

// ── Severity helpers ──────────────────────────────────────────────────────────

const SEVERITY_CONFIG: Record<Severity, { label: string; color: string; bg: string; border: string; badge: string }> = {
  critical: {
    label: 'CRITICAL',
    color: 'text-red-400',
    bg: 'bg-red-500/10',
    border: 'border-red-500/30',
    badge: 'bg-red-500/20 text-red-300 border-red-500/30',
  },
  warning: {
    label: 'WARN',
    color: 'text-amber-400',
    bg: 'bg-amber-500/10',
    border: 'border-amber-500/30',
    badge: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
  },
  info: {
    label: 'INFO',
    color: 'text-blue-400',
    bg: 'bg-blue-500/10',
    border: 'border-blue-500/30',
    badge: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
  },
  ok: {
    label: 'OK',
    color: 'text-green-400',
    bg: 'bg-green-500/10',
    border: 'border-green-500/30',
    badge: 'bg-green-500/20 text-green-300 border-green-500/30',
  },
};

const STEP_STATUS_CONFIG = {
  ok: { icon: '✓', color: 'text-green-400' },
  warn: { icon: '⚠', color: 'text-amber-400' },
  error: { icon: '✗', color: 'text-red-400' },
  info: { icon: '·', color: 'text-blue-400' },
};

const STATUS_SUMMARY = {
  passed: { label: 'All checks passed', color: 'text-green-400', bg: 'bg-green-500/10', border: 'border-green-500/30' },
  warnings: { label: 'Passed with warnings', color: 'text-amber-400', bg: 'bg-amber-500/10', border: 'border-amber-500/30' },
  failed: { label: 'Critical issues found — execution blocked', color: 'text-red-400', bg: 'bg-red-500/10', border: 'border-red-500/30' },
  error: { label: 'Analysis error', color: 'text-red-400', bg: 'bg-red-500/10', border: 'border-red-500/30' },
};

// ── IssueCard ─────────────────────────────────────────────────────────────────

function IssueCard({ issue, index }: { issue: Issue; index: number }) {
  const [expanded, setExpanded] = useState(false);
  const cfg = SEVERITY_CONFIG[issue.severity];

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.06 }}
      className={`rounded-xl border ${cfg.border} ${cfg.bg} overflow-hidden`}
    >
      <button
        onClick={() => setExpanded(e => !e)}
        className="w-full flex items-start gap-3 p-4 text-left hover:bg-white/5 transition-colors"
      >
        <span className={`font-mono text-xs font-bold pt-0.5 flex-shrink-0 px-1.5 py-0.5 rounded border ${cfg.badge}`}>
          {cfg.label}
        </span>
        <div className="flex-1 min-w-0">
          <p className="text-slate-100 font-medium text-sm leading-snug">{issue.message}</p>
          {issue.line && (
            <p className="text-slate-500 text-xs mt-0.5 font-mono">Line {issue.line}</p>
          )}
        </div>
        <motion.span
          animate={{ rotate: expanded ? 180 : 0 }}
          transition={{ duration: 0.2 }}
          className="text-slate-500 flex-shrink-0 mt-0.5"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
          </svg>
        </motion.span>
      </button>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="border-t border-white/5"
          >
            <div className="p-4 space-y-4">
              <div>
                <p className="text-xs text-slate-400 font-mono uppercase tracking-wider mb-1.5">What's wrong</p>
                <p className="text-slate-300 text-sm leading-relaxed">{issue.detail}</p>
              </div>

              {issue.fix && (
                <div>
                  <p className="text-xs text-slate-400 font-mono uppercase tracking-wider mb-1.5">How to fix it</p>
                  <p className="text-slate-300 text-sm leading-relaxed">{issue.fix}</p>
                </div>
              )}

              {issue.fixCode && (
                <div>
                  <p className="text-xs text-slate-400 font-mono uppercase tracking-wider mb-1.5">Code fix</p>
                  <div className="relative group/code">
                    <pre className="bg-slate-950 rounded-lg p-4 text-xs font-mono text-emerald-300 overflow-x-auto leading-relaxed border border-slate-800">
                      {issue.fixCode}
                    </pre>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        navigator.clipboard.writeText(issue.fixCode!);
                      }}
                      className="absolute top-2 right-2 opacity-0 group-hover/code:opacity-100 p-1.5 rounded bg-slate-800 hover:bg-slate-700 transition-all"
                      title="Copy fix"
                    >
                      <svg className="w-3.5 h-3.5 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                      </svg>
                    </button>
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

// ── AnalysisPanel ─────────────────────────────────────────────────────────────

function AnalysisPanel({ report }: { report: AnalysisReport }) {
  const summary = STATUS_SUMMARY[report.status];
  const criticals = report.issues.filter(i => i.severity === 'critical');
  const warnings = report.issues.filter(i => i.severity === 'warning');
  const infos = report.issues.filter(i => i.severity === 'info');

  return (
    <div className="h-full flex flex-col gap-4 overflow-y-auto">
      {/* Terminal-style header */}
      <div className="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden flex-shrink-0">
        {/* Dots */}
        <div className="flex items-center gap-1.5 px-4 py-2.5 border-b border-slate-800 bg-slate-950">
          <span className="w-3 h-3 rounded-full bg-red-500/70" />
          <span className="w-3 h-3 rounded-full bg-amber-500/70" />
          <span className="w-3 h-3 rounded-full bg-green-500/70" />
          <span className="ml-auto text-slate-500 text-xs font-mono">checkdk analysis</span>
        </div>

        {/* Steps log */}
        <div className="p-4 space-y-1.5 font-mono text-xs">
          {report.steps.map((step, i) => {
            const cfg = STEP_STATUS_CONFIG[step.status];
            return (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -4 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.08 }}
                className="flex items-center gap-3"
              >
                <span className={`font-bold w-4 ${cfg.color}`}>{cfg.icon}</span>
                <span className="text-slate-400 w-40 flex-shrink-0">{step.label}</span>
                <span className="text-slate-500 truncate">{step.detail}</span>
              </motion.div>
            );
          })}

          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: report.steps.length * 0.08 + 0.1 }}
            className="pt-2 border-t border-slate-800 flex items-center justify-between"
          >
            <span className={`font-bold ${summary.color}`}>
              {report.status === 'passed' ? '✓' : report.status === 'failed' ? '✗' : '⚠'}{' '}
              {summary.label}
            </span>
            <span className="text-slate-600">{report.executionTimeMs}ms</span>
          </motion.div>
        </div>
      </div>

      {/* Summary badges */}
      <motion.div
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="flex flex-wrap gap-2"
      >
        {[
          { count: criticals.length, label: 'Critical', cfg: SEVERITY_CONFIG.critical },
          { count: warnings.length, label: 'Warnings', cfg: SEVERITY_CONFIG.warning },
          { count: infos.length, label: 'Info', cfg: SEVERITY_CONFIG.info },
        ].map(({ count, label, cfg }) => (
          <span
            key={label}
            className={`px-3 py-1.5 rounded-lg border text-xs font-mono font-semibold ${cfg.badge}`}
          >
            {count} {label}
          </span>
        ))}
        <span className="px-3 py-1.5 rounded-lg border border-slate-700 text-xs font-mono font-semibold text-slate-400 bg-slate-800/50 ml-auto">
          {report.configType === 'docker-compose' ? '🐳 Docker Compose' : report.configType === 'kubernetes' ? '☸ Kubernetes' : '? Unknown'}
        </span>
      </motion.div>

      {/* Issue list */}
      {report.issues.length > 0 ? (
        <div className="space-y-3 flex-1">
          {[...criticals, ...warnings, ...infos].map((issue, i) => (
            <IssueCard key={i} issue={issue} index={i} />
          ))}
        </div>
      ) : (
        <motion.div
          initial={{ opacity: 0, scale: 0.97 }}
          animate={{ opacity: 1, scale: 1 }}
          className="flex-1 flex flex-col items-center justify-center gap-3 text-center py-8"
        >
          <div className="w-14 h-14 rounded-2xl bg-green-500/20 border border-green-500/30 flex items-center justify-center">
            <svg className="w-7 h-7 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <p className="text-green-400 font-semibold">All checks passed!</p>
          <p className="text-slate-500 text-sm">Your configuration looks great. No issues detected.</p>
        </motion.div>
      )}
    </div>
  );
}

// ── Main Playground ───────────────────────────────────────────────────────────

const Playground = () => {
  const [yaml, setYaml] = useState('');
  const [report, setReport] = useState<AnalysisReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'docker-compose' | 'kubernetes' | 'paste'>('paste');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleLoadSample = (type: 'docker-compose' | 'kubernetes') => {
    setYaml(SAMPLE_CONFIGS[type]);
    setReport(null);
    setActiveTab(type);
    setTimeout(() => textareaRef.current?.focus(), 50);
  };

  const handleAnalyze = async () => {
    if (!yaml.trim() || loading) return;
    setLoading(true);
    setReport(null);
    try {
      const result = await analyzeConfig(yaml);
      setReport(result);
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setYaml('');
    setReport(null);
    setActiveTab('paste');
    textareaRef.current?.focus();
  };

  const lineCount = yaml.split('\n').length;

  return (
    <section id="playground" className="py-24 px-4 sm:px-6 bg-slate-950 relative overflow-hidden">
      {/* Background glow */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[400px] bg-indigo-500/5 rounded-full blur-[120px]" />
      </div>

      <div className="max-w-7xl mx-auto relative z-10">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-14"
        >
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-sm font-medium mb-6">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-indigo-500"></span>
            </span>
            Live Playground
          </div>
          <h2 className="text-4xl sm:text-5xl md:text-6xl font-bold tracking-tight mb-5 bg-clip-text text-transparent bg-gradient-to-r from-white via-indigo-200 to-white">
            Try It Right Now
          </h2>
          <p className="text-slate-400 text-lg max-w-2xl mx-auto">
            Paste your Docker Compose or Kubernetes manifest and get an instant full analysis report — just like running <code className="text-indigo-300 bg-indigo-500/10 px-1.5 py-0.5 rounded text-sm">checkdk</code> from your terminal.
          </p>
        </motion.div>

        {/* Two-panel layout */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Left — Editor */}
          <div className="flex flex-col gap-3">
            {/* Sample tabs */}
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-500 font-mono">Load sample:</span>
              {(['docker-compose', 'kubernetes'] as const).map(type => (
                <button
                  key={type}
                  onClick={() => handleLoadSample(type)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-mono font-medium transition-all border ${
                    activeTab === type
                      ? 'bg-indigo-500/20 text-indigo-300 border-indigo-500/30'
                      : 'bg-slate-800/50 text-slate-400 border-slate-700 hover:text-slate-200 hover:border-slate-600'
                  }`}
                >
                  {type === 'docker-compose' ? '🐳 docker-compose' : '☸ kubernetes'}
                </button>
              ))}
              {yaml && (
                <button
                  onClick={handleClear}
                  className="ml-auto px-2.5 py-1.5 rounded-lg text-xs font-mono text-slate-500 hover:text-slate-300 hover:bg-slate-800 transition-all border border-transparent hover:border-slate-700"
                >
                  Clear
                </button>
              )}
            </div>

            {/* Editor window */}
            <div className="relative rounded-xl bg-slate-900 border border-slate-700/60 overflow-hidden flex-1 min-h-[420px] flex flex-col">
              {/* Window chrome */}
              <div className="flex items-center gap-1.5 px-4 py-2.5 border-b border-slate-800 bg-slate-950 flex-shrink-0">
                <span className="w-3 h-3 rounded-full bg-red-500/70" />
                <span className="w-3 h-3 rounded-full bg-amber-500/70" />
                <span className="w-3 h-3 rounded-full bg-green-500/70" />
                <span className="ml-3 text-slate-500 text-xs font-mono">
                  {activeTab === 'paste' ? 'untitled.yml' : activeTab === 'docker-compose' ? 'docker-compose.yml' : 'k8s-manifest.yaml'}
                </span>
                {yaml && (
                  <span className="ml-auto text-slate-600 text-xs font-mono">{lineCount} lines</span>
                )}
              </div>

              {/* Editor area with line numbers */}
              <div className="flex flex-1 overflow-hidden">
                {/* Line numbers */}
                <div className="flex-shrink-0 w-10 bg-slate-950/50 border-r border-slate-800 pt-4 pb-4 px-2 overflow-hidden select-none">
                  {Array.from({ length: Math.max(lineCount, 20) }, (_, i) => (
                    <div key={i} className="text-slate-700 text-xs font-mono leading-6 text-right">
                      {i + 1}
                    </div>
                  ))}
                </div>

                {/* Textarea */}
                <textarea
                  ref={textareaRef}
                  value={yaml}
                  onChange={e => { setYaml(e.target.value); setReport(null); }}
                  onKeyDown={e => {
                    // Tab key inserts 2 spaces instead of changing focus
                    if (e.key === 'Tab') {
                      e.preventDefault();
                      const start = e.currentTarget.selectionStart;
                      const end = e.currentTarget.selectionEnd;
                      const newVal = yaml.substring(0, start) + '  ' + yaml.substring(end);
                      setYaml(newVal);
                      setTimeout(() => {
                        if (textareaRef.current) {
                          textareaRef.current.selectionStart = start + 2;
                          textareaRef.current.selectionEnd = start + 2;
                        }
                      }, 0);
                    }
                  }}
                  placeholder={`# Paste your docker-compose.yml or Kubernetes manifest here\n# or load a sample above ↑\n\nversion: "3.9"\nservices:\n  web:\n    image: nginx:latest\n    ports:\n      - "80:80"`}
                  className="flex-1 bg-transparent text-slate-200 font-mono text-sm leading-6 resize-none outline-none p-4 placeholder:text-slate-700"
                  spellCheck={false}
                  autoComplete="off"
                  autoCorrect="off"
                />
              </div>
            </div>

            {/* Analyze button */}
            <button
              onClick={handleAnalyze}
              disabled={!yaml.trim() || loading}
              className={`relative w-full py-3.5 rounded-xl font-semibold text-sm transition-all duration-300 overflow-hidden group ${
                yaml.trim() && !loading
                  ? 'bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white shadow-lg shadow-indigo-500/25 hover:shadow-indigo-500/40'
                  : 'bg-slate-800 text-slate-500 cursor-not-allowed'
              }`}
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  Analyzing configuration...
                </span>
              ) : (
                <span className="flex items-center justify-center gap-2">
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                  Run checkdk Analysis
                </span>
              )}

              {/* Shimmer on hover */}
              {yaml.trim() && !loading && (
                <div className="absolute inset-0 -translate-x-full group-hover:translate-x-full transition-transform duration-700 bg-gradient-to-r from-transparent via-white/10 to-transparent" />
              )}
            </button>
          </div>

          {/* Right — Results */}
          <div className="min-h-[540px] lg:min-h-0">
            <AnimatePresence mode="wait">
              {!report && !loading && (
                <motion.div
                  key="empty"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="h-full min-h-[420px] flex flex-col items-center justify-center gap-4 rounded-xl border border-slate-800 border-dashed bg-slate-900/30 text-center p-8"
                >
                  <div className="w-16 h-16 rounded-2xl bg-slate-800 border border-slate-700 flex items-center justify-center">
                    <svg className="w-8 h-8 text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  <div>
                    <p className="text-slate-500 font-medium">Analysis results will appear here</p>
                    <p className="text-slate-600 text-sm mt-1">Paste a config and click "Run checkdk Analysis"</p>
                  </div>
                </motion.div>
              )}

              {loading && (
                <motion.div
                  key="loading"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="h-full min-h-[420px] flex flex-col items-center justify-center gap-5 rounded-xl border border-slate-800 bg-slate-900/30"
                >
                  {/* Animated terminal lines */}
                  <div className="w-72 space-y-2.5 font-mono text-xs">
                    {[
                      { text: 'Parsing YAML structure...', delay: 0 },
                      { text: 'Detecting config type...', delay: 0.2 },
                      { text: 'Running validators...', delay: 0.5 },
                      { text: 'Scanning for secrets...', delay: 0.8 },
                      { text: 'Generating AI suggestions...', delay: 1.1 },
                    ].map((item, i) => (
                      <motion.div
                        key={i}
                        initial={{ opacity: 0, x: -8 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: item.delay }}
                        className="flex items-center gap-2 text-slate-500"
                      >
                        <motion.span
                          animate={{ opacity: [1, 0.3, 1] }}
                          transition={{ repeat: Infinity, duration: 1.2, delay: item.delay }}
                          className="text-indigo-400"
                        >
                          ›
                        </motion.span>
                        {item.text}
                      </motion.div>
                    ))}
                  </div>
                </motion.div>
              )}

              {report && !loading && (
                <motion.div
                  key="results"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  className="h-full"
                >
                  <AnalysisPanel report={report} />
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>

        {/* "Connect to real API" callout */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="mt-8 flex items-center gap-3 p-4 rounded-xl bg-slate-900/50 border border-slate-800 text-sm"
        >
          <div className="w-8 h-8 rounded-lg bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center flex-shrink-0">
            <svg className="w-4 h-4 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <p className="text-slate-400">
            This playground runs client-side validation. When the backend API is ready, swap{' '}
            <code className="text-indigo-300 bg-indigo-500/10 px-1 py-0.5 rounded text-xs">analyzeConfig()</code>
            {' '}in{' '}
            <code className="text-indigo-300 bg-indigo-500/10 px-1 py-0.5 rounded text-xs">lib/yamlValidator.ts</code>
            {' '}to hit <code className="text-indigo-300 bg-indigo-500/10 px-1 py-0.5 rounded text-xs">POST /api/analyze</code> for full AI-powered analysis.
          </p>
        </motion.div>
      </div>
    </section>
  );
};

export default Playground;
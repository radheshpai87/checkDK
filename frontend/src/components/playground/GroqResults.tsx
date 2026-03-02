import React, { useState } from 'react';
import {
  CheckCircle,
  AlertTriangle,
  XCircle,
  Info,
  Shield,
  TrendingUp,
  Lightbulb,
  ChevronDown,
} from 'lucide-react';
import type { GroqAnalysisResult, GroqIssue, IssueSeverity } from '../../services/groqAnalysis';

// ── Configs ────────────────────────────────────────────────────────────────────

const SEVERITY_CFG: Record<
  IssueSeverity,
  { label: string; color: string; bg: string; border: string; badge: string; Icon: React.ElementType }
> = {
  critical: {
    label: 'Critical',
    color: 'text-red-400',
    bg: 'bg-red-500/10',
    border: 'border-red-500/30',
    badge: 'bg-red-500/20 text-red-300 border border-red-500/40',
    Icon: XCircle,
  },
  high: {
    label: 'High',
    color: 'text-orange-400',
    bg: 'bg-orange-500/10',
    border: 'border-orange-500/30',
    badge: 'bg-orange-500/20 text-orange-300 border border-orange-500/40',
    Icon: AlertTriangle,
  },
  medium: {
    label: 'Medium',
    color: 'text-yellow-400',
    bg: 'bg-yellow-500/10',
    border: 'border-yellow-500/30',
    badge: 'bg-yellow-500/20 text-yellow-300 border border-yellow-500/40',
    Icon: AlertTriangle,
  },
  low: {
    label: 'Low',
    color: 'text-blue-400',
    bg: 'bg-blue-500/10',
    border: 'border-blue-500/30',
    badge: 'bg-blue-500/20 text-blue-300 border border-blue-500/40',
    Icon: Info,
  },
  info: {
    label: 'Info',
    color: 'text-slate-400',
    bg: 'bg-slate-700/30',
    border: 'border-slate-600/40',
    badge: 'bg-slate-600/30 text-slate-300 border border-slate-600/40',
    Icon: Info,
  },
};

const STATUS_CFG = {
  secure: {
    Icon: CheckCircle,
    color: 'text-emerald-400',
    bg: 'bg-emerald-500/10',
    border: 'border-emerald-500/30',
    label: 'Secure',
    scoreColor: '#34d399',
    ringBg: 'rgba(52,211,153,0.12)',
  },
  warning: {
    Icon: AlertTriangle,
    color: 'text-yellow-400',
    bg: 'bg-yellow-500/10',
    border: 'border-yellow-500/30',
    label: 'Warning',
    scoreColor: '#fbbf24',
    ringBg: 'rgba(251,191,36,0.12)',
  },
  critical: {
    Icon: XCircle,
    color: 'text-red-400',
    bg: 'bg-red-500/10',
    border: 'border-red-500/30',
    label: 'Critical Issues Found',
    scoreColor: '#f87171',
    ringBg: 'rgba(248,113,113,0.12)',
  },
};

// ── IssueCard ──────────────────────────────────────────────────────────────────

function IssueCard({ issue, index }: { issue: GroqIssue; index: number }) {
  const [open, setOpen] = useState(index === 0);
  const cfg = SEVERITY_CFG[issue.severity] ?? SEVERITY_CFG.info;
  const { Icon } = cfg;

  return (
    <div className={`rounded-xl border ${cfg.border} ${cfg.bg} overflow-hidden`}>
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-start gap-3 p-4 text-left hover:bg-white/5 transition-colors"
      >
        <Icon className={`w-4 h-4 mt-0.5 flex-shrink-0 ${cfg.color}`} />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm font-semibold text-slate-100">{issue.title}</span>
            <span className={`text-xs px-2 py-0.5 rounded-full ${cfg.badge}`}>{cfg.label}</span>
            {issue.line != null && (
              <span className="text-xs text-slate-500 font-mono">Line {issue.line}</span>
            )}
          </div>
          {!open && (
            <p className="text-xs text-slate-500 mt-0.5 truncate">{issue.description}</p>
          )}
        </div>
        <ChevronDown
          className={`w-4 h-4 text-slate-500 flex-shrink-0 mt-0.5 transition-transform duration-200 ${open ? 'rotate-180' : ''}`}
        />
      </button>

      {open && (
        <div className="px-4 pb-4 space-y-3 border-t border-white/5 pt-3">
          <p className="text-sm text-slate-300 leading-relaxed">{issue.description}</p>
          <div className="flex items-start gap-2 bg-slate-900/50 rounded-lg p-3">
            <Lightbulb className="w-3.5 h-3.5 text-amber-400 mt-0.5 flex-shrink-0" />
            <p className="text-xs text-slate-300 leading-relaxed">
              <span className="text-amber-400 font-semibold">Fix: </span>
              {issue.recommendation}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

// ── GroqResults ────────────────────────────────────────────────────────────────

interface GroqResultsProps {
  result: GroqAnalysisResult;
  filename?: string;
}

export const GroqResults: React.FC<GroqResultsProps> = ({ result, filename }) => {
  const status = STATUS_CFG[result.status] ?? STATUS_CFG.warning;
  const { Icon: StatusIcon } = status;

  // SVG ring
  const RADIUS = 48;
  const CIRC = 2 * Math.PI * RADIUS;
  const offset = CIRC - (Math.min(100, Math.max(0, result.score)) / 100) * CIRC;

  const counts = {
    critical: result.issues.filter((i) => i.severity === 'critical').length,
    high:     result.issues.filter((i) => i.severity === 'high').length,
    medium:   result.issues.filter((i) => i.severity === 'medium').length,
    low:      result.issues.filter((i) => i.severity === 'low').length,
  };

  // Sort issues by severity priority
  const PRIORITY: Record<IssueSeverity, number> = { critical: 0, high: 1, medium: 2, low: 3, info: 4 };
  const sorted = [...result.issues].sort((a, b) => PRIORITY[a.severity] - PRIORITY[b.severity]);

  return (
    <div className="space-y-5">
      {/* ── Score + summary ─────────────────────────────────────────────────── */}
      <div className={`rounded-2xl border ${status.border} ${status.bg} p-5 flex flex-col sm:flex-row items-center gap-5`}>
        {/* Score ring */}
        <div className="relative flex-shrink-0">
          <svg width="120" height="120" className="-rotate-90">
            <circle cx="60" cy="60" r={RADIUS} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="9" />
            <circle
              cx="60" cy="60" r={RADIUS} fill="none"
              stroke={status.scoreColor} strokeWidth="9"
              strokeDasharray={CIRC} strokeDashoffset={offset}
              strokeLinecap="round"
              style={{ transition: 'stroke-dashoffset 1.2s cubic-bezier(.4,0,.2,1)' }}
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-3xl font-bold" style={{ color: status.scoreColor }}>
              {result.score}
            </span>
            <span className="text-[10px] text-slate-400 font-medium tracking-wide">/100</span>
          </div>
        </div>

        {/* Text */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1.5 flex-wrap">
            <StatusIcon className={`w-4 h-4 ${status.color}`} />
            <span className={`font-bold ${status.color}`}>{status.label}</span>
            {filename && (
              <span className="text-xs text-slate-500 truncate">— {filename}</span>
            )}
          </div>
          <p className="text-sm text-slate-300 leading-relaxed">{result.summary}</p>

          {/* Counts */}
          <div className="flex flex-wrap gap-2 mt-3">
            {counts.critical > 0 && (
              <span className="text-xs px-2 py-0.5 rounded-full bg-red-500/20 text-red-300 border border-red-500/30">
                {counts.critical} Critical
              </span>
            )}
            {counts.high > 0 && (
              <span className="text-xs px-2 py-0.5 rounded-full bg-orange-500/20 text-orange-300 border border-orange-500/30">
                {counts.high} High
              </span>
            )}
            {counts.medium > 0 && (
              <span className="text-xs px-2 py-0.5 rounded-full bg-yellow-500/20 text-yellow-300 border border-yellow-500/30">
                {counts.medium} Medium
              </span>
            )}
            {counts.low > 0 && (
              <span className="text-xs px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-300 border border-blue-500/30">
                {counts.low} Low
              </span>
            )}
            {result.issues.length === 0 && (
              <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                No issues found
              </span>
            )}
          </div>
        </div>
      </div>

      {/* ── Highlights ──────────────────────────────────────────────────────── */}
      {result.highlights?.length > 0 && (
        <div className="rounded-xl border border-slate-700/50 bg-slate-800/40 p-4">
          <div className="flex items-center gap-2 mb-3">
            <TrendingUp className="w-4 h-4 text-violet-400" />
            <h3 className="text-sm font-semibold text-slate-200">Key Highlights</h3>
          </div>
          <ul className="space-y-2">
            {result.highlights.map((h, i) => (
              <li key={i} className="flex items-start gap-2">
                {h.type === 'good'
                  ? <CheckCircle className="w-4 h-4 text-emerald-400 mt-0.5 flex-shrink-0" />
                  : h.type === 'bad'
                    ? <XCircle className="w-4 h-4 text-red-400 mt-0.5 flex-shrink-0" />
                    : <Info className="w-4 h-4 text-slate-400 mt-0.5 flex-shrink-0" />
                }
                <span className="text-sm text-slate-300">{h.text}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* ── Findings ────────────────────────────────────────────────────────── */}
      {sorted.length > 0 && (
        <div className="space-y-2.5">
          <div className="flex items-center gap-2">
            <Shield className="w-4 h-4 text-violet-400" />
            <h3 className="text-sm font-semibold text-slate-200">
              Findings ({sorted.length})
            </h3>
          </div>
          {sorted.map((issue, i) => (
            <IssueCard key={i} issue={issue} index={i} />
          ))}
        </div>
      )}

      <p className="text-center text-xs text-slate-600 pt-1">
        Powered by{' '}
        <span className="text-violet-500 font-medium">CheckDK</span>
      </p>
    </div>
  );
};

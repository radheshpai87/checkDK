// ─────────────────────────────────────────────────────────────────────────────
// lib/mockAnalyzer.ts
// Lightweight client-side rule-based analyzer used when the user is not
// authenticated. No network requests — runs entirely in the browser.
// Returns the same AnalysisResult shape as the backend playground endpoint.
// ─────────────────────────────────────────────────────────────────────────────

import type { AnalysisResult, AnalysisIssue } from '../services/aiAnalysis';

interface Rule {
  test: (content: string) => boolean;
  issue: AnalysisIssue;
}

const RULES: Rule[] = [
  {
    test: (c) => /:latest/.test(c) || (/image:\s*\S+$/.test(c) && !/:/.test(c.match(/image:\s*(\S+)/)?.[1] ?? ':')),
    issue: {
      severity: 'medium',
      title: 'Unpinned image tag',
      description: 'One or more images use ":latest" or no tag, making builds non-reproducible.',
      recommendation: 'Pin a specific version, e.g. nginx:1.25.3',
      category: 'image_tag',
    },
  },
  {
    test: (c) => /privileged:\s*true/.test(c),
    issue: {
      severity: 'high',
      title: 'Privileged container',
      description: 'A container runs in privileged mode, granting full host access.',
      recommendation: 'Remove "privileged: true" and use specific capabilities instead.',
      category: 'security',
    },
  },
  {
    test: (c) => /(password|secret|api_key|token)\s*=\s*\S+/i.test(c),
    issue: {
      severity: 'high',
      title: 'Possible hardcoded secret',
      description: 'A secret or API key may be hardcoded in the config.',
      recommendation: 'Use environment variable references or a secrets manager.',
      category: 'hardcoded_secret',
    },
  },
  {
    test: (c) => /services:/.test(c) && !/resources:/.test(c),
    issue: {
      severity: 'medium',
      title: 'No resource limits',
      description: 'Services have no CPU/memory limits defined.',
      recommendation: 'Add deploy.resources.limits with cpus and memory.',
      category: 'resource_limits',
    },
  },
  {
    test: (c) => /kind:\s*Deployment/.test(c) && !/livenessProbe|readinessProbe/.test(c),
    issue: {
      severity: 'medium',
      title: 'Missing liveness/readiness probes',
      description: 'Kubernetes Deployment has no liveness or readiness probes.',
      recommendation: 'Add livenessProbe and readinessProbe to your container spec.',
      category: 'probe',
    },
  },
  {
    test: (c) => /kind:\s*Deployment/.test(c) && !/resources:/.test(c),
    issue: {
      severity: 'medium',
      title: 'No resource requests/limits',
      description: 'Kubernetes containers have no CPU or memory requests/limits.',
      recommendation: 'Set resources.requests and resources.limits on each container.',
      category: 'resource_limits',
    },
  },
];

export async function mockAnalyze(
  content: string,
): Promise<AnalysisResult> {
  const issues: AnalysisIssue[] = RULES
    .filter((r) => r.test(content))
    .map((r) => r.issue);

  const criticalCount = issues.filter((i) => i.severity === 'critical').length;
  const highCount = issues.filter((i) => i.severity === 'high').length;
  const mediumCount = issues.filter((i) => i.severity === 'medium').length;

  const penalty = criticalCount * 25 + highCount * 15 + mediumCount * 8;
  const score = Math.max(0, Math.min(100, 100 - penalty));

  const status =
    score >= 80 ? 'secure'
    : score >= 50 ? 'warning'
    : 'critical';

  const summary =
    issues.length === 0
      ? 'No obvious issues detected by the quick scanner. Sign in for a full AI-powered audit.'
      : `Found ${issues.length} issue${issues.length > 1 ? 's' : ''} with the quick scanner. Sign in for a full AI-powered audit.`;

  return {
    score,
    status,
    summary,
    issues,
    highlights: [],
    provider: 'mock',
  };
}

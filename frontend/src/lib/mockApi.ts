// ── Types ─────────────────────────────────────────────────────────────────────

export type IssueSeverity = 'critical' | 'warning' | 'info';

export interface AnalysisIssue {
  severity: IssueSeverity;
  message: string;
  explanation: string;
  fix?: string;
  line?: number;
  file: string;
}

export interface AnalysisReport {
  id: string;
  status: 'passed' | 'warnings' | 'failed';
  configType: 'docker-compose' | 'kubernetes';
  command: string;
  files: string[];
  errors: AnalysisIssue[];
  timestamp: string;
  executionTimeMs: number;
}

export interface DashboardStats {
  totalRuns: number;
  passedRuns: number;
  warningRuns: number;
  failedRuns: number;
  runsPerDay: { date: string; count: number }[];
  mostCommonErrors: { type: string; count: number }[];
}

// ── Helpers ───────────────────────────────────────────────────────────────────

export function formatRelativeTime(timestamp: string): string {
  const diff = Date.now() - new Date(timestamp).getTime();
  const minutes = Math.floor(diff / 60_000);
  if (minutes < 1) return 'just now';
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

// ── Mock data ─────────────────────────────────────────────────────────────────

const MOCK_REPORTS: AnalysisReport[] = [
  {
    id: '1',
    status: 'failed',
    configType: 'docker-compose',
    command: 'checkdk docker compose up -d',
    files: ['docker-compose.yml'],
    timestamp: new Date(Date.now() - 5 * 60_000).toISOString(),
    executionTimeMs: 312,
    errors: [
      {
        severity: 'critical',
        message: 'Port 8080 is bound on multiple services',
        explanation: 'Services "api" and "worker" both attempt to bind host port 8080, which will cause a conflict at runtime.',
        fix: 'Change the worker service to use a different port, e.g. "8081:8080".',
        line: 14,
        file: 'docker-compose.yml',
      },
      {
        severity: 'warning',
        message: 'No resource limits set on service "db"',
        explanation: 'Without CPU and memory limits the database container can consume all host resources and starve other services.',
        fix: 'Add a deploy.resources.limits block with appropriate cpu and memory values.',
        line: 27,
        file: 'docker-compose.yml',
      },
      {
        severity: 'warning',
        message: 'Image tag "latest" used for service "api"',
        explanation: 'Using the "latest" tag makes builds non-reproducible and can cause unexpected breakage on re-pulls.',
        fix: 'Pin to a specific version, e.g. myapp:1.4.2.',
        line: 8,
        file: 'docker-compose.yml',
      },
    ],
  },
  {
    id: '2',
    status: 'warnings',
    configType: 'kubernetes',
    command: 'checkdk kubectl apply -f',
    files: ['k8s-deployment.yml', 'k8s-service.yml'],
    timestamp: new Date(Date.now() - 2 * 3600_000).toISOString(),
    executionTimeMs: 487,
    errors: [
      {
        severity: 'warning',
        message: 'Liveness probe missing on container "backend"',
        explanation: 'Without a liveness probe Kubernetes cannot detect a deadlocked container and will not restart it automatically.',
        fix: 'Add a livenessProbe block targeting the /health endpoint.',
        line: 33,
        file: 'k8s-deployment.yml',
      },
      {
        severity: 'info',
        message: 'Readiness probe interval is very short (2s)',
        explanation: 'A 2 s probe interval increases API-server load; 10–15 s is typical for most workloads.',
        file: 'k8s-deployment.yml',
      },
    ],
  },
  {
    id: '3',
    status: 'passed',
    configType: 'docker-compose',
    command: 'checkdk docker compose up -d',
    files: ['docker-compose.prod.yml'],
    timestamp: new Date(Date.now() - 24 * 3600_000).toISOString(),
    executionTimeMs: 278,
    errors: [],
  },
  {
    id: '4',
    status: 'failed',
    configType: 'kubernetes',
    command: 'checkdk kubectl apply -f',
    files: ['k8s-complex.yml'],
    timestamp: new Date(Date.now() - 2 * 24 * 3600_000).toISOString(),
    executionTimeMs: 601,
    errors: [
      {
        severity: 'critical',
        message: 'Hardcoded secret in environment variable "DB_PASSWORD"',
        explanation: 'Plain-text secrets in manifests are stored unencrypted in the cluster etcd and any git history.',
        fix: 'Use a Kubernetes Secret resource and reference it with secretKeyRef.',
        line: 45,
        file: 'k8s-complex.yml',
      },
      {
        severity: 'warning',
        message: 'No resource requests set — scheduler cannot place pod optimally',
        explanation: 'Without resource requests the Kubernetes scheduler has no signal for bin-packing and may over-commit nodes.',
        fix: 'Add resources.requests.cpu and resources.requests.memory to your container spec.',
        file: 'k8s-complex.yml',
      },
    ],
  },
  {
    id: '5',
    status: 'warnings',
    configType: 'docker-compose',
    command: 'checkdk docker compose up -d',
    files: ['docker-compose.yml'],
    timestamp: new Date(Date.now() - 3 * 24 * 3600_000).toISOString(),
    executionTimeMs: 295,
    errors: [
      {
        severity: 'warning',
        message: 'No healthcheck defined for service "redis"',
        explanation: 'Docker will mark the container healthy immediately after start even if Redis is not yet accepting connections.',
        fix: 'Add a HEALTHCHECK instruction or a healthcheck block using redis-cli ping.',
        file: 'docker-compose.yml',
      },
    ],
  },
  {
    id: '6',
    status: 'passed',
    configType: 'kubernetes',
    command: 'checkdk kubectl apply -f',
    files: ['k8s-deployment.yml'],
    timestamp: new Date(Date.now() - 4 * 24 * 3600_000).toISOString(),
    executionTimeMs: 390,
    errors: [],
  },
];

const MOCK_STATS: DashboardStats = {
  totalRuns: MOCK_REPORTS.length,
  passedRuns: MOCK_REPORTS.filter(r => r.status === 'passed').length,
  warningRuns: MOCK_REPORTS.filter(r => r.status === 'warnings').length,
  failedRuns: MOCK_REPORTS.filter(r => r.status === 'failed').length,
  runsPerDay: [
    { date: 'Mon', count: 3 },
    { date: 'Tue', count: 5 },
    { date: 'Wed', count: 2 },
    { date: 'Thu', count: 7 },
    { date: 'Fri', count: 4 },
    { date: 'Sat', count: 1 },
    { date: 'Sun', count: 6 },
  ],
  mostCommonErrors: [
    { type: 'no_resource_limits', count: 8 },
    { type: 'latest_image_tag', count: 6 },
    { type: 'missing_healthcheck', count: 5 },
    { type: 'port_conflict', count: 3 },
    { type: 'hardcoded_secret', count: 2 },
    { type: 'missing_probes', count: 2 },
  ],
};

// ── API functions (swap for real fetch() calls when backend is ready) ─────────

export async function fetchReports(): Promise<AnalysisReport[]> {
  await new Promise(r => setTimeout(r, 400)); // simulate network latency
  return MOCK_REPORTS;
}

export async function fetchStats(): Promise<DashboardStats> {
  await new Promise(r => setTimeout(r, 250));
  return MOCK_STATS;
}

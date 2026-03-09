// ─────────────────────────────────────────────────────────────────────────────
// components/dashboard/DocsTab.tsx
// Full project documentation — sticky sidebar + scrollable content.
// ─────────────────────────────────────────────────────────────────────────────

import { useState, useEffect, useRef } from 'react';

// ── Reusable copy button ──────────────────────────────────────────────────────
function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      onClick={() => { navigator.clipboard.writeText(text); setCopied(true); setTimeout(() => setCopied(false), 2000); }}
      className="flex-shrink-0 p-1.5 rounded-md bg-slate-700/60 hover:bg-slate-600/60 transition-colors"
      title="Copy"
    >
      {copied ? (
        <svg className="w-3.5 h-3.5 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
        </svg>
      ) : (
        <svg className="w-3.5 h-3.5 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
        </svg>
      )}
    </button>
  );
}

// ── Code block ────────────────────────────────────────────────────────────────
function CodeBlock({ code, lang = 'bash' }: { code: string; lang?: string }) {
  return (
    <div className="relative group/cb my-3 rounded-xl bg-slate-950 border border-slate-800 overflow-hidden">
      <div className="flex items-center justify-between px-4 py-2 border-b border-slate-800/60">
        <span className="text-[10px] font-mono text-slate-500 uppercase tracking-widest">{lang}</span>
        <CopyButton text={code.trim()} />
      </div>
      <pre className="px-4 py-3 overflow-x-auto text-sm">
        <code className="text-cyan-300 font-mono whitespace-pre">{code.trim()}</code>
      </pre>
    </div>
  );
}

// ── Section heading ───────────────────────────────────────────────────────────
function SectionHeading({ id, children }: { id: string; children: React.ReactNode }) {
  return (
    <h2 id={id} className="scroll-mt-24 text-2xl font-bold text-white mb-4 pt-2 flex items-center gap-2 group">
      {children}
      <a href={`#${id}`} className="opacity-0 group-hover:opacity-40 hover:!opacity-80 text-indigo-400 transition-opacity text-lg">#</a>
    </h2>
  );
}

function SubHeading({ id, children }: { id: string; children: React.ReactNode }) {
  return (
    <h3 id={id} className="scroll-mt-24 text-lg font-semibold text-slate-100 mb-3 mt-6">{children}</h3>
  );
}

// ── Badge helper ──────────────────────────────────────────────────────────────
function Badge({ children, color = 'indigo' }: { children: React.ReactNode; color?: 'indigo' | 'green' | 'amber' | 'red' | 'slate' }) {
  const cls: Record<string, string> = {
    indigo: 'bg-indigo-500/15 text-indigo-300 border-indigo-500/30',
    green:  'bg-green-500/15 text-green-300 border-green-500/30',
    amber:  'bg-amber-500/15 text-amber-300 border-amber-500/30',
    red:    'bg-red-500/15 text-red-300 border-red-500/30',
    slate:  'bg-slate-700/40 text-slate-300 border-slate-700/60',
  };
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-md border text-xs font-mono font-medium ${cls[color]}`}>
      {children}
    </span>
  );
}

// ── Callout ───────────────────────────────────────────────────────────────────
function Callout({ type = 'info', children }: { type?: 'info' | 'warn' | 'tip'; children: React.ReactNode }) {
  const styles = {
    info: 'bg-indigo-500/10 border-indigo-500/30 text-indigo-200',
    warn: 'bg-amber-500/10 border-amber-500/30 text-amber-200',
    tip:  'bg-green-500/10 border-green-500/30 text-green-200',
  };
  const icons = {
    info: <path strokeLinecap="round" strokeLinejoin="round" d="M13 16h-1v-4h-1m1-4h.01M12 2a10 10 0 100 20A10 10 0 0012 2z" />,
    warn: <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />,
    tip:  <path strokeLinecap="round" strokeLinejoin="round" d="M12 18v-5.25m0 0a6.01 6.01 0 001.5-.189m-1.5.189a6.01 6.01 0 01-1.5-.189m3.75 7.478a12.06 12.06 0 01-4.5 0m3.75 2.383a14.406 14.406 0 01-3 0M14.25 18v-.192c0-.983.658-1.823 1.508-2.316a7.5 7.5 0 10-7.517 0c.85.493 1.509 1.333 1.509 2.316V18" />,
  };
  return (
    <div className={`flex gap-3 p-4 rounded-xl border my-4 text-sm ${styles[type]}`}>
      <svg className="w-4 h-4 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>{icons[type]}</svg>
      <div>{children}</div>
    </div>
  );
}

// ── Table ─────────────────────────────────────────────────────────────────────
function DocTable({ headers, rows }: { headers: string[]; rows: (string | React.ReactNode)[][] }) {
  return (
    <div className="my-4 overflow-x-auto rounded-xl border border-slate-800">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-slate-800 bg-slate-900/60">
            {headers.map((h, i) => (
              <th key={i} className="px-4 py-2.5 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-800/60">
          {rows.map((row, i) => (
            <tr key={i} className="hover:bg-slate-800/30 transition-colors">
              {row.map((cell, j) => (
                <td key={j} className="px-4 py-2.5 text-slate-300 font-mono text-xs">{cell}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ── Sidebar nav data ──────────────────────────────────────────────────────────
const NAV = [
  { id: 'installation',  label: 'Installation',       icon: '' },
  { id: 'overview',      label: 'Overview',            icon: '' },
  { id: 'features',      label: 'Features',            icon: '' },
  { id: 'cli',           label: 'CLI Reference',       icon: '' },
  { id: 'api',           label: 'API Reference',       icon: '' },
  { id: 'ml',            label: 'ML Prediction',       icon: '' },
  { id: 'architecture',  label: 'Architecture',        icon: '' },
  { id: 'roadmap',       label: 'Roadmap',             icon: '' },
];

// ── Main component ────────────────────────────────────────────────────────────
export default function DocsTab() {
  const [active, setActive] = useState('installation');
  const contentRef = useRef<HTMLDivElement>(null);

  // Track active section via IntersectionObserver
  useEffect(() => {
    const observers: IntersectionObserver[] = [];
    NAV.forEach(({ id }) => {
      const el = document.getElementById(id);
      if (!el) return;
      const obs = new IntersectionObserver(
        ([entry]) => { if (entry.isIntersecting) setActive(id); },
        { rootMargin: '-20% 0px -60% 0px', threshold: 0 }
      );
      obs.observe(el);
      observers.push(obs);
    });
    return () => observers.forEach(o => o.disconnect());
  }, []);

  const scrollTo = (id: string) => {
    const el = document.getElementById(id);
    el?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    setActive(id);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 pt-6 pb-16">
      <div className="flex gap-8">

        {/* ── Sidebar ─────────────────────────────────────────────────────── */}
        <aside className="hidden lg:block w-52 flex-shrink-0">
          <div className="sticky top-24 space-y-0.5">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-widest mb-3 px-3">
              On this page
            </p>
            {NAV.map(({ id, label, icon }) => (
              <button
                key={id}
                onClick={() => scrollTo(id)}
                className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm text-left transition-all ${
                  active === id
                    ? 'bg-indigo-500/15 text-indigo-300 border border-indigo-500/25'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40 border border-transparent'
                }`}
              >
                <span className="text-base leading-none">{icon}</span>
                {label}
              </button>
            ))}
          </div>
        </aside>

        {/* ── Content ─────────────────────────────────────────────────────── */}
        <div ref={contentRef} className="flex-1 min-w-0 space-y-12">

          {/* ── INSTALLATION ─────────────────────────────────────── */}
          <section>
            <SectionHeading id="installation">Installation</SectionHeading>
            <p className="text-slate-400 text-sm leading-relaxed mb-6">
              Get checkDK running locally in under two minutes. Choose the install method that suits your setup — no Python required for npm.
            </p>

            <SubHeading id="req">Requirements</SubHeading>
            <DocTable
              headers={['Dependency', 'Version', 'Purpose']}
              rows={[
                ['Node.js', '≥ 20', 'npm/npx install (no Python needed)'],
                ['Python', '≥ 3.10', 'Required only for pipx install'],
                ['Docker Engine', '≥ 20.10', 'Docker Compose analysis'],
                ['kubectl', 'any', 'Kubernetes manifest validation'],
              ]}
            />

            <SubHeading id="install-npm">Option A — npm</SubHeading>
            <CodeBlock code="npm install -g @checkdk/cli" />

            <SubHeading id="install-pipx">Option B — pipx</SubHeading>
            <CodeBlock code="pipx install checkdk-cli" />

            <Callout type="tip">
              The npm package ships a pre-compiled binary — no Python, no virtual env, no system dependencies. Works on Linux x64/arm64, macOS x64/arm64, and Windows x64.
            </Callout>

            <SubHeading id="install-auth">Authenticate</SubHeading>
            <p className="text-slate-400 text-sm mb-1">Sign in with GitHub or Google to unlock AI-powered analysis and history.</p>
            <CodeBlock code="checkdk auth login" />

            <SubHeading id="install-first">First analysis</SubHeading>
            <CodeBlock code={`# analyse a Docker Compose file
checkdk playground -f docker-compose.yml

# analyse a Kubernetes manifest
checkdk playground -f k8s-deployment.yaml`} />

            <Callout type="info">
              You can also paste your config at <strong>checkdk.app</strong> — no install needed. Sign in to save history.
            </Callout>
          </section>

          {/* ── OVERVIEW ─────────────────────────────────────────── */}
          <section>
            <SectionHeading id="overview">Overview</SectionHeading>
            <p className="text-slate-400 text-sm leading-relaxed">
              <strong className="text-slate-200">checkDK</strong> is an AI-powered configuration validator for Docker Compose and Kubernetes. It catches port conflicts, security misconfigurations, missing health probes, undefined environment variables, and more — <em>before</em> you deploy. Each issue comes with an AI-generated root cause and copy-paste-ready fix.
            </p>
            <p className="text-slate-400 text-sm leading-relaxed mt-3">
              On top of static analysis, checkDK includes an ML-based pod failure predictor (RandomForest, XGBoost, LSTM) that scores live container metrics for risk of failure.
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-6">
              {[
                { label: 'Web UI', desc: 'Paste or upload a config at checkdk.app — instant results.' },
                { label: 'CLI',    desc: 'Run checkdk playground -f <file> from your terminal.' },
                { label: 'API',    desc: 'POST /analyze/* from any HTTP client or pipeline.' },
              ].map(({ label, desc }) => (
                <div key={label} className="p-4 rounded-xl bg-slate-900 border border-slate-800">
                  <p className="text-sm font-semibold text-indigo-300 mb-1">{label}</p>
                  <p className="text-slate-500 text-xs leading-relaxed">{desc}</p>
                </div>
              ))}
            </div>
          </section>

          {/* ── FEATURES ─────────────────────────────────────────── */}
          <section>
            <SectionHeading id="features">Features</SectionHeading>

            <SubHeading id="feat-docker">Docker Compose Analysis</SubHeading>
            <ul className="space-y-1.5 text-sm text-slate-400 pl-1">
              {[
                'Port conflicts between services',
                'Broken service dependencies (depends_on)',
                'Missing resource limits (cpu/memory)',
                'Undefined or empty environment variables',
                ':latest image tags (non-reproducible builds)',
                'Privileged container mode',
                'Missing restart policies',
              ].map(f => (
                <li key={f} className="flex items-start gap-2">
                  <span className="text-indigo-400 mt-0.5">›</span>{f}
                </li>
              ))}
            </ul>

            <SubHeading id="feat-k8s">Kubernetes Analysis</SubHeading>
            <ul className="space-y-1.5 text-sm text-slate-400 pl-1">
              {[
                'NodePort conflicts across services',
                'Selector / label mismatches (Deployment ↔ Service)',
                'Privilege escalation (allowPrivilegeEscalation: true)',
                'Missing liveness / readiness / startup probes',
                'No resource requests or limits defined',
                'Running containers as root',
                'Missing namespace declarations',
              ].map(f => (
                <li key={f} className="flex items-start gap-2">
                  <span className="text-indigo-400 mt-0.5">›</span>{f}
                </li>
              ))}
            </ul>

            <SubHeading id="feat-ai">AI-Powered Fixes</SubHeading>
            <p className="text-slate-400 text-sm leading-relaxed">
              Every detected issue is sent to an LLM (Mistral → Groq/Llama 3.3 70B → Gemini fallback). The response includes the root cause, a step-by-step fix, and a corrected YAML snippet. Sensitive values (passwords, tokens, keys) are redacted before the payload leaves your browser.
            </p>

            <SubHeading id="feat-history">Analysis History</SubHeading>
            <p className="text-slate-400 text-sm leading-relaxed">
              Every scan is stored per-user in DynamoDB. The History tab surfaces recurring issue patterns across your scans so you can spot systemic problems.
            </p>
          </section>

          {/* ── CLI ──────────────────────────────────────────────── */}
          <section>
            <SectionHeading id="cli">CLI Reference</SectionHeading>
            <p className="text-slate-400 text-sm mb-4">All commands delegate analysis to the backend API. The CLI is a thin HTTP/WebSocket client.</p>

            <DocTable
              headers={['Command', 'Description']}
              rows={[
                [<code className="text-cyan-300">checkdk auth login</code>,    'Open browser OAuth flow; saves JWT locally'],
                [<code className="text-cyan-300">checkdk auth logout</code>,   'Remove local credentials'],
                [<code className="text-cyan-300">checkdk auth whoami</code>,   'Print current authenticated user'],
                [<code className="text-cyan-300">checkdk playground -f &lt;file&gt;</code>, 'Full AI analysis of a config file'],
                [<code className="text-cyan-300">checkdk docker &lt;cmd&gt;</code>,  'Passthrough wrapper for docker commands'],
                [<code className="text-cyan-300">checkdk kubectl &lt;cmd&gt;</code>, 'Passthrough wrapper for kubectl commands'],
                [<code className="text-cyan-300">checkdk predict</code>,       'Run ML pod failure prediction interactively'],
                [<code className="text-cyan-300">checkdk monitor</code>,       'Poll container metrics + show risk score'],
                [<code className="text-cyan-300">checkdk chaos</code>,         'Chaos test helpers'],
              ]}
            />

            <SubHeading id="cli-playground">playground flags</SubHeading>
            <DocTable
              headers={['Flag', 'Type', 'Description']}
              rows={[
                ['-f / --file', 'path', 'Path to docker-compose.yml or k8s manifest'],
                ['--no-ai',     'bool', 'Use rule-based analysis only (faster, no token usage)'],
                ['--json',      'bool', 'Output raw JSON instead of rich terminal UI'],
              ]}
            />
          </section>

          {/* ── API ──────────────────────────────────────────────── */}
          <section>
            <SectionHeading id="api">API Reference</SectionHeading>
            <p className="text-slate-400 text-sm mb-4">
              Base URL: <code className="text-cyan-300 text-sm">https://api.checkdk.app</code>
            </p>
            <Callout type="info">
              Authenticated routes require an <code className="text-indigo-300">Authorization: Bearer &lt;jwt&gt;</code> header. Obtain a token via <code className="text-indigo-300">checkdk auth login</code> or the web sign-in flow.
            </Callout>

            <DocTable
              headers={['Method', 'Path', 'Auth', 'Description']}
              rows={[
                ['POST', '/analyze/docker-compose', <Badge color="amber">Required</Badge>, 'Analyse a Docker Compose YAML'],
                ['POST', '/analyze/kubernetes',     <Badge color="amber">Required</Badge>, 'Analyse a Kubernetes manifest'],
                ['POST', '/analyze/playground',     <Badge color="green">Optional</Badge>, 'Hybrid AI + rule-based audit (any config)'],
                ['POST', '/predict',                <Badge color="amber">Required</Badge>, 'ML pod failure prediction'],
                ['GET',  '/history',                <Badge color="amber">Required</Badge>, 'Fetch user\'s last 10 analyses'],
                ['GET',  '/auth/me',                <Badge color="amber">Required</Badge>, 'Current authenticated user info'],
                ['GET',  '/health',                 <Badge color="green">Public</Badge>,   'Service health check'],
              ]}
            />

            <SubHeading id="api-playground">POST /analyze/playground</SubHeading>
            <p className="text-slate-400 text-sm mb-2">Multi-modal endpoint — accepts any config type and runs both LLM analysis and deterministic validators, then deduplicates findings.</p>
            <CodeBlock lang="json" code={`{
  "content": "version: '3.8'\\nservices:\\n  web:\\n    image: nginx:latest\\n  ...",
  "filename": "docker-compose.yml",
  "use_ai": true
}`} />
          </section>

          {/* ── ML ───────────────────────────────────────────────── */}
          <section>
            <SectionHeading id="ml">ML Prediction</SectionHeading>
            <p className="text-slate-400 text-sm leading-relaxed mb-4">
              checkDK ships four trained models for pod failure prediction. They score live container metrics and return a risk tier (low / medium / high) with confidence percentages.
            </p>

            <DocTable
              headers={['Model', 'Algorithm', 'Endpoint']}
              rows={[
                ['RandomForest', 'scikit-learn RandomForestClassifier', 'POST /predict/random-forest'],
                ['XGBoost',      'XGBoostClassifier',                   'POST /predict/xgboost'],
                ['LSTM',         'PyTorch LSTM (sequence model)',        'POST /predict/lstm'],
                ['Ensemble',     'Soft-vote average of all three',      'POST /predict/ensemble'],
              ]}
            />

            <SubHeading id="ml-features">Input features</SubHeading>
            <DocTable
              headers={['Field', 'Type', 'Range', 'Description']}
              rows={[
                ['cpu_usage',            'float', '0 – 100', 'CPU usage %'],
                ['memory_usage',         'float', '0 – 100', 'Memory usage %'],
                ['disk_usage',           'float', '0 – 100', 'Disk usage %'],
                ['network_latency',      'float', '≥ 0 ms',  'Network round-trip latency (ms)'],
                ['restart_count',        'int',   '≥ 0',     'Container restart count'],
                ['probe_failures',       'int',   '≥ 0',     'Cumulative probe failure count'],
                ['node_cpu_pressure',    'float', '0 – 100', 'Node-level CPU pressure %'],
                ['node_memory_pressure', 'float', '0 – 100', 'Node-level memory pressure %'],
                ['pod_age_minutes',      'float', '≥ 0',     'Age of pod in minutes'],
              ]}
            />

            <SubHeading id="ml-example">Example request</SubHeading>
            <CodeBlock lang="bash" code={`curl -X POST https://api.checkdk.app/predict/random-forest \\
  -H "Authorization: Bearer <token>" \\
  -H "Content-Type: application/json" \\
  -d '{
    "cpu_usage": 82.5,
    "memory_usage": 70.0,
    "disk_usage": 45.0,
    "network_latency": 120.0,
    "restart_count": 3,
    "probe_failures": 1,
    "node_cpu_pressure": 60.0,
    "node_memory_pressure": 55.0,
    "pod_age_minutes": 1440
  }'`} />
          </section>

          {/* ── ARCHITECTURE ─────────────────────────────────────── */}
          <section>
            <SectionHeading id="architecture">Architecture</SectionHeading>
            <CodeBlock lang="text" code={`Browser
  ├──▶ CloudFront CDN ──▶ S3 (React SPA)
  └──▶ CloudFront /api/* ──▶ AWS App Runner (FastAPI)
                                    ├── DynamoDB  (users + history)
                                    ├── Mistral / Groq / Gemini  (AI fixes)
                                    └── RandomForest model  (risk score)`} />
            <DocTable
              headers={['Layer', 'Technology']}
              rows={[
                ['Frontend',  'React 19 · TypeScript · Vite 7 · TailwindCSS 4 · Framer Motion'],
                ['Backend',   'FastAPI · Python 3.11 · Uvicorn'],
                ['Auth',      'GitHub OAuth · Google OAuth · JWT (HS256)'],
                ['Database',  'AWS DynamoDB'],
                ['AI / LLM',  'Mistral AI · Groq (Llama 3.3 70B) · Gemini (fallback)'],
                ['ML',        'scikit-learn RandomForest · XGBoost · PyTorch LSTM'],
                ['Hosting',   'AWS App Runner (backend) · S3 + CloudFront (frontend)'],
                ['CI/CD',     'GitHub Actions → ECR → App Runner + S3 (OIDC auth)'],
              ]}
            />
          </section>

          {/* ── ROADMAP ──────────────────────────────────────────── */}
          <section>
            <SectionHeading id="roadmap">Roadmap</SectionHeading>
            <DocTable
              headers={['Phase', 'Feature', 'Status']}
              rows={[
                ['1', 'AWS infrastructure (App Runner, S3, CloudFront, ECR)',             <Badge color="green">✓ Complete</Badge>],
                ['2', 'Auth + Database (OAuth, JWT, DynamoDB history)',                   <Badge color="green">✓ Complete</Badge>],
                ['3', 'Post-login dashboard (playground, history, models)',               <Badge color="green">✓ Complete</Badge>],
                ['4', 'CI/CD (GitHub Actions — pytest, lint, ECR, S3, CloudFront)',       <Badge color="green">✓ Complete</Badge>],
                ['5', 'Real-time monitoring (REST-polled pod metrics + risk score)',       <Badge color="green">✓ Complete</Badge>],
                ['6', 'Chaos dataset + ML retraining (EKS data via Chaos Mesh)',          <Badge color="slate">Planned</Badge>],
                ['7', 'Amazon Bedrock (Claude Haiku via IAM role)',                       <Badge color="slate">Planned</Badge>],
              ]}
            />
          </section>

        </div>
      </div>
    </div>
  );
}

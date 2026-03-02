// ─────────────────────────────────────────────────────────────────────────────
// services/groqAnalysis.ts
// Groq-powered AI analysis for AWS / Docker / Kubernetes config files.
// ─────────────────────────────────────────────────────────────────────────────

import Groq from 'groq-sdk';

const groq = new Groq({
  apiKey: import.meta.env.VITE_GROQ_API_KEY as string,
  dangerouslyAllowBrowser: true,
});

export type IssueSeverity = 'critical' | 'high' | 'medium' | 'low' | 'info';
export type AnalysisStatus = 'secure' | 'warning' | 'critical';

export interface GroqIssue {
  severity: IssueSeverity;
  title: string;
  description: string;
  line?: number | null;
  recommendation: string;
}

export interface GroqHighlight {
  type: 'good' | 'bad' | 'neutral';
  text: string;
}

export interface GroqAnalysisResult {
  score: number;            // 0–100, higher = more secure
  status: AnalysisStatus;
  summary: string;
  issues: GroqIssue[];
  highlights: GroqHighlight[];
}

// ── System prompt ─────────────────────────────────────────────────────────────

const SYSTEM_PROMPT = `You are an expert DevOps security auditor specialising in AWS, Docker, and Kubernetes configurations.
Analyse the provided configuration file and identify ALL security vulnerabilities, misconfigurations, and best-practice violations.

Check for (not limited to):
- IAM over-permissive policies (Action:"*", Resource:"*", wildcard principals)
- Public S3 buckets / missing bucket policies / ACL issues
- Unencrypted storage (EBS, RDS, S3, Secrets Manager)
- Security groups with 0.0.0.0/0 open on sensitive ports (22, 3389, etc.)
- Missing CloudTrail / VPC flow logs / access logging
- Hardcoded secrets, passwords, or API keys
- Missing MFA enforcement on IAM
- Outdated / deprecated runtimes or API versions
- Missing backup / retention policies
- Non-compliant or missing resource tags
- Missing VPC or overly-permissive network exposure
- Overly-permissive trust relationships
- Docker: root containers, missing resource limits, hardcoded secrets, :latest tags
- Kubernetes: missing resource limits, no liveness/readiness probes, privileged containers, host networking

Respond ONLY with a valid JSON object matching this exact TypeScript interface — no markdown, no explanation, no code fences:

{
  "score": number,          // 0-100 security score (100 = fully secure)
  "status": "secure" | "warning" | "critical",
  "summary": string,        // 2-3 sentence overall summary
  "issues": [
    {
      "severity": "critical" | "high" | "medium" | "low" | "info",
      "title": string,
      "description": string,
      "line": number | null,
      "recommendation": string
    }
  ],
  "highlights": [
    {
      "type": "good" | "bad" | "neutral",
      "text": string
    }
  ]
}

Be precise and specific — cite exact resource names, values, and line numbers where possible.
Do NOT hallucinate issues that are not present. If the config is clean, say so with a high score.`;

// ── Main export ───────────────────────────────────────────────────────────────

export async function analyzeWithGroq(
  configContent: string,
  filename?: string
): Promise<GroqAnalysisResult> {
  if (!import.meta.env.VITE_GROQ_API_KEY) {
    throw new Error(
      'VITE_GROQ_API_KEY is not set. Add it to your .env file and restart the dev server.'
    );
  }

  const userMessage = `Analyse this configuration file${filename ? ` (${filename})` : ''}:

${configContent}

Return ONLY the JSON object — no markdown, no code fences, no explanation.`;

  const completion = await groq.chat.completions.create({
    model: 'llama-3.3-70b-versatile',
    messages: [
      { role: 'system', content: SYSTEM_PROMPT },
      { role: 'user', content: userMessage },
    ],
    temperature: 0.1,
    max_tokens: 4096,
  });

  const raw = completion.choices[0]?.message?.content ?? '';

  // Strip potential markdown code fences that the model may emit
  const cleaned = raw
    .replace(/^```(?:json)?\s*/i, '')
    .replace(/```\s*$/i, '')
    .trim();

  try {
    return JSON.parse(cleaned) as GroqAnalysisResult;
  } catch {
    throw new Error(
      `Groq returned an unparseable response. First 400 chars: ${raw.slice(0, 400)}`
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// services/aiAnalysis.ts
// AI-powered analysis for AWS / Docker / Kubernetes config files.
// Primary: Mistral  |  Fallback: Groq
// ─────────────────────────────────────────────────────────────────────────────

import Groq from 'groq-sdk';
import { Mistral } from '@mistralai/mistralai';

const mistral = new Mistral({
  apiKey: import.meta.env.VITE_MISTRAL_API_KEY as string,
});

const groq = new Groq({
  apiKey: import.meta.env.VITE_GROQ_API_KEY as string,
  dangerouslyAllowBrowser: true,
});

export type IssueSeverity = 'critical' | 'high' | 'medium' | 'low' | 'info';
export type AnalysisStatus = 'secure' | 'warning' | 'critical';

export interface AnalysisIssue {
  severity: IssueSeverity;
  title: string;
  description: string;
  line?: number | null;
  recommendation: string;
}

export interface AnalysisHighlight {
  type: 'good' | 'bad' | 'neutral';
  text: string;
}

export interface AnalysisResult {
  score: number;            // 0–100, higher = more secure
  status: AnalysisStatus;
  summary: string;
  issues: AnalysisIssue[];
  highlights: AnalysisHighlight[];
  provider?: 'mistral' | 'groq';
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

// ── Helpers ───────────────────────────────────────────────────────────────────

function stripFences(raw: string): string {
  return raw
    .replace(/^```(?:json)?\s*/i, '')
    .replace(/```\s*$/i, '')
    .trim();
}

function buildUserMessage(configContent: string, filename?: string): string {
  return `Analyse this configuration file${filename ? ` (${filename})` : ''}:

${configContent}

Return ONLY the JSON object — no markdown, no code fences, no explanation.`;
}

// ── Mistral (primary) ─────────────────────────────────────────────────────────

async function analyzeWithMistral(
  configContent: string,
  filename?: string
): Promise<AnalysisResult> {
  const response = await mistral.chat.complete({
    model: 'mistral-large-latest',
    messages: [
      { role: 'system', content: SYSTEM_PROMPT },
      { role: 'user', content: buildUserMessage(configContent, filename) },
    ],
    temperature: 0.1,
    maxTokens: 4096,
  });

  const raw = (response.choices?.[0]?.message?.content as string) ?? '';
  const cleaned = stripFences(raw);

  try {
    const result = JSON.parse(cleaned) as AnalysisResult;
    result.provider = 'mistral';
    return result;
  } catch {
    throw new Error(
      `Mistral returned an unparseable response. First 400 chars: ${raw.slice(0, 400)}`
    );
  }
}

// ── Groq (fallback) ───────────────────────────────────────────────────────────

async function analyzeWithGroq(
  configContent: string,
  filename?: string
): Promise<AnalysisResult> {
  if (!import.meta.env.VITE_GROQ_API_KEY) {
    throw new Error(
      'VITE_GROQ_API_KEY is not set. Add it to your .env file and restart the dev server.'
    );
  }

  const completion = await groq.chat.completions.create({
    model: 'llama-3.3-70b-versatile',
    messages: [
      { role: 'system', content: SYSTEM_PROMPT },
      { role: 'user', content: buildUserMessage(configContent, filename) },
    ],
    temperature: 0.1,
    max_tokens: 4096,
  });

  const raw = completion.choices[0]?.message?.content ?? '';
  const cleaned = stripFences(raw);

  try {
    const result = JSON.parse(cleaned) as AnalysisResult;
    result.provider = 'groq';
    return result;
  } catch {
    throw new Error(
      `Groq returned an unparseable response. First 400 chars: ${raw.slice(0, 400)}`
    );
  }
}

// ── Main export ───────────────────────────────────────────────────────────────

export async function analyze(
  configContent: string,
  filename?: string
): Promise<AnalysisResult> {
  if (!import.meta.env.VITE_MISTRAL_API_KEY && !import.meta.env.VITE_GROQ_API_KEY) {
    throw new Error(
      'Neither VITE_MISTRAL_API_KEY nor VITE_GROQ_API_KEY is set. Add at least one to your .env file and restart the dev server.'
    );
  }

  // Try Mistral first
  if (import.meta.env.VITE_MISTRAL_API_KEY) {
    try {
      return await analyzeWithMistral(configContent, filename);
    } catch (mistralErr) {
      console.warn('[analyze] Mistral failed, falling back to Groq:', mistralErr);
    }
  }

  // Fall back to Groq
  return analyzeWithGroq(configContent, filename);
}

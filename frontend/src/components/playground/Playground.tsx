import React, { useState, useRef, useCallback, useEffect } from 'react';
import {
  Play, Copy, Check, FileText, Upload, Loader2, ChevronDown,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { analyze } from '../../services/aiAnalysis';
import type { AnalysisResult } from '../../services/aiAnalysis';
import { AnalysisResults } from './AnalysisResults';
import { useAuth } from '../../context/AuthContext';

// ── Sample configs (deliberately misconfigured for demo) ────────────────────────────────────────────────────────────────────

const SAMPLE_CONFIGS = {
  'S3 Bucket': `AWSTemplateFormatVersion: '2010-09-09'
Resources:
  MyS3Bucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: my-public-data-bucket
      AccessControl: PublicRead
      VersioningConfiguration:
        Status: Suspended`,

  'IAM Role': `AWSTemplateFormatVersion: '2010-09-09'
Resources:
  AdminRole:
    Type: AWS::IAM::Role
    Properties:
      RoleName: AdminRole
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: ec2.amazonaws.com
            Action: sts:AssumeRole
      Policies:
        - PolicyName: FullAccess
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Effect: Allow
                Action: '*'
                Resource: '*'`,

  'EC2 Security Group': `AWSTemplateFormatVersion: '2010-09-09'
Resources:
  WebServerSG:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupDescription: Web server security group
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: 22
          ToPort: 22
          CidrIp: 0.0.0.0/0
        - IpProtocol: '-1'
          CidrIp: 0.0.0.0/0`,

  'Docker Compose': `version: "3.9"
services:
  web:
    image: nginx:latest
    ports:
      - "80:80"
    environment:
      - DB_PASSWORD=supersecret123
    depends_on:
      - db
  db:
    image: postgres:14
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_PASSWORD=\${POSTGRES_PASSWORD}`,

  'Kubernetes': `apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: my-app
  template:
    spec:
      containers:
        - name: my-app
          image: my-registry/my-app:latest
          env:
            - name: DB_PASSWORD
              value: "hardcoded-secret"`,
} as const;

type SampleKey = keyof typeof SAMPLE_CONFIGS;

const ACCEPTED = '.yml,.yaml,.json,.tf,.toml';

// ── Playground ────────────────────────────────────────────────────────────────

const Playground = () => {
  const { token, isAuthenticated } = useAuth();
  const [code, setCode] = useState<string>(SAMPLE_CONFIGS['S3 Bucket']);
  const [copied, setCopied] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [uploadedFilename, setUploadedFilename] = useState<string | undefined>(undefined);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showSamples, setShowSamples] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const dragCounter = useRef(0);
  // Refs for the two inner-scrollable containers
  const editorRef = useRef<HTMLTextAreaElement>(null);
  const resultsScrollRef = useRef<HTMLDivElement>(null);

  // ── File handling ───────────────────────────────────────────────────────────
  const loadFile = useCallback((file: File) => {
    if (!/\.(ya?ml|json|tf|toml)$/i.test(file.name)) {
      alert('Please upload a .yml, .yaml, .json, .tf, or .toml file.');
      return;
    }
    if (file.size > 512 * 1024) {
      alert('File is too large. Maximum size is 512 KB.');
      return;
    }
    const reader = new FileReader();
    reader.onload = (e) => {
      setCode(e.target?.result as string);
      setUploadedFilename(file.name);
      setResult(null);
      setError(null);
    };
    reader.readAsText(file);
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) loadFile(file);
    e.target.value = '';
  };

  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    dragCounter.current++;
    if (e.dataTransfer.types.includes('Files')) setIsDragging(true);
  };
  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    dragCounter.current--;
    if (dragCounter.current === 0) setIsDragging(false);
  };
  const handleDragOver = (e: React.DragEvent) => e.preventDefault();
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    dragCounter.current = 0;
    const file = e.dataTransfer.files?.[0];
    if (file) loadFile(file);
  };

  // ── Analysis ────────────────────────────────────────────────────────────────
  const handleAnalyze = async () => {
    if (!code.trim() || isAnalyzing) return;
    setIsAnalyzing(true);
    setResult(null);
    setError(null);
    try {
      const data = await analyze(code, uploadedFilename, token);
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed. Please try again.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  // ── Helpers ─────────────────────────────────────────────────────────────────
  const handleCopy = async () => {
    await navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleClear = () => {
    setCode('');
    setUploadedFilename(undefined);
    setResult(null);
    setError(null);
  };

  const loadSample = (key: SampleKey) => {
    setCode(SAMPLE_CONFIGS[key]);
    setUploadedFilename(undefined);
    setResult(null);
    setError(null);
    setShowSamples(false);
  };

  const lineCount = code.split('\n').length;

  // ── Double-boundary scroll chaining ─────────────────────────────────────────
  // How it works:
  //   • Both elements are registered in window.__lenisPreventMap ('prevent' by
  //     default) so Lenis ignores their wheel events unless we change the state.
  //   • When the user hits a scroll boundary:
  //       – FIRST hit  → set map to 'chain' (arm), absorb the event entirely.
  //       – SECOND hit → map is already 'chain', do NOT call preventDefault;
  //         the event bubbles to Lenis, whose prevent() callback sees 'chain'
  //         and lets Lenis handle it → page scrolls smoothly via Lenis itself.
  //   • As soon as the element is no longer at a boundary, map resets to
  //     'prevent' so the next boundary hit starts fresh.
  useEffect(() => {
    const attachHandler = (el: HTMLElement | null) => {
      if (!el) return () => {};

      // Register this element as 'prevent' so Lenis ignores it by default.
      window.__lenisPreventMap?.set(el, 'prevent');

      const handler = (e: WheelEvent) => {
        const map = window.__lenisPreventMap;
        if (!map) return;

        const { scrollTop, scrollHeight, clientHeight } = el;
        const atBottom = scrollTop + clientHeight >= scrollHeight - 1;
        const atTop    = scrollTop <= 0;
        const atBoundary =
          (atBottom && e.deltaY > 0) || (atTop && e.deltaY < 0);

        if (!atBoundary) {
          // Mid-inner-scroll: ensure Lenis stays prevented.
          map.set(el, 'prevent');
          return; // let browser scroll the inner element natively
        }

        const prevState = map.get(el) ?? 'prevent';

        if (prevState === 'prevent') {
          // FIRST boundary hit: arm for next event, then absorb this one.
          map.set(el, 'chain');
          e.preventDefault();    // stop browser from bouncing / scrolling page
          e.stopPropagation();   // stop Lenis from seeing this event
          return;
        }

        // SECOND+ boundary hit (prevState === 'chain'):
        // Do NOT call preventDefault or stopPropagation.
        // The event bubbles to Lenis; prevent() returns false for 'chain' nodes
        // → Lenis processes the event and smoothly scrolls the page.
        // (State stays 'chain' so continued scrolling keeps chaining.)
      };

      el.addEventListener('wheel', handler, { passive: false });
      return () => {
        el.removeEventListener('wheel', handler);
        window.__lenisPreventMap?.delete(el);
      };
    };

    const cleanupEditor  = attachHandler(editorRef.current);
    const cleanupResults = attachHandler(resultsScrollRef.current);
    return () => {
      cleanupEditor();
      cleanupResults();
    };
  }, []);

  // ── Render ──────────────────────────────────────────────────────────────────
  return (
    <section id="playground" className="py-24 px-4 sm:px-6 bg-slate-950 relative overflow-hidden">
      {/* Background glow */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[400px] bg-violet-500/5 rounded-full blur-[120px]" />
      </div>

      <div className="max-w-7xl mx-auto relative z-10">
        {/* Header */}
        <div className="text-center mb-14">
          <h2 className="text-4xl sm:text-5xl font-bold tracking-tight mb-5 bg-clip-text text-transparent bg-gradient-to-r from-white via-violet-200 to-white">
            Interactive Playground
          </h2>
          <p className="text-slate-400 text-lg max-w-2xl mx-auto">
            Paste your config, load a sample, or{' '}
            <span className="text-violet-300">upload a file</span> — CheckDK
            analyses it instantly for security issues, misconfigurations, and
            best-practice violations.
          </p>

          {/* Sign-in nudge for unauthenticated users */}
          {!isAuthenticated && (
            <div className="mt-5 inline-flex items-center gap-2.5 px-4 py-2.5 rounded-xl bg-amber-500/10 border border-amber-500/25 text-amber-300 text-sm">
              <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
              <span>
                Rule-based checks only.{' '}
                <Link to="/login" className="underline underline-offset-2 hover:text-amber-200 transition-colors">
                  Sign in
                </Link>{' '}
                for full AI-powered analysis.
              </span>
            </div>
          )}
        </div>

        {/* Two-panel layout */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 items-start">
          {/* ── Left: Editor ──────────────────────────────────────────────── */}
          <div className="flex flex-col gap-3">
            {/* Toolbar */}
            <div className="flex items-center gap-2 flex-wrap">
              {/* Samples dropdown */}
              <div className="relative">
                <button
                  onClick={() => setShowSamples((v) => !v)}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-mono font-medium bg-slate-800/60 border border-slate-700 text-slate-400 hover:text-slate-200 hover:border-slate-600 transition-all"
                >
                  Load sample
                  <ChevronDown className={`w-3 h-3 transition-transform duration-200 ${showSamples ? 'rotate-180' : ''}`} />
                </button>
                {showSamples && (
                  <div className="absolute left-0 mt-1 w-52 rounded-xl border border-slate-700/60 bg-slate-800 shadow-xl z-20">
                    {(Object.keys(SAMPLE_CONFIGS) as SampleKey[]).map((key) => (
                      <button
                        key={key}
                        onClick={() => loadSample(key)}
                        className="w-full text-left text-xs px-4 py-2.5 text-slate-300 hover:bg-slate-700/60 first:rounded-t-xl last:rounded-b-xl transition-colors"
                      >
                        {key}
                      </button>
                    ))}
                  </div>
                )}
              </div>

              <div className="w-px h-4 bg-slate-700" />

              {/* Upload button */}
              <button
                onClick={() => fileInputRef.current?.click()}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-mono font-medium bg-violet-600/15 border border-violet-500/30 text-violet-300 hover:bg-violet-600/25 transition-all"
              >
                <Upload className="w-3.5 h-3.5" />
                {uploadedFilename ? uploadedFilename : 'Upload file'}
              </button>
              <input
                ref={fileInputRef}
                type="file"
                accept={ACCEPTED}
                className="hidden"
                onChange={handleFileChange}
              />

              {code && (
                <button
                  onClick={handleClear}
                  className="ml-auto px-2.5 py-1.5 rounded-lg text-xs font-mono text-slate-500 hover:text-slate-300 hover:bg-slate-800 transition-all border border-transparent hover:border-slate-700"
                >
                  Clear
                </button>
              )}
            </div>

            {/* Editor window */}
            <div
              className={`relative rounded-xl bg-slate-900 overflow-hidden h-[480px] flex flex-col transition-colors duration-200 border ${
                isDragging ? 'border-violet-500/60 bg-violet-900/10' : 'border-slate-700/60'
              }`}
              onDragEnter={handleDragEnter}
              onDragLeave={handleDragLeave}
              onDragOver={handleDragOver}
              onDrop={handleDrop}
            >
              {/* Drag overlay */}
              {isDragging && (
                <div className="absolute inset-0 z-50 flex flex-col items-center justify-center gap-3 bg-slate-950/80 backdrop-blur-sm rounded-xl pointer-events-none">
                  <div className="w-16 h-16 rounded-2xl bg-violet-500/20 border-2 border-dashed border-violet-400/60 flex items-center justify-center">
                    <Upload className="w-7 h-7 text-violet-300 animate-bounce" />
                  </div>
                  <p className="text-violet-200 font-semibold text-sm">Drop your config file here</p>
                  <p className="text-slate-400 text-xs">.yml · .yaml · .json · .tf · .toml</p>
                </div>
              )}

              {/* Window chrome */}
              <div className="flex items-center gap-1.5 px-4 py-2.5 border-b border-slate-800 bg-slate-950 flex-shrink-0">
                <span className="w-3 h-3 rounded-full bg-red-500/70" />
                <span className="w-3 h-3 rounded-full bg-amber-500/70" />
                <span className="w-3 h-3 rounded-full bg-green-500/70" />
                <FileText className="w-3.5 h-3.5 text-slate-500 ml-2" />
                <span className="ml-1 text-slate-500 text-xs font-mono">
                  {uploadedFilename ?? 'config.yml'}
                </span>
                {code && (
                  <>
                    <span className="ml-auto text-slate-600 text-xs font-mono">{lineCount} lines</span>
                    <button
                      onClick={handleCopy}
                      className="ml-3 p-1 rounded hover:bg-slate-800 text-slate-500 hover:text-slate-300 transition-colors"
                      title="Copy"
                    >
                      {copied
                        ? <Check className="w-3.5 h-3.5 text-emerald-400" />
                        : <Copy className="w-3.5 h-3.5" />
                      }
                    </button>
                  </>
                )}
              </div>

              {/* Editor with line numbers */}
              <div className="flex flex-1 overflow-hidden">
                <div className="flex-shrink-0 w-10 bg-slate-950/50 border-r border-slate-800 pt-4 pb-4 px-2 overflow-hidden select-none">
                  {Array.from({ length: Math.max(lineCount, 20) }, (_, i) => (
                    <div key={i} className="text-slate-700 text-xs font-mono leading-6 text-right">
                      {i + 1}
                    </div>
                  ))}
                </div>
                <textarea
                  value={code}
                  onChange={(e) => { setCode(e.target.value); setResult(null); setError(null); }}
                  onKeyDown={(e) => {
                    if (e.key === 'Tab') {
                      e.preventDefault();
                      const el = e.currentTarget;
                      const s = el.selectionStart;
                      const end = el.selectionEnd;
                      const next = code.substring(0, s) + '  ' + code.substring(end);
                      setCode(next);
                      setTimeout(() => {
                        el.selectionStart = s + 2;
                        el.selectionEnd = s + 2;
                      }, 0);
                    }
                  }}
                  placeholder={`# Paste your config here, load a sample, or drag & drop a file\n\nversion: "3.9"\nservices:\n  web:\n    image: nginx:latest`}
                  ref={editorRef}
                  className="flex-1 bg-transparent text-slate-200 font-mono text-sm leading-6 resize-none outline-none p-4 placeholder:text-slate-700 magenta-scrollbar"
                  spellCheck={false}
                  autoComplete="off"
                  autoCorrect="off"
                />
              </div>
            </div>

            {/* Analyse button */}
            <button
              onClick={handleAnalyze}
              disabled={!code.trim() || isAnalyzing}
              className={`relative w-full py-3.5 rounded-xl font-semibold text-sm transition-all duration-300 overflow-hidden group ${
                code.trim() && !isAnalyzing
                  ? 'bg-gradient-to-r from-violet-600 to-purple-600 hover:from-violet-500 hover:to-purple-500 text-white shadow-lg shadow-violet-500/25 hover:shadow-violet-500/40'
                  : 'bg-slate-800 text-slate-500 cursor-not-allowed'
              }`}
            >
              {isAnalyzing ? (
                <span className="flex items-center justify-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Analysing…
                </span>
              ) : (
                <span className="flex items-center justify-center gap-2">
                  <Play className="w-4 h-4" />
                  Analyse
                </span>
              )}
              {code.trim() && !isAnalyzing && (
                <div className="absolute inset-0 -translate-x-full group-hover:translate-x-full transition-transform duration-700 bg-gradient-to-r from-transparent via-white/10 to-transparent" />
              )}
            </button>
          </div>

          {/* ── Right: Results ────────────────────────────────────────────── */}
          <div className="min-h-[540px] max-h-[80vh] rounded-xl border border-slate-700/60 bg-slate-900/30 flex flex-col overflow-hidden">
            {/* Window chrome */}
            <div className="flex items-center gap-1.5 px-4 py-2.5 border-b border-slate-800 bg-slate-950 flex-shrink-0">
              <span className="w-3 h-3 rounded-full bg-red-500/70" />
              <span className="w-3 h-3 rounded-full bg-amber-500/70" />
              <span className="w-3 h-3 rounded-full bg-green-500/70" />
            </div>

            <div ref={resultsScrollRef} className="flex-1 p-5 overflow-y-auto magenta-scrollbar">
              {/* Idle */}
              {!isAnalyzing && !result && !error && (
                <div className="h-full flex flex-col items-center justify-center text-center gap-4">
                  <div className="w-16 h-16 rounded-2xl bg-violet-500/10 border border-violet-500/20 flex items-center justify-center">
                    <Play className="w-7 h-7 text-violet-400" />
                  </div>
                  <div>
                    <p className="text-slate-400 font-medium">Analysis results will appear here</p>
                    <p className="text-slate-600 text-sm mt-1">
                      Load a sample, paste a config, or upload a file — then click Analyse
                    </p>
                  </div>
                </div>
              )}

              {/* Loading */}
              {isAnalyzing && (
                <div className="h-full flex flex-col items-center justify-center gap-5">
                  <Loader2 className="w-10 h-10 text-violet-400 animate-spin" />
                  <div className="text-center">
                    <p className="text-slate-300 font-medium">Analysing your configuration…</p>
                  </div>
                </div>
              )}

              {/* Error */}
              {error && !isAnalyzing && (
                <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-5">
                  <p className="text-red-300 font-semibold text-sm mb-1">Analysis failed</p>
                  <p className="text-red-400/80 text-sm">{error}</p>
                </div>
              )}

              {/* Results */}
              {result && !isAnalyzing && (
                <AnalysisResults result={result} filename={uploadedFilename} />
              )}
            </div>
          </div>
        </div>

        {/* Footer callout */}
      </div>
    </section>
  );
};

export default Playground;

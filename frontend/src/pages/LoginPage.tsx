// ─────────────────────────────────────────────────────────────────────────────
// pages/LoginPage.tsx
// Sign-in page for checkDK.
// Clicking a provider button redirects to the backend OAuth flow.
// ─────────────────────────────────────────────────────────────────────────────

import { useEffect, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../context/AuthContext';

// ── OAuth redirect helpers ─────────────────────────────────────────────────────
// Both redirects go to the backend OAuth initiation route. The backend will then
// redirect the user to the provider, handle the callback, and finally redirect
// back to /auth/callback#token=<jwt>.

function getApiBase(): string {
  const win = window as unknown as { __CHECKDK_ENV__?: { CHECKDK_API_URL?: string } };
  if (win.__CHECKDK_ENV__?.CHECKDK_API_URL) return win.__CHECKDK_ENV__.CHECKDK_API_URL.replace(/\/+$/, '');
  if (import.meta.env.VITE_API_URL) return (import.meta.env.VITE_API_URL as string).replace(/\/+$/, '');
  return '/api';
}

function signInWithGitHub() {
  const cliCallback = new URLSearchParams(window.location.search).get('cli_callback');
  if (cliCallback) sessionStorage.setItem('checkdk_cli_callback', cliCallback);
  window.location.href = `${getApiBase()}/auth/github`;
}

function signInWithGoogle() {
  const cliCallback = new URLSearchParams(window.location.search).get('cli_callback');
  if (cliCallback) sessionStorage.setItem('checkdk_cli_callback', cliCallback);
  window.location.href = `${getApiBase()}/auth/google`;
}

// ── Error messages ────────────────────────────────────────────────────────────

const ERROR_MESSAGES: Record<string, string> = {
  access_denied: 'You denied access. Please try again if you want to sign in.',
  oauth_failed: 'OAuth sign-in failed. Please try again.',
  callback_failed: 'Authentication callback failed. Please try again.',
  token_invalid: 'Received an invalid token. Please try signing in again.',
};

function getErrorMessage(code: string | null): string | null {
  if (!code) return null;
  return ERROR_MESSAGES[code] ?? `Sign-in error: ${code}`;
}

// ── Component ─────────────────────────────────────────────────────────────────

export default function LoginPage() {
  const { isAuthenticated, token } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [dismissedError, setDismissedError] = useState(false);
  const [cliDone, setCliDone] = useState(false);

  const nextPath = searchParams.get('next') ?? '/app/dashboard';
  const cliCallback = searchParams.get('cli_callback');
  const errorCode = searchParams.get('error');
  const errorMessage = getErrorMessage(errorCode);

  // If the user is already signed in AND this is a CLI login request,
  // send the existing token directly to the CLI's local callback server
  // instead of redirecting to the dashboard.
  useEffect(() => {
    if (isAuthenticated && cliCallback && token) {
      // Save cli_callback to sessionStorage in case the user re-authenticates
      sessionStorage.setItem('checkdk_cli_callback', cliCallback);
      const dest = `${cliCallback}?token=${encodeURIComponent(token)}`;
      fetch(dest)
        .then(() => setCliDone(true))
        .catch(() => {
          // fetch may fail due to CORS on redirect — try as a navigation fallback
          window.location.href = dest;
        });
      return;
    }
    // Normal case: already signed in with no CLI callback → go to dashboard
    if (isAuthenticated && !cliCallback) navigate(nextPath, { replace: true });
  }, [isAuthenticated, navigate, nextPath, cliCallback, token]);

  // CLI token was sent successfully → show confirmation instead of login card
  if (cliDone) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="fixed inset-0 pointer-events-none overflow-hidden">
          <div className="absolute top-1/3 left-1/2 -translate-x-1/2 w-96 h-96 bg-indigo-500/15 rounded-full blur-[120px]" />
        </div>
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.3 }}
          className="flex flex-col items-center gap-5 text-center px-4"
        >
          <div className="w-14 h-14 rounded-2xl bg-green-500/20 border border-green-500/30 flex items-center justify-center">
            <svg className="w-7 h-7 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <div>
            <p className="text-white font-semibold text-lg">Logged in to checkDK CLI</p>
            <p className="text-slate-400 text-sm mt-1">You can close this tab and return to your terminal.</p>
          </div>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center px-4">
      {/* Background glows */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <div className="absolute top-1/4 -left-1/4 w-1/2 h-1/2 bg-indigo-500/15 rounded-full blur-[120px]" />
        <div className="absolute bottom-1/4 -right-1/4 w-1/2 h-1/2 bg-purple-500/15 rounded-full blur-[120px]" />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: 'easeOut' }}
        className="relative w-full max-w-sm"
      >
        {/* Card */}
        <div className="bg-slate-900/80 backdrop-blur-xl rounded-2xl border border-slate-700/50 shadow-2xl shadow-indigo-500/10 p-8">

          {/* Logo + Title */}
          <div className="flex flex-col items-center gap-3 mb-8">
            <Link to="/">
              <img src="/favicon.svg" alt="checkDK" className="w-12 h-12 hover:scale-105 transition-transform" />
            </Link>
            <div className="text-center">
              <h1 className="text-xl font-bold text-white">Sign in to checkDK</h1>
              <p className="text-slate-400 text-sm mt-1">
                Get AI-powered config analysis & history tracking
              </p>
            </div>
          </div>

          {/* Error banner */}
          <AnimatePresence>
            {errorMessage && !dismissedError && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="mb-5 overflow-hidden"
              >
                <div className="flex items-start gap-3 p-4 rounded-xl bg-red-500/10 border border-red-500/30">
                  <svg className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
                  </svg>
                  <p className="text-red-300 text-sm flex-1">{errorMessage}</p>
                  <button
                    onClick={() => setDismissedError(true)}
                    className="text-red-500 hover:text-red-300 transition-colors"
                    aria-label="Dismiss"
                  >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* OAuth buttons */}
          <div className="flex flex-col gap-3">
            {/* GitHub */}
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={signInWithGitHub}
              className="flex items-center justify-center gap-3 w-full px-5 py-3 rounded-xl bg-slate-800 border border-slate-700 text-white font-medium text-sm hover:bg-slate-700 hover:border-slate-600 transition-all"
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <path fillRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clipRule="evenodd" />
              </svg>
              Continue with GitHub
            </motion.button>

            {/* Google */}
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={signInWithGoogle}
              className="flex items-center justify-center gap-3 w-full px-5 py-3 rounded-xl bg-slate-800 border border-slate-700 text-white font-medium text-sm hover:bg-slate-700 hover:border-slate-600 transition-all"
            >
              {/* Google "G" logo */}
              <svg className="w-5 h-5" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
              </svg>
              Continue with Google
            </motion.button>
          </div>

          {/* Divider + back to home */}
          <div className="mt-6 pt-6 border-t border-slate-800 text-center">
            <p className="text-slate-500 text-xs">
              No account needed — we use your OAuth provider.{' '}
              <Link to="/" className="text-indigo-400 hover:text-indigo-300 transition-colors">
                Back to home ↗
              </Link>
            </p>
          </div>
        </div>

        {/* Privacy note */}
        <p className="text-center text-slate-600 text-xs mt-4">
          By signing in you agree to our{' '}
          <a href="#" className="text-slate-500 hover:text-slate-400 transition-colors">Terms</a>
          {' '}and{' '}
          <a href="#" className="text-slate-500 hover:text-slate-400 transition-colors">Privacy Policy</a>.
        </p>
      </motion.div>
    </div>
  );
}

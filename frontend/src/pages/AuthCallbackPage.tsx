// ─────────────────────────────────────────────────────────────────────────────
// pages/AuthCallbackPage.tsx
// Handles the redirect from the backend after OAuth success.
//
// Expected URL shape:  /auth/callback#token=<jwt>
//
// Flow (browser login):
//   1. Read token from window.location.hash
//   2. Call auth.login(token) -> stores in localStorage
//   3. Navigate to /app/dashboard
//
// Flow (CLI login):
//   1. Read token from window.location.hash
//   2. Read cli_callback URL from sessionStorage (set by LoginPage)
//   3. Redirect to http://127.0.0.1:PORT/callback?token=<jwt>
//   4. Show "you can close this tab" message
// ─────────────────────────────────────────────────────────────────────────────

import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useAuth } from '../context/AuthContext';

export default function AuthCallbackPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const handled = useRef(false);

  // Read cli_callback synchronously before first render so the effect never
  // calls setState (avoids react-hooks/set-state-in-effect lint error).
  const [cliMode] = useState(() => !!sessionStorage.getItem('checkdk_cli_callback'));

  useEffect(() => {
    if (handled.current) return;
    handled.current = true;

    const hash = window.location.hash;
    const params = new URLSearchParams(hash.replace(/^#/, ''));
    const token = params.get('token');

    if (!token) {
      navigate('/login?error=callback_failed', { replace: true });
      return;
    }

    const cliCallback = sessionStorage.getItem('checkdk_cli_callback');
    sessionStorage.removeItem('checkdk_cli_callback');

    if (cliCallback) {
      // CLI flow: POST token to the local server; no state update needed here
      // because cliMode was already derived above.
      const dest = `${cliCallback}?token=${encodeURIComponent(token)}`;
      fetch(dest).catch(() => { window.location.href = dest; });
      return;
    }

    // Normal browser flow
    try {
      login(token);
      setTimeout(() => navigate('/app/dashboard', { replace: true }), 50);
    } catch {
      navigate('/login?error=token_invalid', { replace: true });
    }
  }, [login, navigate]);

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
        {cliMode ? (
          <>
            <div className="w-14 h-14 rounded-2xl bg-green-500/20 border border-green-500/30 flex items-center justify-center">
              <svg className="w-7 h-7 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <div>
              <p className="text-white font-semibold text-lg">Logged in to checkDK CLI</p>
              <p className="text-slate-400 text-sm mt-1">You can close this tab and return to your terminal.</p>
            </div>
          </>
        ) : (
          <>
            <div className="w-14 h-14 rounded-2xl bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center">
              <svg className="w-7 h-7 text-indigo-400 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
            </div>
            <div>
              <p className="text-white font-semibold text-lg">Signing you in...</p>
              <p className="text-slate-400 text-sm mt-1">Just a moment while we get things ready.</p>
            </div>
          </>
        )}
      </motion.div>
    </div>
  );
}

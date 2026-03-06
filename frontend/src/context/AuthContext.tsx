// ─────────────────────────────────────────────────────────────────────────────
// context/AuthContext.tsx
// Provides authentication state throughout the app.
// JWT is stored in localStorage under the key 'checkdk_token'.
// The payload is decoded client-side (no signature verification — that's the
// server's job). We just need the claims for display purposes.
// ─────────────────────────────────────────────────────────────────────────────

import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  type ReactNode,
} from 'react';

// ── Types ────────────────────────────────────────────────────────────────────

export interface AuthUser {
  userId: string;
  email: string;
  name: string;
  avatarUrl: string;
  provider: string;
  exp: number; // Unix timestamp seconds
}

export interface AuthContextValue {
  user: AuthUser | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (token: string) => void;
  logout: () => void;
}

// ── Helpers ──────────────────────────────────────────────────────────────────

const TOKEN_KEY = 'checkdk_token';

/** Decode a JWT payload without verifying signature (client-side read-only). */
function decodeJwtPayload(token: string): AuthUser | null {
  try {
    const parts = token.split('.');
    if (parts.length !== 3) return null;
    // Base64url → base64 → JSON
    const padded = parts[1].padEnd(parts[1].length + ((4 - parts[1].length % 4) % 4), '=');
    const json = atob(padded.replace(/-/g, '+').replace(/_/g, '/'));
    const payload = JSON.parse(json);
    // Reject expired tokens immediately
    if (payload.exp && Date.now() / 1000 > payload.exp) return null;
    return {
      userId: payload.sub ?? '',
      email: payload.email ?? '',
      name: payload.name ?? '',
      avatarUrl: payload.avatarUrl ?? payload.avatar_url ?? '',
      provider: payload.provider ?? '',
      exp: payload.exp ?? 0,
    };
  } catch {
    return null;
  }
}

// ── Context ───────────────────────────────────────────────────────────────────

const AuthContext = createContext<AuthContextValue>({
  user: null,
  token: null,
  isAuthenticated: false,
  isLoading: true,
  login: () => {},
  logout: () => {},
});

// ── Provider ──────────────────────────────────────────────────────────────────

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // On mount: restore token from localStorage
  useEffect(() => {
    const stored = localStorage.getItem(TOKEN_KEY);
    if (stored) {
      const decoded = decodeJwtPayload(stored);
      if (decoded) {
        setToken(stored);
        setUser(decoded);
      } else {
        // Token expired or invalid — clean up
        localStorage.removeItem(TOKEN_KEY);
      }
    }
    setIsLoading(false);
  }, []);

  const login = useCallback((newToken: string) => {
    const decoded = decodeJwtPayload(newToken);
    if (!decoded) {
      console.error('[Auth] Received invalid or expired token');
      return;
    }
    localStorage.setItem(TOKEN_KEY, newToken);
    setToken(newToken);
    setUser(decoded);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    setToken(null);
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: user !== null,
        isLoading,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

// ── Hook ──────────────────────────────────────────────────────────────────────

export function useAuth(): AuthContextValue {
  return useContext(AuthContext);
}

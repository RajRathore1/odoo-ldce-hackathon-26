"use client";

import { useRouter } from "next/navigation";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";
import { api, onSignedOut } from "@/lib/api/client";
import { clearTokens, hasSession, storeTokens } from "@/lib/api/tokens";
import type { AuthResult, AuthUser, RegisterPayload } from "@/lib/api/types";

type AuthState = {
  user: AuthUser | null;
  /** Still working out whether there is a session. */
  loading: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (payload: RegisterPayload) => Promise<void>;
  signOut: () => Promise<void>;
  refreshUser: () => Promise<void>;
};

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  // localStorage is not readable while rendering on the server, so the very
  // first paint always starts as "unknown" and settles here.
  useEffect(() => {
    let active = true;

    async function restore() {
      if (!hasSession()) {
        if (active) setLoading(false);
        return;
      }

      try {
        const me = await api<AuthUser>("/users/me/");
        if (active) setUser(me);
      } catch {
        clearTokens();
      } finally {
        if (active) setLoading(false);
      }
    }

    restore();

    return () => {
      active = false;
    };
  }, []);

  // A refresh token the backend has rejected ends the session wherever the
  // failing call happened to be.
  useEffect(() => {
    return onSignedOut(() => {
      setUser(null);
      router.replace("/login");
    });
  }, [router]);

  const signIn = useCallback(async (email: string, password: string) => {
    const result = await api<AuthResult>("/auth/login/", {
      method: "POST",
      body: { email, password },
      anonymous: true,
    });
    storeTokens(result.tokens);
    setUser(result.user);
  }, []);

  const signUp = useCallback(async (payload: RegisterPayload) => {
    const result = await api<AuthResult>("/auth/register/", {
      method: "POST",
      body: payload,
      anonymous: true,
    });
    storeTokens(result.tokens);
    setUser(result.user);
  }, []);

  const signOut = useCallback(async () => {
    const refresh = window.localStorage.getItem("gt_refresh");

    if (refresh) {
      // Best effort: the tokens go regardless, so a backend hiccup can never
      // leave someone stuck in a session they asked to end.
      try {
        await api("/auth/logout/", { method: "POST", body: { refresh } });
      } catch {
        // ignored on purpose
      }
    }

    clearTokens();
    setUser(null);
    router.replace("/login");
  }, [router]);

  const refreshUser = useCallback(async () => {
    setUser(await api<AuthUser>("/users/me/"));
  }, []);

  return (
    <AuthContext.Provider
      value={{ user, loading, signIn, signUp, signOut, refreshUser }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside AuthProvider");
  return context;
}

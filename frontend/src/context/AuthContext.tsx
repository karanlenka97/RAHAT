"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { User, LoginCredentials, AuthResponse } from "@/types/auth";
import { apiClient, ApiError } from "@/lib/api";

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => Promise<void>;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const TOKEN_STORAGE_KEY = "rahat_auth_token";

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function initAuth() {
      if (typeof window === "undefined") {
        if (isMounted) setIsLoading(false);
        return;
      }

      const storedToken = sessionStorage.getItem(TOKEN_STORAGE_KEY);
      if (!storedToken) {
        if (isMounted) setIsLoading(false);
        return;
      }

      try {
        const userProfile = await apiClient<User>("/api/v1/auth/me", {
          token: storedToken,
        });
        if (isMounted) {
          setUser(userProfile);
          setToken(storedToken);
        }
      } catch (err) {
        console.warn("Session verification failed or token expired:", err);
        sessionStorage.removeItem(TOKEN_STORAGE_KEY);
        if (isMounted) {
          setUser(null);
          setToken(null);
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    initAuth();

    return () => {
      isMounted = false;
    };
  }, []);

  const login = async (credentials: LoginCredentials) => {
    setIsLoading(true);
    setError(null);
    try {
      const authData = await apiClient<AuthResponse>("/api/v1/auth/login", {
        method: "POST",
        body: JSON.stringify(credentials),
      });

      setToken(authData.access_token);
      setUser(authData.user);

      if (typeof window !== "undefined") {
        sessionStorage.setItem(TOKEN_STORAGE_KEY, authData.access_token);
      }
    } catch (err: unknown) {
      const msg =
        err instanceof ApiError
          ? err.message
          : err instanceof Error
          ? err.message
          : "Authentication failed. Please check your network and credentials.";
      setError(msg);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    setIsLoading(true);
    try {
      if (token) {
        await apiClient("/api/v1/auth/logout", {
          method: "POST",
          token,
        }).catch(() => {
          // Graceful fallback if backend is unreachable
        });
      }
    } finally {
      setUser(null);
      setToken(null);
      if (typeof window !== "undefined") {
        sessionStorage.removeItem(TOKEN_STORAGE_KEY);
      }
      setIsLoading(false);
    }
  };

  const clearError = () => setError(null);

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!user && !!token,
        isLoading,
        error,
        login,
        logout,
        clearError,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}

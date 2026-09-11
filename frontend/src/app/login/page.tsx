"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import { ApiError } from "@/lib/api";

const DEMO_ACCOUNTS = [
  { label: "ASHA", id: "+919000000008", name: "Manju Bai (ASHA)" },
  { label: "Doctor", id: "doctor@rahat.local", name: "Dr. Rajesh Varma" },
  { label: "MO", id: "medical.officer@rahat.local", name: "Dr. Sunita Patel" },
  { label: "CHO", id: "cho@rahat.local", name: "Pooja Mishra" },
  { label: "ANM", id: "anm@rahat.local", name: "Kavita Devi" },
  { label: "Admin", id: "admin@rahat.local", name: "System Admin" },
  { label: "District", id: "district.admin@rahat.local", name: "District Officer" },
  { label: "Facility", id: "facility.admin@rahat.local", name: "Superintendent" },
];

export default function LoginPage() {
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  const { login, error: contextError, clearError } = useAuth();
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLocalError(null);
    clearError();

    if (!identifier.trim() || !password.trim()) {
      setLocalError("Please enter your registered phone/email and password.");
      return;
    }

    setSubmitting(true);
    try {
      await login({
        identifier: identifier.trim(),
        password: password.trim(),
      });
      router.push("/dashboard");
    } catch (err: unknown) {
      const msg =
        err instanceof ApiError
          ? err.message
          : err instanceof Error
          ? err.message
          : "Invalid credentials. Please verify your details.";
      setLocalError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  const fillDemoAccount = (demoId: string) => {
    setIdentifier(demoId);
    setPassword("RahatDev@2026");
    setLocalError(null);
    clearError();
  };

  const displayError = localError || contextError;

  return (
    <div className="flex min-h-screen flex-col justify-center bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950 px-4 py-12 sm:px-6 lg:px-8 text-slate-100">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        {/* Brand Header */}
        <div className="text-center">
          <Link href="/" className="inline-flex items-center gap-2 mb-4">
            <div className="h-11 w-11 rounded-xl bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center font-bold text-emerald-400 text-2xl shadow-inner">
              R
            </div>
            <span className="text-3xl font-extrabold tracking-tight bg-gradient-to-r from-emerald-400 to-teal-200 bg-clip-text text-transparent">
              RAHAT
            </span>
          </Link>
          <h2 className="text-2xl font-bold tracking-tight text-white">
            Healthcare Access Portal
          </h2>
          <p className="mt-1 text-sm text-slate-400">
            Sign in to access emergency routing & clinical triage
          </p>
        </div>

        {/* Login Card */}
        <div className="mt-8 bg-slate-900/80 border border-slate-800 backdrop-blur-md px-6 py-8 shadow-2xl rounded-2xl sm:px-10">
          {displayError && (
            <div className="mb-6 rounded-lg bg-rose-500/10 border border-rose-500/30 p-4 text-sm text-rose-400 flex items-start gap-3">
              <span className="font-bold">⚠️</span>
              <div className="flex-1">{displayError}</div>
            </div>
          )}

          <form className="space-y-5" onSubmit={handleSubmit}>
            <div>
              <label
                htmlFor="identifier"
                className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5"
              >
                Phone Number or Email
              </label>
              <input
                id="identifier"
                name="identifier"
                type="text"
                autoComplete="username"
                required
                value={identifier}
                onChange={(e) => setIdentifier(e.target.value)}
                placeholder="+919000000008 or asha@rahat.local"
                className="w-full rounded-lg bg-slate-950 border border-slate-700 px-3.5 py-2.5 text-sm text-white placeholder-slate-500 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
              />
            </div>

            <div>
              <label
                htmlFor="password"
                className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5"
              >
                Password
              </label>
              <input
                id="password"
                name="password"
                type="password"
                autoComplete="current-password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full rounded-lg bg-slate-950 border border-slate-700 px-3.5 py-2.5 text-sm text-white placeholder-slate-500 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
              />
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="w-full mt-2 flex items-center justify-center rounded-lg bg-emerald-500 hover:bg-emerald-400 active:bg-emerald-600 px-4 py-3 text-sm font-semibold text-slate-950 transition-colors shadow-lg shadow-emerald-500/20 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {submitting ? (
                <span className="inline-flex items-center gap-2">
                  <span className="h-4 w-4 animate-spin rounded-full border-2 border-slate-950 border-t-transparent"></span>
                  Authenticating...
                </span>
              ) : (
                "Sign In"
              )}
            </button>
          </form>

          {/* Quick Demo Credentials */}
          <div className="mt-8 pt-6 border-t border-slate-800">
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3 text-center">
              Quick Test Accounts (Phase 3 Seeded)
            </p>
            <div className="grid grid-cols-4 gap-1.5">
              {DEMO_ACCOUNTS.map((acc) => (
                <button
                  key={acc.label}
                  type="button"
                  onClick={() => fillDemoAccount(acc.id)}
                  className="px-2 py-1.5 text-xs font-medium bg-slate-800/80 hover:bg-slate-700 hover:text-emerald-400 border border-slate-700 rounded-md text-slate-300 text-center truncate transition"
                  title={`${acc.name} (${acc.id})`}
                >
                  {acc.label}
                </button>
              ))}
            </div>
            <p className="mt-2 text-[11px] text-slate-500 text-center">
              Click any role to autofill test credentials (Password: <code className="text-slate-400">RahatDev@2026</code>)
            </p>
          </div>
        </div>

        {/* Back Link */}
        <div className="mt-6 text-center">
          <Link
            href="/"
            className="text-xs text-slate-400 hover:text-emerald-400 transition underline underline-offset-4"
          >
            ← Back to Overview
          </Link>
        </div>
      </div>
    </div>
  );
}

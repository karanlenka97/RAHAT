"use client";

import React from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import { ProtectedRoute } from "@/components/ProtectedRoute";

function DashboardContent() {
  const { user, logout } = useAuth();
  const router = useRouter();

  const handleLogout = async () => {
    await logout();
    router.push("/login");
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Top Navbar */}
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link href="/" className="flex items-center gap-2">
              <div className="h-9 w-9 rounded-lg bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center font-bold text-emerald-400 text-lg">
                R
              </div>
              <span className="text-xl font-bold tracking-tight bg-gradient-to-r from-emerald-400 to-teal-200 bg-clip-text text-transparent">
                RAHAT
              </span>
            </Link>
            <span className="hidden sm:inline-block text-xs uppercase tracking-wider text-slate-400 border-l border-slate-700 pl-2">
              Portal Dashboard
            </span>
          </div>

          <div className="flex items-center gap-4">
            <div className="hidden sm:flex flex-col text-right">
              <span className="text-xs font-semibold text-white">{user?.full_name}</span>
              <span className="text-[11px] font-mono text-emerald-400">{user?.role}</span>
            </div>
            <button
              onClick={handleLogout}
              className="px-3.5 py-1.5 text-xs font-medium bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 rounded-lg transition"
            >
              Sign Out
            </button>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-10">
        {/* Welcome Banner */}
        <div className="p-6 sm:p-8 rounded-2xl bg-gradient-to-r from-emerald-950/40 via-slate-900 to-slate-900 border border-emerald-500/20 mb-8">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-500/20 text-emerald-400 mb-2">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-ping"></span>
                Session Active (Phase 3 Verified)
              </div>
              <h1 className="text-2xl sm:text-3xl font-extrabold text-white">
                Welcome, {user?.full_name}
              </h1>
              <p className="mt-1 text-sm text-slate-400">
                Logged in with RBAC Role: <strong className="text-emerald-400">{user?.role}</strong>
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span className="px-3 py-1 text-xs font-mono bg-slate-800 text-slate-300 rounded-md border border-slate-700">
                UID: {user?.id.slice(0, 8)}...
              </span>
            </div>
          </div>
        </div>

        {/* User Identity Details & RBAC Permissions Card */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Identity Card */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400 mb-4">
              Authenticated Identity
            </h2>
            <dl className="space-y-3 text-sm">
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <dt className="text-slate-400">Full Name</dt>
                <dd className="font-medium text-white">{user?.full_name}</dd>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <dt className="text-slate-400">Registered Phone</dt>
                <dd className="font-mono text-emerald-400">{user?.phone}</dd>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <dt className="text-slate-400">Email Address</dt>
                <dd className="font-mono text-slate-300">{user?.email || "N/A"}</dd>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <dt className="text-slate-400">Assigned Role</dt>
                <dd className="font-semibold text-emerald-400">{user?.role}</dd>
              </div>
              <div className="flex justify-between py-1">
                <dt className="text-slate-400">Account Status</dt>
                <dd className="text-emerald-400 flex items-center gap-1.5">
                  <span className="h-2 w-2 rounded-full bg-emerald-400"></span> Active & Verified
                </dd>
              </div>
            </dl>
          </div>

          {/* Permissions Matrix Card */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400 mb-4">
              RBAC Role Permissions
            </h2>
            <div className="flex flex-wrap gap-2 mb-4">
              {user?.permissions && user.permissions.length > 0 ? (
                user.permissions.map((perm) => (
                  <span
                    key={perm}
                    className="px-2.5 py-1 text-xs font-mono bg-slate-800 border border-slate-700 text-slate-300 rounded-md"
                  >
                    {perm}
                  </span>
                ))
              ) : (
                <span className="text-xs text-slate-500">No specific granular permissions assigned.</span>
              )}
            </div>
            <p className="text-xs text-slate-500">
              Future protected modules (Patient intake, referral dispatch, bed allocation) will enforce these RBAC scopes.
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}

export default function DashboardPage() {
  return (
    <ProtectedRoute>
      <DashboardContent />
    </ProtectedRoute>
  );
}

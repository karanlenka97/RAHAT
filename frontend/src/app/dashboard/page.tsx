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
              Future clinical workflows will enforce these RBAC scopes.
            </p>
          </div>
        </div>

        {/* Available Modules */}
        <div className="mt-8">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400 mb-4">
            Active Core Modules
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            <Link
              href="/patients"
              className="group p-6 rounded-xl bg-gradient-to-br from-slate-900 to-emerald-950/20 border border-slate-800 hover:border-emerald-500/40 transition shadow-lg hover:shadow-emerald-950/30 flex flex-col justify-between"
            >
              <div>
                <div className="h-10 w-10 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 font-bold mb-4 group-hover:scale-105 transition">
                  👥
                </div>
                <h3 className="text-base font-bold text-white group-hover:text-emerald-400 transition">
                  Patient Registry & Intake
                </h3>
                <p className="mt-1 text-xs text-slate-400">
                  Search, register, and update rural citizen health records with village association and unique patient codes.
                </p>
              </div>
              <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs text-emerald-400 font-medium">
                <span>Access Module</span>
                <span>&rarr;</span>
              </div>
            </Link>

            <Link
              href="/care-requests"
              className="group p-6 rounded-xl bg-gradient-to-br from-slate-900 to-teal-950/20 border border-slate-800 hover:border-teal-500/40 transition shadow-lg hover:shadow-teal-950/30 flex flex-col justify-between"
            >
              <div>
                <div className="h-10 w-10 rounded-lg bg-teal-500/10 border border-teal-500/30 flex items-center justify-center text-teal-400 font-bold mb-4 group-hover:scale-105 transition">
                  🩺
                </div>
                <h3 className="text-base font-bold text-white group-hover:text-teal-400 transition">
                  Care Requests & Triage
                </h3>
                <p className="mt-1 text-xs text-slate-400">
                  Log clinical requirements, assess triage urgency, and record specialist and diagnostic needs for registered patients.
                </p>
              </div>
              <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs text-teal-400 font-medium">
                <span>Access Module</span>
                <span>&rarr;</span>
              </div>
            </Link>

            <Link
              href="/facilities"
              className="group p-6 rounded-xl bg-gradient-to-br from-slate-900 to-cyan-950/20 border border-slate-800 hover:border-cyan-500/40 transition shadow-lg hover:shadow-cyan-950/30 flex flex-col justify-between"
            >
              <div>
                <div className="h-10 w-10 rounded-lg bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400 font-bold mb-4 group-hover:scale-105 transition">
                  🏥
                </div>
                <h3 className="text-base font-bold text-white group-hover:text-cyan-400 transition">
                  Facilities & Capabilities
                </h3>
                <p className="mt-1 text-xs text-slate-400">
                  Inspect health center tiers, bed availability, verified clinical capabilities, and locate nearby facilities via geospatial lookup.
                </p>
              </div>
              <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs text-cyan-400 font-medium">
                <span>Access Module</span>
                <span>&rarr;</span>
              </div>
            </Link>

            <Link
              href="/referrals"
              className="group p-6 rounded-xl bg-gradient-to-br from-slate-900 to-indigo-950/20 border border-slate-800 hover:border-indigo-500/40 transition shadow-lg hover:shadow-indigo-950/30 flex flex-col justify-between"
            >
              <div>
                <div className="h-10 w-10 rounded-lg bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center text-indigo-400 font-bold mb-4 group-hover:scale-105 transition">
                  🚑
                </div>
                <h3 className="text-base font-bold text-white group-hover:text-indigo-400 transition">
                  Referral Lifecycle & Tracking
                </h3>
                <p className="mt-1 text-xs text-slate-400">
                  Manage patient referral acceptance, patient notification, transit milestones, clinical service completion, and back-referrals.
                </p>
              </div>
              <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs text-indigo-400 font-medium">
                <span>Access Module</span>
                <span>&rarr;</span>
              </div>
            </Link>
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

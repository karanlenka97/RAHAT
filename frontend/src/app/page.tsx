"use client";

import Link from "next/link";
import { useAuth } from "@/context/AuthContext";

export default function Home() {
  const { isAuthenticated, user } = useAuth();

  return (
    <div className="flex flex-col min-h-screen bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950 text-slate-100">
      {/* Navigation Bar */}
      <header className="border-b border-slate-800 bg-slate-950/80 backdrop-blur sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="h-9 w-9 rounded-lg bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center font-bold text-emerald-400 text-lg">
              R
            </div>
            <div>
              <span className="text-xl font-bold tracking-tight bg-gradient-to-r from-emerald-400 to-teal-200 bg-clip-text text-transparent">
                RAHAT
              </span>
              <span className="hidden sm:inline-block ml-2 text-xs uppercase tracking-wider text-slate-400 border-l border-slate-700 pl-2">
                SwasthyaSetu
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
              Phase 3 RBAC Ready
            </span>

            {isAuthenticated ? (
              <Link
                href="/dashboard"
                className="px-3.5 py-1.5 text-xs font-semibold bg-emerald-500 hover:bg-emerald-400 text-slate-950 rounded-lg transition"
              >
                Dashboard ({user?.role})
              </Link>
            ) : (
              <Link
                href="/login"
                className="px-3.5 py-1.5 text-xs font-semibold bg-emerald-500 hover:bg-emerald-400 text-slate-950 rounded-lg transition shadow-md shadow-emerald-500/10"
              >
                Sign In
              </Link>
            )}
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-12 flex flex-col justify-center">
        <div className="text-center max-w-3xl mx-auto mb-12">
          <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight text-white mb-4">
            Rural Assistance & Healthcare Access Tele-network
          </h1>
          <p className="text-lg text-slate-400 leading-relaxed mb-6">
            Scalable foundation for intelligent patient routing, dynamic healthcare capacity allocation, and emergency referral workflows.
          </p>
          <div className="flex flex-wrap justify-center gap-4">
            <Link
              href="/login"
              className="px-6 py-3 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-semibold text-sm transition shadow-lg shadow-emerald-500/20"
            >
              Access Healthcare Portal
            </Link>
            <Link
              href="/dashboard"
              className="px-6 py-3 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700 text-white font-semibold text-sm transition"
            >
              View Protected Dashboard
            </Link>
          </div>
        </div>

        {/* Foundation Modules Status Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
          <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 shadow-sm hover:border-slate-700 transition">
            <div className="text-xs font-semibold text-emerald-400 uppercase tracking-wider mb-2">Auth & Security</div>
            <h2 className="text-lg font-bold text-white mb-1">JWT & RBAC</h2>
            <p className="text-sm text-slate-400">8 Standard Roles with token authentication, route guards, and bcrypt hashing.</p>
          </div>

          <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 shadow-sm hover:border-slate-700 transition">
            <div className="text-xs font-semibold text-sky-400 uppercase tracking-wider mb-2">Backend API</div>
            <h2 className="text-lg font-bold text-white mb-1">FastAPI Service</h2>
            <p className="text-sm text-slate-400">Asynchronous REST API with health monitoring, auth endpoints & OpenAPI docs.</p>
          </div>

          <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 shadow-sm hover:border-slate-700 transition">
            <div className="text-xs font-semibold text-indigo-400 uppercase tracking-wider mb-2">Spatial Storage</div>
            <h2 className="text-lg font-bold text-white mb-1">PostgreSQL + PostGIS</h2>
            <p className="text-sm text-slate-400">13 core domain tables with PostGIS geometry fields & spatial indexes.</p>
          </div>

          <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 shadow-sm hover:border-slate-700 transition">
            <div className="text-xs font-semibold text-amber-400 uppercase tracking-wider mb-2">Cache & Queue</div>
            <h2 className="text-lg font-bold text-white mb-1">Redis Engine</h2>
            <p className="text-sm text-slate-400">Low-latency caching and distributed queue infrastructure.</p>
          </div>
        </div>

        {/* Environment & Quick Info */}
        <div className="bg-slate-900/40 rounded-xl border border-slate-800/80 p-6 flex flex-col sm:flex-row items-center justify-between gap-4 text-sm text-slate-400">
          <div>
            <span className="font-semibold text-slate-300">System Status:</span> Phase 3 Authentication & RBAC fully operational.
          </div>
          <div className="flex items-center gap-4">
            <a
              href="http://localhost:8000/docs"
              target="_blank"
              rel="noopener noreferrer"
              className="text-emerald-400 hover:text-emerald-300 underline underline-offset-4"
            >
              Backend Docs (Local)
            </a>
            <span className="text-slate-700">•</span>
            <a
              href="http://localhost:8000/health"
              target="_blank"
              rel="noopener noreferrer"
              className="text-emerald-400 hover:text-emerald-300 underline underline-offset-4"
            >
              Health Check
            </a>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 py-6 text-center text-xs text-slate-500">
        <p>RAHAT / SwasthyaSetu — Smart Healthcare Referral Architecture</p>
      </footer>
    </div>
  );
}

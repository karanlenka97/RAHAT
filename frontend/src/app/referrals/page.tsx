"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { getReferrals } from "@/lib/referralApi";
import { Referral, ReferralStatus } from "@/types/referral";
import { ApiError } from "@/lib/api";

const STATUS_FILTERS: { value: string; label: string }[] = [
  { value: "", label: "All Statuses" },
  { value: "PENDING_ACCEPTANCE", label: "Pending Acceptance" },
  { value: "ACCEPTED", label: "Accepted" },
  { value: "PATIENT_NOTIFIED", label: "Patient Notified" },
  { value: "DEPARTED", label: "In Transit (Departed)" },
  { value: "ARRIVED", label: "Arrived at Facility" },
  { value: "IN_SERVICE", label: "In Service" },
  { value: "COMPLETED", label: "Completed" },
  { value: "BACK_REFERRED", label: "Back Referred" },
  { value: "REJECTED", label: "Rejected" },
  { value: "REROUTED", label: "Rerouted" },
];

const URGENCY_FILTERS = [
  { value: "", label: "All Urgencies" },
  { value: "EMERGENCY", label: "Emergency" },
  { value: "HIGH", label: "High" },
  { value: "MEDIUM", label: "Medium" },
  { value: "LOW", label: "Low" },
];

function UrgencyBadge({ urgency }: { urgency: string }) {
  switch (urgency?.toUpperCase()) {
    case "EMERGENCY":
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-bold bg-rose-500/20 text-rose-400 border border-rose-500/40 shadow-sm shadow-rose-500/10">
          <span className="h-1.5 w-1.5 rounded-full bg-rose-400 animate-ping"></span>
          EMERGENCY
        </span>
      );
    case "HIGH":
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/20 text-amber-400 border border-amber-500/40">
          HIGH
        </span>
      );
    case "MEDIUM":
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-teal-500/20 text-teal-400 border border-teal-500/40">
          MEDIUM
        </span>
      );
    case "LOW":
    default:
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-800 text-slate-300 border border-slate-700">
          LOW
        </span>
      );
  }
}

function StatusBadge({ status }: { status: ReferralStatus | string }) {
  switch (status) {
    case "PENDING_ACCEPTANCE":
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-semibold bg-amber-500/10 text-amber-300 border border-amber-500/30">
          <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse"></span>
          Pending Acceptance
        </span>
      );
    case "ACCEPTED":
      return (
        <span className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-semibold bg-teal-500/10 text-teal-300 border border-teal-500/30">
          Accepted
        </span>
      );
    case "PATIENT_NOTIFIED":
      return (
        <span className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-medium bg-cyan-500/10 text-cyan-300 border border-cyan-500/30">
          Patient Notified
        </span>
      );
    case "DEPARTED":
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-semibold bg-indigo-500/10 text-indigo-300 border border-indigo-500/30">
          🚑 In Transit (Departed)
        </span>
      );
    case "ARRIVED":
      return (
        <span className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-semibold bg-blue-500/10 text-blue-300 border border-blue-500/30">
          Arrived at Facility
        </span>
      );
    case "IN_SERVICE":
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-semibold bg-purple-500/10 text-purple-300 border border-purple-500/30">
          <span className="w-1.5 h-1.5 rounded-full bg-purple-400"></span>
          In Service
        </span>
      );
    case "COMPLETED":
      return (
        <span className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-bold bg-emerald-500/10 text-emerald-300 border border-emerald-500/30">
          ✓ Completed
        </span>
      );
    case "BACK_REFERRED":
      return (
        <span className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-bold bg-violet-500/20 text-violet-300 border border-violet-500/40">
          ↺ Back Referred
        </span>
      );
    case "REJECTED":
      return (
        <span className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-semibold bg-rose-500/10 text-rose-300 border border-rose-500/30">
          ✕ Rejected
        </span>
      );
    case "REROUTED":
      return (
        <span className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-medium bg-orange-500/10 text-orange-300 border border-orange-500/30">
          ➔ Rerouted
        </span>
      );
    default:
      return (
        <span className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-medium bg-slate-800 text-slate-400 border border-slate-700">
          {status}
        </span>
      );
  }
}

function ReferralListContent() {
  const { user, token, logout } = useAuth();
  const router = useRouter();

  const [referrals, setReferrals] = useState<Referral[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [page, setPage] = useState<number>(1);
  const [totalPages, setTotalPages] = useState<number>(1);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [search, setSearch] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [urgencyFilter, setUrgencyFilter] = useState<string>("");

  useEffect(() => {
    let isMounted = true;

    async function loadReferrals() {
      if (!token) return;
      setIsLoading(true);
      setError(null);

      try {
        const data = await getReferrals(
          {
            page,
            page_size: 15,
            status: statusFilter || undefined,
            urgency: urgencyFilter || undefined,
            search: search.trim() || undefined,
          },
          token
        );

        if (isMounted) {
          setReferrals(data.items);
          setTotal(data.total);
          setTotalPages(data.total_pages);
        }
      } catch (err: unknown) {
        if (isMounted) {
          const msg =
            err instanceof ApiError
              ? err.message
              : err instanceof Error
              ? err.message
              : "Failed to load referrals.";
          setError(msg);
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    loadReferrals();

    return () => {
      isMounted = false;
    };
  }, [token, page, statusFilter, urgencyFilter, search]);

  const handleLogout = async () => {
    await logout();
    router.push("/login");
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Top Navbar */}
      <header className="border-b border-slate-800/80 bg-slate-900/60 backdrop-blur-md sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-8">
            <Link href="/dashboard" className="flex items-center gap-3">
              <div className="h-9 w-9 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-400 flex items-center justify-center font-bold text-white shadow-lg shadow-emerald-900/30">
                R
              </div>
              <span className="font-extrabold text-lg tracking-wider text-white">
                RAHAT
              </span>
            </Link>

            <nav className="hidden md:flex items-center gap-1 text-sm font-medium">
              <Link
                href="/dashboard"
                className="px-3 py-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/50 transition"
              >
                Dashboard
              </Link>
              <Link
                href="/patients"
                className="px-3 py-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/50 transition"
              >
                Patients
              </Link>
              <Link
                href="/care-requests"
                className="px-3 py-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/50 transition"
              >
                Care Requests
              </Link>
              <Link
                href="/facilities"
                className="px-3 py-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/50 transition"
              >
                Facilities
              </Link>
              <Link
                href="/referrals"
                className="px-3 py-1.5 rounded-lg bg-slate-800 text-emerald-400 font-semibold"
              >
                Referrals
              </Link>
            </nav>
          </div>

          <div className="flex items-center gap-4">
            <div className="hidden sm:block text-right">
              <div className="text-xs font-semibold text-white">
                {user?.full_name}
              </div>
              <div className="text-[11px] font-mono text-emerald-400">
                {user?.role}
              </div>
            </div>
            <button
              onClick={handleLogout}
              className="p-2 rounded-lg bg-slate-800/60 hover:bg-slate-800 text-slate-400 hover:text-rose-400 border border-slate-700/50 transition text-xs"
              title="Logout"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Page Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
          <div>
            <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-3">
              Referral Tracking & Journey
              <span className="text-xs px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 font-mono font-normal">
                {total} Records
              </span>
            </h1>
            <p className="text-xs text-slate-400 mt-1">
              End-to-end referral lifecycle management: Facility acceptance, patient briefing, transit tracking, and continuity of care.
            </p>
          </div>

          <Link
            href="/care-requests"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-lg shadow-emerald-950/40 transition self-start md:self-auto"
          >
            <span>+ Create Referral from Care Request</span>
          </Link>
        </div>

        {/* Search & Filter Toolbar */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4 mb-6 space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div>
              <label className="block text-[11px] font-medium text-slate-400 mb-1">
                Search Referral / Patient
              </label>
              <input
                type="text"
                placeholder="Code (e.g. REF-RAHAT-000001), name, phone..."
                value={search}
                onChange={(e) => {
                  setSearch(e.target.value);
                  setPage(1);
                }}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 transition"
              />
            </div>

            <div>
              <label className="block text-[11px] font-medium text-slate-400 mb-1">
                Status Filter
              </label>
              <select
                value={statusFilter}
                onChange={(e) => {
                  setStatusFilter(e.target.value);
                  setPage(1);
                }}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500 transition"
              >
                {STATUS_FILTERS.map((f) => (
                  <option key={f.value} value={f.value}>
                    {f.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-[11px] font-medium text-slate-400 mb-1">
                Urgency Level
              </label>
              <select
                value={urgencyFilter}
                onChange={(e) => {
                  setUrgencyFilter(e.target.value);
                  setPage(1);
                }}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500 transition"
              >
                {URGENCY_FILTERS.map((u) => (
                  <option key={u.value} value={u.value}>
                    {u.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-xs text-rose-400 mb-6">
            <strong>Error:</strong> {error}
          </div>
        )}

        {/* Loading Skeleton */}
        {isLoading && (
          <div className="space-y-3">
            {[1, 2, 3, 4, 5].map((i) => (
              <div
                key={i}
                className="animate-pulse bg-slate-900/40 border border-slate-800/80 rounded-xl p-5 flex justify-between items-center"
              >
                <div className="space-y-2 w-1/3">
                  <div className="h-4 bg-slate-800 rounded w-1/2"></div>
                  <div className="h-3 bg-slate-800/60 rounded w-3/4"></div>
                </div>
                <div className="h-6 bg-slate-800 rounded w-24"></div>
              </div>
            ))}
          </div>
        )}

        {/* Empty State */}
        {!isLoading && !error && referrals.length === 0 && (
          <div className="text-center py-16 px-4 border border-dashed border-slate-800 rounded-2xl bg-slate-900/20">
            <div className="w-14 h-14 rounded-full bg-slate-800 flex items-center justify-center mx-auto mb-4 text-slate-500">
              <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
              </svg>
            </div>
            <h3 className="text-base font-semibold text-white">No Referrals Found</h3>
            <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
              No patient referrals match your current filters. Open a Care Request to generate recommendations and initiate a referral.
            </p>
            <div className="mt-5">
              <Link
                href="/care-requests"
                className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition"
              >
                Go to Care Requests
              </Link>
            </div>
          </div>
        )}

        {/* Referral Cards List */}
        {!isLoading && !error && referrals.length > 0 && (
          <div className="space-y-3">
            {referrals.map((ref) => (
              <div
                key={ref.id}
                className="bg-slate-900/60 border border-slate-800/80 hover:border-slate-700 rounded-xl p-5 transition group hover:shadow-lg"
              >
                <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                  {/* Left Side: Referral Code, Patient, Destination */}
                  <div className="space-y-2 flex-1">
                    <div className="flex flex-wrap items-center gap-2.5">
                      <Link
                        href={`/referrals/${ref.id}`}
                        className="font-mono text-sm font-bold text-white hover:text-emerald-400 transition"
                      >
                        {ref.referral_code}
                      </Link>
                      <UrgencyBadge urgency={ref.urgency} />
                      <StatusBadge status={ref.status} />
                      {ref.parent_referral_id && (
                        <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-orange-950/40 text-orange-400 border border-orange-500/30">
                          Rerouted Child
                        </span>
                      )}
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2 text-xs">
                      <div>
                        <span className="text-slate-500">Patient: </span>
                        <strong className="text-slate-200 font-medium">
                          {ref.patient_name || "Anonymous"}
                        </strong>{" "}
                        <span className="text-slate-500 font-mono text-[11px]">
                          ({ref.patient_code})
                        </span>
                      </div>

                      <div>
                        <span className="text-slate-500">Receiving: </span>
                        <strong className="text-emerald-400 font-medium">
                          {ref.receiving_facility_name}
                        </strong>
                      </div>

                      <div>
                        <span className="text-slate-500">Origin / Source: </span>
                        <span className="text-slate-300">
                          {ref.source_facility_name || ref.patient_village || "Community Post"}
                        </span>
                      </div>
                    </div>

                    <div className="text-xs text-slate-400 line-clamp-1">
                      <span className="text-slate-500">Reason: </span>
                      {ref.clinical_summary || ref.referral_reason || "None specified"}
                    </div>
                  </div>

                  {/* Right Side: Action Button */}
                  <div className="flex items-center gap-3 self-end lg:self-center shrink-0">
                    <span className="text-[11px] text-slate-500 font-mono hidden sm:inline">
                      {new Date(ref.created_at).toLocaleDateString("en-IN")}
                    </span>
                    <Link
                      href={`/referrals/${ref.id}`}
                      className="px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white border border-slate-700 text-xs font-semibold transition inline-flex items-center gap-1.5"
                    >
                      <span>View Journey</span>
                      <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    </Link>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Pagination */}
        {!isLoading && totalPages > 1 && (
          <div className="flex items-center justify-between border-t border-slate-800/80 pt-6 mt-6">
            <div className="text-xs text-slate-400">
              Showing page <strong className="text-white">{page}</strong> of{" "}
              <strong className="text-white">{totalPages}</strong> ({total} total referrals)
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs font-medium text-slate-300 hover:text-white hover:bg-slate-800 disabled:opacity-50 disabled:pointer-events-none transition"
              >
                Previous
              </button>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs font-medium text-slate-300 hover:text-white hover:bg-slate-800 disabled:opacity-50 disabled:pointer-events-none transition"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default function ReferralsPage() {
  return (
    <ProtectedRoute>
      <ReferralListContent />
    </ProtectedRoute>
  );
}

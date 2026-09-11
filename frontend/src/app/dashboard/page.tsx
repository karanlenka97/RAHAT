"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import {
  getFrontlineDashboard,
  getFacilityDashboard,
  getDistrictDashboard,
  getReferralFunnel,
} from "@/lib/dashboardApi";
import {
  FrontlineDashboardData,
  FacilityDashboardData,
  DistrictDashboardData,
  ReferralFunnelData,
} from "@/types/dashboard";

type DashboardTab = "frontline" | "facility" | "district";

function DashboardContent() {
  const { user, token, logout } = useAuth();
  const router = useRouter();

  // Determine permitted tabs based on user role
  const userRole = (user?.role || "").toUpperCase();
  const isAdmin = userRole === "ADMIN";
  const isDistrictAdmin = userRole === "DISTRICT_ADMIN";
  const isFacilityUser = ["FACILITY_ADMIN", "DOCTOR", "MEDICAL_OFFICER"].includes(userRole);

  const [activeTab, setActiveTab] = useState<DashboardTab>(() => {
    if (isDistrictAdmin) return "district";
    if (isFacilityUser && !["ASHA", "ANM", "CHO", "MEDICAL_OFFICER"].includes(userRole)) return "facility";
    return "frontline";
  });

  const [timeRange, setTimeRange] = useState<string>("all");
  const [reloadKey, setReloadKey] = useState<number>(0);

  // State for data
  const [frontlineData, setFrontlineData] = useState<FrontlineDashboardData | null>(null);
  const [facilityData, setFacilityData] = useState<FacilityDashboardData | null>(null);
  const [districtData, setDistrictData] = useState<DistrictDashboardData | null>(null);
  const [funnelData, setFunnelData] = useState<ReferralFunnelData | null>(null);

  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleLogout = async () => {
    await logout();
    router.push("/login");
  };

  const userFacilityId = user?.facility_id;

  useEffect(() => {
    let isMounted = true;

    async function fetchData() {
      if (!token) return;
      setIsLoading(true);
      setErrorMessage(null);

      try {
        if (activeTab === "frontline") {
          const data = await getFrontlineDashboard(token);
          if (isMounted) setFrontlineData(data);
        } else if (activeTab === "facility") {
          const data = await getFacilityDashboard(token, userFacilityId || null);
          if (isMounted) setFacilityData(data);
        } else if (activeTab === "district") {
          const [dData, fData] = await Promise.all([
            getDistrictDashboard(token, null, timeRange),
            getReferralFunnel(token, null, null, timeRange),
          ]);
          if (isMounted) {
            setDistrictData(dData);
            setFunnelData(fData);
          }
        }
      } catch (err: unknown) {
        if (isMounted) {
          const msg = err instanceof Error ? err.message : "Failed to load dashboard operational metrics.";
          setErrorMessage(msg);
        }
      } finally {
        if (isMounted) setIsLoading(false);
      }
    }

    fetchData();

    return () => {
      isMounted = false;
    };
  }, [token, activeTab, timeRange, userFacilityId, reloadKey]);

  // Urgency badge styling helper
  const getUrgencyBadge = (urgency: string) => {
    const u = (urgency || "").toUpperCase();
    if (u === "EMERGENCY") {
      return "bg-rose-500/20 text-rose-300 border-rose-500/40";
    }
    if (u === "HIGH") {
      return "bg-amber-500/20 text-amber-300 border-amber-500/40";
    }
    if (u === "MEDIUM") {
      return "bg-cyan-500/20 text-cyan-300 border-cyan-500/40";
    }
    return "bg-slate-700/50 text-slate-300 border-slate-600";
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Top Navigation */}
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
              Operational Command Portal
            </span>
          </div>

          <div className="flex items-center gap-4">
            <div className="hidden sm:flex flex-col text-right">
              <span className="text-xs font-semibold text-white">{user?.full_name}</span>
              <span className="text-[11px] font-mono text-emerald-400">{user?.role}</span>
            </div>
            <button
              onClick={handleLogout}
              className="px-3.5 py-1.5 text-xs font-medium bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 rounded-lg transition cursor-pointer"
            >
              Sign Out
            </button>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Welcome & Role Context Header */}
        <div className="p-6 rounded-2xl bg-gradient-to-r from-slate-900 via-slate-900 to-emerald-950/30 border border-slate-800 mb-6">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-500/20 text-emerald-400 mb-2 border border-emerald-500/30">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-ping"></span>
                Phase 9 Live Operational Dashboard
              </div>
              <h1 className="text-2xl font-extrabold text-white tracking-tight">
                Health Operations Overview
              </h1>
              <p className="mt-1 text-xs text-slate-400">
                Logged in as <strong className="text-emerald-400">{user?.full_name}</strong> ({user?.role})
              </p>
            </div>

            {/* Multi-Perspective Tab Switcher (Visible to Admins / Medical Officers) */}
            {(isAdmin || isFacilityUser) && (
              <div className="flex items-center bg-slate-950 p-1 rounded-xl border border-slate-800">
                <button
                  onClick={() => setActiveTab("frontline")}
                  className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition cursor-pointer ${
                    activeTab === "frontline"
                      ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  Frontline Action
                </button>
                <button
                  onClick={() => setActiveTab("facility")}
                  className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition cursor-pointer ${
                    activeTab === "facility"
                      ? "bg-cyan-500/20 text-cyan-400 border border-cyan-500/30"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  Facility Operations
                </button>
                {(isAdmin || isDistrictAdmin) && (
                  <button
                    onClick={() => setActiveTab("district")}
                    className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition cursor-pointer ${
                      activeTab === "district"
                        ? "bg-indigo-500/20 text-indigo-400 border border-indigo-500/30"
                        : "text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    District Performance
                  </button>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Error State Callout */}
        {errorMessage && (
          <div className="p-4 mb-6 rounded-xl bg-rose-950/40 border border-rose-500/30 text-rose-300 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-xl">⚠️</span>
              <span className="text-sm font-medium">{errorMessage}</span>
            </div>
            <button
              onClick={() => setReloadKey((prev) => prev + 1)}
              className="px-3 py-1 text-xs bg-rose-500/20 hover:bg-rose-500/30 text-rose-200 rounded-md border border-rose-500/40 transition cursor-pointer"
            >
              Retry
            </button>
          </div>
        )}

        {/* Loading State Skeleton */}
        {isLoading && (
          <div className="space-y-6">
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
              {[...Array(6)].map((_, i) => (
                <div key={i} className="h-24 bg-slate-900/60 border border-slate-800 rounded-xl animate-pulse"></div>
              ))}
            </div>
            <div className="h-80 bg-slate-900/60 border border-slate-800 rounded-xl animate-pulse"></div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* TAB 1: FRONTLINE DASHBOARD                                                */}
        {/* ========================================================================= */}
        {!isLoading && activeTab === "frontline" && frontlineData && (
          <div className="space-y-6">
            {/* Urgent Alert Banner */}
            {frontlineData.urgent_care_requests > 0 && (
              <div className="p-4 rounded-xl bg-rose-950/30 border border-rose-500/30 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="h-8 w-8 rounded-lg bg-rose-500/20 text-rose-400 flex items-center justify-center font-bold text-base">
                    🚨
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-rose-200">
                      {frontlineData.urgent_care_requests} Urgent / Emergency Case(s) Active
                    </h3>
                    <p className="text-xs text-rose-400/80">
                      Priority action required in community queue. Immediate facility referral or transport coordination recommended.
                    </p>
                  </div>
                </div>
                <Link
                  href="/care-requests"
                  className="px-3 py-1.5 text-xs font-semibold bg-rose-500/20 hover:bg-rose-500/30 text-rose-200 border border-rose-500/40 rounded-lg transition"
                >
                  View Triage List &rarr;
                </Link>
              </div>
            )}

            {/* Quick Metrics Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
              <div className="p-4 rounded-xl bg-slate-900/70 border border-slate-800">
                <span className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold">Patients</span>
                <p className="text-2xl font-black text-white mt-1">{frontlineData.total_patients}</p>
                <span className="text-[10px] text-slate-500">Accessible registry</span>
              </div>

              <div className="p-4 rounded-xl bg-slate-900/70 border border-slate-800">
                <span className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold">Active Requests</span>
                <p className="text-2xl font-black text-teal-400 mt-1">{frontlineData.active_care_requests}</p>
                <span className="text-[10px] text-slate-500">Submitted / Triaged</span>
              </div>

              <div className="p-4 rounded-xl bg-slate-900/70 border border-slate-800">
                <span className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold">Action Queue</span>
                <p className="text-2xl font-black text-amber-400 mt-1">{frontlineData.action_required_count}</p>
                <span className="text-[10px] text-slate-500">Needs attention</span>
              </div>

              <div className="p-4 rounded-xl bg-slate-900/70 border border-slate-800">
                <span className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold">Pending Referral</span>
                <p className="text-2xl font-black text-cyan-400 mt-1">{frontlineData.pending_referrals}</p>
                <span className="text-[10px] text-slate-500">Awaiting acceptance</span>
              </div>

              <div className="p-4 rounded-xl bg-slate-900/70 border border-slate-800">
                <span className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold">In Transit</span>
                <p className="text-2xl font-black text-indigo-400 mt-1">{frontlineData.in_transit_referrals}</p>
                <span className="text-[10px] text-slate-500">Patient departed</span>
              </div>

              <div className="p-4 rounded-xl bg-slate-900/70 border border-slate-800">
                <span className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold">Completed</span>
                <p className="text-2xl font-black text-emerald-400 mt-1">{frontlineData.completed_referrals}</p>
                <span className="text-[10px] text-slate-500">Service finished</span>
              </div>
            </div>

            {/* Frontline Action Queue */}
            <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h2 className="text-base font-bold text-white flex items-center gap-2">
                    <span>⚡</span> Frontline Action & Attention Queue
                  </h2>
                  <p className="text-xs text-slate-400">
                    Prioritized by clinical urgency and pending wait time. Click any item to take direct operational action.
                  </p>
                </div>
                <span className="px-2.5 py-1 text-xs font-mono bg-slate-800 text-slate-300 rounded-md border border-slate-700">
                  {frontlineData.action_queue.length} Pending Actions
                </span>
              </div>

              {frontlineData.action_queue.length === 0 ? (
                <div className="text-center py-12 text-slate-500">
                  <span className="text-3xl block mb-2">🎉</span>
                  <p className="text-sm">Action queue is completely clear! No pending tasks require attention.</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-950/60 text-slate-400 uppercase tracking-wider border-b border-slate-800">
                      <tr>
                        <th className="py-3 px-3">Urgency</th>
                        <th className="py-3 px-3">Patient</th>
                        <th className="py-3 px-3">Required Action</th>
                        <th className="py-3 px-3">Context / Facility</th>
                        <th className="py-3 px-3">Elapsed Time</th>
                        <th className="py-3 px-3 text-right">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60">
                      {frontlineData.action_queue.map((item) => (
                        <tr key={`${item.item_type}-${item.id}`} className="hover:bg-slate-800/30 transition">
                          <td className="py-3 px-3">
                            <span
                              className={`inline-block px-2 py-0.5 rounded font-mono text-[10px] font-bold border ${getUrgencyBadge(
                                item.urgency
                              )}`}
                            >
                              {item.urgency}
                            </span>
                          </td>
                          <td className="py-3 px-3">
                            <div className="font-semibold text-white">{item.patient_name}</div>
                            <div className="font-mono text-[10px] text-slate-400">{item.patient_code}</div>
                          </td>
                          <td className="py-3 px-3">
                            <div className="font-medium text-amber-300 flex items-center gap-1.5">
                              <span className="h-1.5 w-1.5 rounded-full bg-amber-400 animate-pulse"></span>
                              {item.action_required}
                            </div>
                            <div className="text-[10px] text-slate-500 font-mono">
                              Type: {item.item_type} ({item.status})
                            </div>
                          </td>
                          <td className="py-3 px-3 text-slate-300">
                            {item.facility_name || item.village_name || "Community Triage"}
                          </td>
                          <td className="py-3 px-3 font-mono text-slate-400">
                            {item.elapsed_hours > 24
                              ? `${Math.floor(item.elapsed_hours / 24)}d ${Math.round(item.elapsed_hours % 24)}h`
                              : `${item.elapsed_hours} hrs`}
                          </td>
                          <td className="py-3 px-3 text-right">
                            <Link
                              href={item.deep_link}
                              className="px-2.5 py-1 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 rounded-md font-semibold text-[11px] transition"
                            >
                              Open &rarr;
                            </Link>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            {/* Recent Activity Stream */}
            {frontlineData.recent_activity.length > 0 && (
              <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-6">
                <h2 className="text-sm font-bold text-white uppercase tracking-wider mb-4 flex items-center gap-2">
                  <span>📜</span> Recent Referral Milestones & Activity
                </h2>
                <div className="space-y-3">
                  {frontlineData.recent_activity.map((act) => (
                    <div
                      key={act.id}
                      className="p-3 rounded-lg bg-slate-950/50 border border-slate-800/80 flex items-center justify-between"
                    >
                      <div className="flex items-center gap-3">
                        <div className="h-2 w-2 rounded-full bg-emerald-400"></div>
                        <div>
                          <span className="font-semibold text-white text-xs">{act.patient_name}</span>
                          <span className="text-[10px] text-slate-400 font-mono ml-2">({act.patient_code})</span>
                          <p className="text-xs text-slate-300 mt-0.5">{act.action_description}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <span className="text-[10px] font-mono text-slate-500">
                          {new Date(act.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                        </span>
                        <div>
                          <Link href={act.deep_link} className="text-[11px] text-emerald-400 hover:underline">
                            View
                          </Link>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* ========================================================================= */}
        {/* TAB 2: FACILITY DASHBOARD                                                 */}
        {/* ========================================================================= */}
        {!isLoading && activeTab === "facility" && facilityData && (
          <div className="space-y-6">
            {/* Facility Header Card */}
            <div className="p-6 rounded-xl bg-slate-900/70 border border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div>
                <div className="flex items-center gap-2">
                  <span className="px-2.5 py-0.5 rounded text-[11px] font-mono font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                    Tier {facilityData.tier_level} • {facilityData.facility_type}
                  </span>
                  <span className="px-2 py-0.5 rounded text-[11px] font-medium bg-emerald-500/20 text-emerald-400">
                    {facilityData.operational_status}
                  </span>
                </div>
                <h2 className="text-xl font-extrabold text-white mt-1">{facilityData.facility_name}</h2>
                <p className="text-xs text-slate-400">
                  {facilityData.district}, {facilityData.state} • Operational Referral Intake & Live Ward Capacity
                </p>
              </div>

              <div className="flex items-center gap-3">
                <Link
                  href="/referrals"
                  className="px-3.5 py-2 text-xs font-semibold bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 border border-emerald-500/40 rounded-lg transition"
                >
                  Manage Inbound Referrals &rarr;
                </Link>
              </div>
            </div>

            {/* Live Bed & ICU Capacity Gauges */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="p-5 rounded-xl bg-slate-900/70 border border-slate-800">
                <div className="flex justify-between items-center text-xs text-slate-400 mb-2">
                  <span className="font-semibold uppercase tracking-wider">Total Bed Occupancy</span>
                  <span className="font-mono font-bold text-white">{facilityData.bed_utilization_percent}%</span>
                </div>
                <div className="w-full h-3 bg-slate-800 rounded-full overflow-hidden mb-2">
                  <div
                    className={`h-full transition-all duration-500 ${
                      facilityData.bed_utilization_percent > 85
                        ? "bg-rose-500"
                        : facilityData.bed_utilization_percent > 65
                        ? "bg-amber-500"
                        : "bg-emerald-500"
                    }`}
                    style={{ width: `${Math.min(100, facilityData.bed_utilization_percent)}%` }}
                  ></div>
                </div>
                <div className="flex justify-between text-xs text-slate-400">
                  <span>Available: <strong className="text-emerald-400">{facilityData.available_beds}</strong></span>
                  <span>Total: <strong className="text-white">{facilityData.total_beds}</strong></span>
                </div>
              </div>

              <div className="p-5 rounded-xl bg-slate-900/70 border border-slate-800">
                <div className="flex justify-between items-center text-xs text-slate-400 mb-2">
                  <span className="font-semibold uppercase tracking-wider">ICU Bed Occupancy</span>
                  <span className="font-mono font-bold text-white">{facilityData.icu_utilization_percent}%</span>
                </div>
                <div className="w-full h-3 bg-slate-800 rounded-full overflow-hidden mb-2">
                  <div
                    className={`h-full transition-all duration-500 ${
                      facilityData.icu_utilization_percent > 85
                        ? "bg-rose-500"
                        : facilityData.icu_utilization_percent > 65
                        ? "bg-amber-500"
                        : "bg-cyan-500"
                    }`}
                    style={{ width: `${Math.min(100, facilityData.icu_utilization_percent)}%` }}
                  ></div>
                </div>
                <div className="flex justify-between text-xs text-slate-400">
                  <span>Available: <strong className="text-cyan-400">{facilityData.icu_beds_available}</strong></span>
                  <span>Total: <strong className="text-white">{facilityData.icu_beds_total}</strong></span>
                </div>
              </div>

              <div className="p-5 rounded-xl bg-slate-900/70 border border-slate-800">
                <span className="text-xs uppercase tracking-wider text-slate-400 font-semibold">Oxygen Beds</span>
                <p className="text-2xl font-black text-teal-400 mt-1">
                  {facilityData.available_oxygen_beds}{" "}
                  <span className="text-xs font-normal text-slate-500">/ {facilityData.oxygen_supported_beds} avail</span>
                </p>
                <span className="text-[10px] text-slate-500">Oxygen-supported capacity</span>
              </div>

              <div className="p-5 rounded-xl bg-slate-900/70 border border-slate-800">
                <span className="text-xs uppercase tracking-wider text-slate-400 font-semibold">Ventilators</span>
                <p className="text-2xl font-black text-indigo-400 mt-1">
                  {facilityData.available_ventilators}{" "}
                  <span className="text-xs font-normal text-slate-500">/ {facilityData.ventilators_count} avail</span>
                </p>
                <span className="text-[10px] text-slate-500">Critical care units</span>
              </div>
            </div>

            {/* Inbound Referral Status Summary Chips */}
            <div className="p-5 rounded-xl bg-slate-900/70 border border-slate-800">
              <h3 className="text-xs uppercase tracking-wider text-slate-400 font-bold mb-3">
                Inbound Referral Status Pipeline ({facilityData.active_referrals_count} active)
              </h3>
              <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3">
                <div className="p-3 bg-slate-950/60 border border-amber-500/30 rounded-lg text-center">
                  <span className="text-[10px] uppercase text-slate-400 font-semibold block">Decision Pending</span>
                  <span className="text-xl font-black text-amber-400">{facilityData.status_breakdown.pending_acceptance}</span>
                </div>
                <div className="p-3 bg-slate-950/60 border border-cyan-500/30 rounded-lg text-center">
                  <span className="text-[10px] uppercase text-slate-400 font-semibold block">Accepted</span>
                  <span className="text-xl font-black text-cyan-400">{facilityData.status_breakdown.accepted}</span>
                </div>
                <div className="p-3 bg-slate-950/60 border border-slate-800 rounded-lg text-center">
                  <span className="text-[10px] uppercase text-slate-400 font-semibold block">Notified</span>
                  <span className="text-xl font-black text-slate-300">{facilityData.status_breakdown.patient_notified}</span>
                </div>
                <div className="p-3 bg-slate-950/60 border border-indigo-500/30 rounded-lg text-center">
                  <span className="text-[10px] uppercase text-slate-400 font-semibold block">In Transit</span>
                  <span className="text-xl font-black text-indigo-400">{facilityData.status_breakdown.in_transit}</span>
                </div>
                <div className="p-3 bg-slate-950/60 border border-teal-500/30 rounded-lg text-center">
                  <span className="text-[10px] uppercase text-slate-400 font-semibold block">Arrived</span>
                  <span className="text-xl font-black text-teal-400">{facilityData.status_breakdown.arrived}</span>
                </div>
                <div className="p-3 bg-slate-950/60 border border-blue-500/30 rounded-lg text-center">
                  <span className="text-[10px] uppercase text-slate-400 font-semibold block">In Service</span>
                  <span className="text-xl font-black text-blue-400">{facilityData.status_breakdown.in_service}</span>
                </div>
                <div className="p-3 bg-slate-950/60 border border-emerald-500/30 rounded-lg text-center">
                  <span className="text-[10px] uppercase text-slate-400 font-semibold block">Completed</span>
                  <span className="text-xl font-black text-emerald-400">{facilityData.status_breakdown.completed}</span>
                </div>
                <div className="p-3 bg-slate-950/60 border border-rose-500/30 rounded-lg text-center">
                  <span className="text-[10px] uppercase text-slate-400 font-semibold block">Rejected</span>
                  <span className="text-xl font-black text-rose-400">{facilityData.status_breakdown.rejected}</span>
                </div>
              </div>
            </div>

            {/* Operational Referral Queue */}
            <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-6">
              <h2 className="text-base font-bold text-white mb-4 flex items-center gap-2">
                <span>📋</span> Facility Inbound Operational Queue
              </h2>

              {facilityData.operational_queue.length === 0 ? (
                <div className="text-center py-8 text-slate-500 text-xs">
                  No active inbound referrals currently queued for this facility.
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-950/60 text-slate-400 uppercase tracking-wider border-b border-slate-800">
                      <tr>
                        <th className="py-3 px-3">Priority</th>
                        <th className="py-3 px-3">Status</th>
                        <th className="py-3 px-3">Patient</th>
                        <th className="py-3 px-3">Origin / Transit</th>
                        <th className="py-3 px-3">Elapsed</th>
                        <th className="py-3 px-3 text-right">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60">
                      {facilityData.operational_queue.map((ref) => (
                        <tr key={ref.referral_id} className="hover:bg-slate-800/30 transition">
                          <td className="py-3 px-3">
                            <span className={`px-2 py-0.5 rounded font-mono font-bold text-[10px] border ${getUrgencyBadge(ref.priority)}`}>
                              {ref.priority}
                            </span>
                          </td>
                          <td className="py-3 px-3">
                            <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-800 text-slate-200 border border-slate-700">
                              {ref.status}
                            </span>
                          </td>
                          <td className="py-3 px-3">
                            <div className="font-semibold text-white">{ref.patient_name}</div>
                            <div className="font-mono text-[10px] text-slate-400">{ref.patient_code}</div>
                          </td>
                          <td className="py-3 px-3 text-slate-300">
                            <div>{ref.origin_facility_name}</div>
                            <div className="text-[10px] text-slate-500 font-mono">Mode: {ref.transport_mode || "Standard"}</div>
                          </td>
                          <td className="py-3 px-3 font-mono text-slate-400">{ref.elapsed_hours}h</td>
                          <td className="py-3 px-3 text-right">
                            <Link
                              href={ref.deep_link}
                              className="px-2.5 py-1 bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 rounded-md font-semibold text-[11px] transition"
                            >
                              Open Referral &rarr;
                            </Link>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            {/* Department Capabilities & Load Table */}
            <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-base font-bold text-white flex items-center gap-2">
                  <span>🩺</span> Clinical Department Capabilities & Live Load
                </h2>
                <span className="text-xs text-slate-400 font-mono">
                  {facilityData.available_capabilities_count} of {facilityData.total_capabilities_count} Available
                </span>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-950/60 text-slate-400 uppercase tracking-wider border-b border-slate-800">
                    <tr>
                      <th className="py-3 px-3">Service Name</th>
                      <th className="py-3 px-3">Category</th>
                      <th className="py-3 px-3">Status</th>
                      <th className="py-3 px-3">Workload / Capacity</th>
                      <th className="py-3 px-3">Utilization</th>
                      <th className="py-3 px-3">Specialist</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {facilityData.capabilities.map((cap) => (
                      <tr key={cap.capability_id} className="hover:bg-slate-800/30 transition">
                        <td className="py-3 px-3 font-semibold text-white">{cap.service_name}</td>
                        <td className="py-3 px-3 text-slate-400">{cap.service_category}</td>
                        <td className="py-3 px-3">
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                              cap.availability_status === "AVAILABLE"
                                ? "bg-emerald-500/20 text-emerald-400"
                                : cap.availability_status === "LIMITED"
                                ? "bg-amber-500/20 text-amber-400"
                                : "bg-rose-500/20 text-rose-400"
                            }`}
                          >
                            {cap.availability_status}
                          </span>
                        </td>
                        <td className="py-3 px-3 font-mono text-slate-300">
                          {cap.current_load} / {cap.capacity} patients
                        </td>
                        <td className="py-3 px-3">
                          <div className="flex items-center gap-2">
                            <div className="w-16 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                              <div
                                className="h-full bg-cyan-400"
                                style={{ width: `${Math.min(100, cap.utilization_percent)}%` }}
                              ></div>
                            </div>
                            <span className="font-mono text-[10px] text-slate-400">{cap.utilization_percent}%</span>
                          </div>
                        </td>
                        <td className="py-3 px-3">
                          {cap.specialist_required ? (
                            <span className="text-[10px] text-emerald-400 font-semibold">Specialist Req</span>
                          ) : (
                            <span className="text-[10px] text-slate-500">General Staff</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* TAB 3: DISTRICT DASHBOARD                                                 */}
        {/* ========================================================================= */}
        {!isLoading && activeTab === "district" && districtData && (
          <div className="space-y-6">
            {/* Filter Bar */}
            <div className="p-4 rounded-xl bg-slate-900/70 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <h2 className="text-base font-bold text-white">
                  District Operations: <span className="text-indigo-400">{districtData.district_name}</span>
                </h2>
                <p className="text-xs text-slate-400">
                  Aggregated health access analytics, referral funnels, and facility throughput
                </p>
              </div>

              {/* Time Range Selector */}
              <div className="flex items-center bg-slate-950 p-1 rounded-lg border border-slate-800">
                {[
                  { key: "all", label: "All Time" },
                  { key: "today", label: "Today" },
                  { key: "7d", label: "7 Days" },
                  { key: "30d", label: "30 Days" },
                ].map((item) => (
                  <button
                    key={item.key}
                    onClick={() => setTimeRange(item.key)}
                    className={`px-3 py-1 text-xs font-semibold rounded-md transition cursor-pointer ${
                      timeRange === item.key
                        ? "bg-indigo-500/20 text-indigo-300 border border-indigo-500/40"
                        : "text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    {item.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Core KPI Cards Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Care Completion Rate KPI Gauge */}
              <div className="p-5 rounded-xl bg-gradient-to-br from-slate-900 to-indigo-950/40 border border-indigo-500/30 flex items-center justify-between">
                <div>
                  <span className="text-xs uppercase tracking-wider text-indigo-300 font-bold">
                    Care Completion Rate
                  </span>
                  <p className="text-3xl font-black text-white mt-1">
                    {districtData.care_completion_rate}%
                  </p>
                  <span className="text-[10px] text-indigo-400/80">Primary RAHAT KPI</span>
                </div>
                {/* SVG Progress Ring */}
                <div className="relative h-16 w-16 flex items-center justify-center">
                  <svg className="h-16 w-16 -rotate-90" viewBox="0 0 36 36">
                    <path
                      className="text-slate-800"
                      strokeWidth="3.5"
                      stroke="currentColor"
                      fill="none"
                      d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                    />
                    <path
                      className="text-indigo-400"
                      strokeDasharray={`${districtData.care_completion_rate}, 100`}
                      strokeWidth="3.5"
                      strokeLinecap="round"
                      stroke="currentColor"
                      fill="none"
                      d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                    />
                  </svg>
                  <span className="absolute text-[11px] font-bold text-white">
                    {Math.round(districtData.care_completion_rate)}%
                  </span>
                </div>
              </div>

              <div className="p-5 rounded-xl bg-slate-900/70 border border-slate-800">
                <span className="text-xs uppercase tracking-wider text-slate-400 font-semibold">Total Referrals</span>
                <p className="text-3xl font-black text-white mt-1">{districtData.total_referrals}</p>
                <div className="flex gap-2 mt-1 text-[11px]">
                  <span className="text-emerald-400">{districtData.completed_referrals} Completed</span>
                  <span className="text-slate-500">•</span>
                  <span className="text-amber-400">{districtData.active_referrals} Active</span>
                </div>
              </div>

              <div className="p-5 rounded-xl bg-slate-900/70 border border-slate-800">
                <span className="text-xs uppercase tracking-wider text-slate-400 font-semibold">Avg Completion Time</span>
                <p className="text-3xl font-black text-teal-400 mt-1">
                  {districtData.avg_referral_completion_hours != null
                    ? `${districtData.avg_referral_completion_hours} hrs`
                    : "N/A"}
                </p>
                <span className="text-[10px] text-slate-500">Initiation to service finish</span>
              </div>

              <div className="p-5 rounded-xl bg-slate-900/70 border border-slate-800">
                <span className="text-xs uppercase tracking-wider text-slate-400 font-semibold">Urgent & Emergency</span>
                <p className="text-3xl font-black text-rose-400 mt-1">{districtData.urgent_emergency_count}</p>
                <span className="text-[10px] text-slate-500">Critical cases routed</span>
              </div>
            </div>

            {/* Referral Lifecycle Funnel Visualization */}
            {funnelData && (
              <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-6">
                <div className="flex items-center justify-between mb-6">
                  <div>
                    <h3 className="text-base font-bold text-white flex items-center gap-2">
                      <span>📉</span> Referral Lifecycle Funnel & Milestone Progression
                    </h3>
                    <p className="text-xs text-slate-400">
                      Sequential progression from initial dispatch to service completion. Identifies transit drop-offs.
                    </p>
                  </div>
                  <div className="flex items-center gap-3 text-xs font-mono">
                    <span className="text-rose-400">Rejected: {funnelData.side_branches.REJECTED || 0}</span>
                    <span className="text-amber-400">Rerouted: {funnelData.side_branches.REROUTED || 0}</span>
                  </div>
                </div>

                <div className="space-y-4">
                  {funnelData.stages.map((stage, idx) => (
                    <div key={stage.stage_key} className="space-y-1">
                      <div className="flex justify-between items-center text-xs">
                        <span className="font-semibold text-slate-200">
                          {idx + 1}. {stage.stage_name}
                        </span>
                        <div className="flex items-center gap-3 font-mono text-xs">
                          <span className="text-white font-bold">{stage.count} cases</span>
                          <span className="text-slate-400">({stage.percentage_of_total}%)</span>
                          {stage.drop_off_count > 0 && (
                            <span className="text-rose-400 text-[11px]">
                              -{stage.drop_off_count} ({stage.drop_off_rate}% drop)
                            </span>
                          )}
                        </div>
                      </div>
                      <div className="w-full h-3 bg-slate-950 rounded-full overflow-hidden border border-slate-800">
                        <div
                          className="h-full bg-gradient-to-r from-indigo-500 to-teal-400 transition-all duration-500 rounded-full"
                          style={{ width: `${Math.max(2, stage.percentage_of_total)}%` }}
                        ></div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Category Breakdown & Distribution */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Care Categories Chart */}
              <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-6">
                <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-4">
                  Care Requests by Category
                </h3>
                <div className="space-y-3">
                  {Object.entries(districtData.care_requests_by_category).length === 0 ? (
                    <div className="text-center py-6 text-slate-500 text-xs">No care requests in selected period.</div>
                  ) : (
                    Object.entries(districtData.care_requests_by_category).map(([cat, cnt]) => {
                      const total = districtData.total_care_requests || 1;
                      const pct = Math.round((cnt / total) * 100);
                      return (
                        <div key={cat} className="space-y-1">
                          <div className="flex justify-between text-xs">
                            <span className="text-slate-300 font-medium">{cat}</span>
                            <span className="font-mono text-slate-400">{cnt} ({pct}%)</span>
                          </div>
                          <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
                            <div className="h-full bg-teal-400 rounded-full" style={{ width: `${pct}%` }}></div>
                          </div>
                        </div>
                      );
                    })
                  )}
                </div>
              </div>

              {/* Referral Status Summary */}
              <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-6">
                <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-4">
                  Referral Status Distribution
                </h3>
                <div className="space-y-3">
                  {Object.entries(districtData.referrals_by_status).length === 0 ? (
                    <div className="text-center py-6 text-slate-500 text-xs">No referrals in selected period.</div>
                  ) : (
                    Object.entries(districtData.referrals_by_status).map(([st, cnt]) => {
                      const total = districtData.total_referrals || 1;
                      const pct = Math.round((cnt / total) * 100);
                      return (
                        <div key={st} className="space-y-1">
                          <div className="flex justify-between text-xs">
                            <span className="text-slate-300 font-medium">{st}</span>
                            <span className="font-mono text-slate-400">{cnt} ({pct}%)</span>
                          </div>
                          <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
                            <div className="h-full bg-indigo-400 rounded-full" style={{ width: `${pct}%` }}></div>
                          </div>
                        </div>
                      );
                    })
                  )}
                </div>
              </div>
            </div>

            {/* Facility Operational Performance Summary Table */}
            <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-6">
              <h3 className="text-base font-bold text-white mb-4 flex items-center gap-2">
                <span>🏥</span> District Facility Operational Throughput
              </h3>

              {districtData.facility_performance.length === 0 ? (
                <div className="text-center py-6 text-slate-500 text-xs">No facilities found for this district.</div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-950/60 text-slate-400 uppercase tracking-wider border-b border-slate-800">
                      <tr>
                        <th className="py-3 px-3">Facility</th>
                        <th className="py-3 px-3">Type / Tier</th>
                        <th className="py-3 px-3">Received</th>
                        <th className="py-3 px-3">Accepted</th>
                        <th className="py-3 px-3">Completed</th>
                        <th className="py-3 px-3">Acceptance Rate</th>
                        <th className="py-3 px-3">Avg Time</th>
                        <th className="py-3 px-3">Bed Util.</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60">
                      {districtData.facility_performance.map((fac) => (
                        <tr key={fac.facility_id} className="hover:bg-slate-800/30 transition">
                          <td className="py-3 px-3 font-semibold text-white">{fac.facility_name}</td>
                          <td className="py-3 px-3 text-slate-400">
                            {fac.facility_type} (T{fac.tier_level})
                          </td>
                          <td className="py-3 px-3 font-mono font-bold text-white">{fac.referrals_received}</td>
                          <td className="py-3 px-3 font-mono text-cyan-400">{fac.referrals_accepted}</td>
                          <td className="py-3 px-3 font-mono text-emerald-400">{fac.referrals_completed}</td>
                          <td className="py-3 px-3 font-mono font-semibold text-indigo-300">{fac.acceptance_rate}%</td>
                          <td className="py-3 px-3 font-mono text-slate-400">
                            {fac.avg_completion_hours != null ? `${fac.avg_completion_hours}h` : "-"}
                          </td>
                          <td className="py-3 px-3">
                            <span
                              className={`px-2 py-0.5 rounded font-mono text-[10px] font-bold ${
                                fac.bed_utilization_percent > 80
                                  ? "bg-rose-500/20 text-rose-300"
                                  : "bg-emerald-500/20 text-emerald-300"
                              }`}
                            >
                              {fac.bed_utilization_percent}%
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Core RAHAT Modules Navigation Grid */}
        <div className="mt-10 pt-8 border-t border-slate-800/80">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-4">
            Core Workflow Navigation
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <Link
              href="/patients"
              className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-emerald-500/40 transition flex items-center justify-between group"
            >
              <div>
                <h4 className="text-xs font-bold text-white group-hover:text-emerald-400 transition">
                  👥 Patient Registry
                </h4>
                <p className="text-[11px] text-slate-400 mt-0.5">Search & register citizens</p>
              </div>
              <span className="text-slate-600 group-hover:text-emerald-400 text-xs font-bold">&rarr;</span>
            </Link>

            <Link
              href="/care-requests"
              className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-teal-500/40 transition flex items-center justify-between group"
            >
              <div>
                <h4 className="text-xs font-bold text-white group-hover:text-teal-400 transition">
                  🩺 Care Requests
                </h4>
                <p className="text-[11px] text-slate-400 mt-0.5">Triage & recommendation</p>
              </div>
              <span className="text-slate-600 group-hover:text-teal-400 text-xs font-bold">&rarr;</span>
            </Link>

            <Link
              href="/facilities"
              className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-cyan-500/40 transition flex items-center justify-between group"
            >
              <div>
                <h4 className="text-xs font-bold text-white group-hover:text-cyan-400 transition">
                  🏥 Health Facilities
                </h4>
                <p className="text-[11px] text-slate-400 mt-0.5">Bed tracking & capabilities</p>
              </div>
              <span className="text-slate-600 group-hover:text-cyan-400 text-xs font-bold">&rarr;</span>
            </Link>

            <Link
              href="/referrals"
              className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-indigo-500/40 transition flex items-center justify-between group"
            >
              <div>
                <h4 className="text-xs font-bold text-white group-hover:text-indigo-400 transition">
                  🚑 Referral Tracking
                </h4>
                <p className="text-[11px] text-slate-400 mt-0.5">Transit & lifecycle stages</p>
              </div>
              <span className="text-slate-600 group-hover:text-indigo-400 text-xs font-bold">&rarr;</span>
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

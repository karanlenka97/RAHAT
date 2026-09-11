"use client";

import React, { useState, useEffect, use } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import {
  getReferral,
  getReferralEvents,
  acceptReferral,
  rejectReferral,
  notifyPatient,
  departPatient,
  arrivePatient,
  startService,
  completeService,
  backRefer,
  rerouteReferral,
} from "@/lib/referralApi";
import { getFacilities } from "@/lib/facilityApi";
import { Referral, ReferralEvent, RejectionReason } from "@/types/referral";
import { Facility } from "@/types/facility";
import { ApiError } from "@/lib/api";

const REJECTION_REASONS: { value: RejectionReason; label: string }[] = [
  { value: "SERVICE_UNAVAILABLE", label: "Service / Department Unavailable" },
  { value: "CAPACITY_UNAVAILABLE", label: "No Available Beds / Capacity Full" },
  { value: "SPECIALIST_UNAVAILABLE", label: "Required Specialist Not on Duty" },
  { value: "FACILITY_CLOSED", label: "Facility Temporarily Closed / Maintenance" },
  { value: "OTHER", label: "Other Administrative / Clinical Reason" },
];

const STAGES = [
  { key: "PENDING_ACCEPTANCE", label: "1. Queued" },
  { key: "ACCEPTED", label: "2. Accepted" },
  { key: "PATIENT_NOTIFIED", label: "3. Notified" },
  { key: "DEPARTED", label: "4. In Transit" },
  { key: "ARRIVED", label: "5. Arrived" },
  { key: "IN_SERVICE", label: "6. In Service" },
  { key: "COMPLETED", label: "7. Completed" },
  { key: "BACK_REFERRED", label: "8. Back Referred" },
];

interface PageProps {
  params: Promise<{ id: string }>;
}

function ReferralDetailContent({ referralId }: { referralId: string }) {
  const { user, token, logout } = useAuth();
  const router = useRouter();

  const [referral, setReferral] = useState<Referral | null>(null);
  const [events, setEvents] = useState<ReferralEvent[]>([]);
  const [facilities, setFacilities] = useState<Facility[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState<number>(0);

  // Modals & Action States
  const [isRejectOpen, setIsRejectOpen] = useState<boolean>(false);
  const [isDepartOpen, setIsDepartOpen] = useState<boolean>(false);
  const [isCompleteOpen, setIsCompleteOpen] = useState<boolean>(false);
  const [isBackReferOpen, setIsBackReferOpen] = useState<boolean>(false);
  const [isRerouteOpen, setIsRerouteOpen] = useState<boolean>(false);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [successBanner, setSuccessBanner] = useState<string | null>(null);

  // Form Inputs
  const [rejectReason, setRejectReason] = useState<string>("CAPACITY_UNAVAILABLE");
  const [rejectNotes, setRejectNotes] = useState<string>("");
  const [departTransport, setDepartTransport] = useState<string>("108_AMBULANCE");
  const [departMinutes, setDepartMinutes] = useState<number>(30);
  const [departNotes, setDepartNotes] = useState<string>("");
  const [completeSummary, setCompleteSummary] = useState<string>("");
  const [completeNotes, setCompleteNotes] = useState<string>("");
  const [backReferNotes, setBackReferNotes] = useState<string>("");
  const [rerouteFacilityId, setRerouteFacilityId] = useState<string>("");
  const [rerouteReason, setRerouteReason] = useState<string>("");

  useEffect(() => {
    let isMounted = true;

    async function loadData() {
      if (!token || !referralId) return;
      setIsLoading(true);
      setError(null);

      try {
        const [refData, eventData, facData] = await Promise.all([
          getReferral(referralId, token),
          getReferralEvents(referralId, token),
          getFacilities({ is_active: true, page_size: 50 }, token),
        ]);

        if (isMounted) {
          setReferral(refData);
          setEvents(eventData);
          setFacilities(facData.items);
        }
      } catch (err: unknown) {
        if (isMounted) {
          const msg =
            err instanceof ApiError
              ? err.message
              : err instanceof Error
              ? err.message
              : "Unable to load referral details.";
          setError(msg);
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    loadData();

    return () => {
      isMounted = false;
    };
  }, [referralId, token, reloadKey]);

  const handleLogout = async () => {
    await logout();
    router.push("/login");
  };

  // Action Handlers
  const handleAccept = async () => {
    if (!token || !referral) return;
    setIsSubmitting(true);
    setActionError(null);
    try {
      await acceptReferral(referral.id, { notes: "Accepted by receiving facility." }, token);
      setSuccessBanner("Referral accepted successfully.");
      setReloadKey((k) => k + 1);
    } catch (err: unknown) {
      const msg = err instanceof ApiError ? err.message : "Failed to accept referral.";
      setActionError(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRejectSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !referral) return;
    setIsSubmitting(true);
    setActionError(null);
    try {
      await rejectReferral(
        referral.id,
        { rejection_reason: rejectReason, rejection_notes: rejectNotes.trim() },
        token
      );
      setIsRejectOpen(false);
      setSuccessBanner("Referral marked as rejected.");
      setReloadKey((k) => k + 1);
    } catch (err: unknown) {
      const msg = err instanceof ApiError ? err.message : "Failed to reject referral.";
      setActionError(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleNotify = async () => {
    if (!token || !referral) return;
    setIsSubmitting(true);
    setActionError(null);
    try {
      await notifyPatient(
        referral.id,
        { notes: "Patient and escort briefed on facility arrival instructions." },
        token
      );
      setSuccessBanner("Patient notification recorded.");
      setReloadKey((k) => k + 1);
    } catch (err: unknown) {
      const msg = err instanceof ApiError ? err.message : "Failed to record notification.";
      setActionError(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDepartSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !referral) return;
    setIsSubmitting(true);
    setActionError(null);
    try {
      await departPatient(
        referral.id,
        {
          transport_mode: departTransport,
          estimated_transit_minutes: departMinutes,
          notes: departNotes.trim() || undefined,
        },
        token
      );
      setIsDepartOpen(false);
      setSuccessBanner("Patient departure and transit recorded.");
      setReloadKey((k) => k + 1);
    } catch (err: unknown) {
      const msg = err instanceof ApiError ? err.message : "Failed to record departure.";
      setActionError(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleArrive = async () => {
    if (!token || !referral) return;
    setIsSubmitting(true);
    setActionError(null);
    try {
      await arrivePatient(referral.id, { notes: "Patient arrived and checked in." }, token);
      setSuccessBanner("Patient arrival recorded.");
      setReloadKey((k) => k + 1);
    } catch (err: unknown) {
      const msg = err instanceof ApiError ? err.message : "Failed to record arrival.";
      setActionError(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleStartService = async () => {
    if (!token || !referral) return;
    setIsSubmitting(true);
    setActionError(null);
    try {
      await startService(
        referral.id,
        { notes: "Clinical evaluation / procedure started." },
        token
      );
      setSuccessBanner("Clinical service marked as in-progress.");
      setReloadKey((k) => k + 1);
    } catch (err: unknown) {
      const msg = err instanceof ApiError ? err.message : "Failed to start service.";
      setActionError(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCompleteSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !referral) return;
    setIsSubmitting(true);
    setActionError(null);
    try {
      await completeService(
        referral.id,
        {
          clinical_summary: completeSummary.trim() || undefined,
          notes: completeNotes.trim() || undefined,
        },
        token
      );
      setIsCompleteOpen(false);
      setSuccessBanner("Clinical care completed.");
      setReloadKey((k) => k + 1);
    } catch (err: unknown) {
      const msg = err instanceof ApiError ? err.message : "Failed to complete service.";
      setActionError(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleBackReferSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !referral) return;
    setIsSubmitting(true);
    setActionError(null);
    try {
      await backRefer(
        referral.id,
        { back_referral_notes: backReferNotes.trim() },
        token
      );
      setIsBackReferOpen(false);
      setSuccessBanner("Back-referral guidance issued.");
      setReloadKey((k) => k + 1);
    } catch (err: unknown) {
      const msg = err instanceof ApiError ? err.message : "Failed to issue back-referral.";
      setActionError(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRerouteSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !referral || !rerouteFacilityId) return;
    setIsSubmitting(true);
    setActionError(null);
    try {
      const childRef = await rerouteReferral(
        referral.id,
        {
          new_receiving_facility_id: rerouteFacilityId,
          reason: rerouteReason.trim() || undefined,
        },
        token
      );
      setIsRerouteOpen(false);
      setSuccessBanner("Referral successfully rerouted.");
      router.push(`/referrals/${childRef.id}`);
    } catch (err: unknown) {
      const msg = err instanceof ApiError ? err.message : "Failed to reroute referral.";
      setActionError(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const currentStageIndex = STAGES.findIndex((s) => s.key === referral?.status);

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
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        {/* Back Link & Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <Link
              href="/referrals"
              className="p-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-400 hover:text-white hover:bg-slate-800 transition text-xs"
            >
              ← Back to Referrals
            </Link>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl font-bold text-white font-mono">
                  {referral?.referral_code || "Referral Record"}
                </h1>
                {referral && (
                  <span className="text-xs font-mono px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
                    Urgency: {referral.urgency}
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Care Request: {referral?.care_request_number || "Linked Request"} • Destination: {referral?.receiving_facility_name}
              </p>
            </div>
          </div>

          {/* Refresh Action */}
          <button
            onClick={() => setReloadKey((k) => k + 1)}
            disabled={isLoading}
            className="self-start sm:self-auto px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-400 hover:text-white hover:bg-slate-800 text-xs font-medium transition"
          >
            ↻ Refresh
          </button>
        </div>

        {/* Notifications & Action Errors */}
        {successBanner && (
          <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-xs text-emerald-300 flex items-center justify-between">
            <span>✓ {successBanner}</span>
            <button onClick={() => setSuccessBanner(null)} className="text-emerald-400 hover:text-white">✕</button>
          </div>
        )}

        {actionError && (
          <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-xs text-rose-300 flex items-center justify-between">
            <span>✕ {actionError}</span>
            <button onClick={() => setActionError(null)} className="text-rose-400 hover:text-white">✕</button>
          </div>
        )}

        {/* Loading State */}
        {isLoading && (
          <div className="animate-pulse space-y-4">
            <div className="h-24 bg-slate-900 rounded-2xl"></div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="h-64 bg-slate-900 rounded-2xl"></div>
              <div className="h-64 bg-slate-900 rounded-2xl"></div>
            </div>
          </div>
        )}

        {/* Error State */}
        {!isLoading && error && (
          <div className="p-6 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-xs text-rose-400">
            <strong>Error:</strong> {error}
          </div>
        )}

        {!isLoading && referral && (
          <div className="space-y-6">
            {/* Stage Progress Stepper */}
            <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-xl">
              <div className="flex items-center justify-between mb-4 pb-2 border-b border-slate-800">
                <span className="text-xs uppercase tracking-wider font-bold text-slate-400">
                  Referral Lifecycle Progression
                </span>
                <span className="text-xs font-mono text-emerald-400">
                  Status: {referral.status}
                </span>
              </div>

              {referral.status === "REJECTED" ? (
                <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-500/30 text-xs text-rose-300 space-y-1">
                  <div className="font-bold text-rose-200">
                    ✕ Referral Rejected by Facility: {referral.rejection_reason}
                  </div>
                  {referral.rejection_notes && (
                    <div className="text-rose-400 italic">Notes: {referral.rejection_notes}</div>
                  )}
                  <div className="pt-2 text-slate-400">
                    You can reroute this referral to an alternative capable facility below.
                  </div>
                </div>
              ) : referral.status === "REROUTED" ? (
                <div className="p-4 rounded-xl bg-orange-950/40 border border-orange-500/30 text-xs text-orange-300">
                  <div className="font-bold text-orange-200">
                    ➔ Referral Rerouted to Alternative Facility
                  </div>
                  <div className="text-orange-400 mt-1">
                    This historical referral has been superseded by a new active child referral.
                  </div>
                </div>
              ) : (
                <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2">
                  {STAGES.map((st, idx) => {
                    const isDone = currentStageIndex >= idx;
                    const isCurrent = currentStageIndex === idx;
                    return (
                      <div
                        key={st.key}
                        className={`p-3 rounded-xl border text-center transition ${
                          isCurrent
                            ? "bg-emerald-500/20 border-emerald-500 text-emerald-300 shadow-md shadow-emerald-950/30"
                            : isDone
                            ? "bg-slate-900 border-slate-700 text-slate-300"
                            : "bg-slate-950/40 border-slate-900 text-slate-600"
                        }`}
                      >
                        <div className="text-[11px] font-semibold">{st.label}</div>
                        <div className="text-[10px] mt-1 font-mono">
                          {isCurrent ? "Active" : isDone ? "✓ Done" : "Pending"}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Contextual Action Bar */}
            <div className="bg-slate-900/80 border border-emerald-500/30 rounded-2xl p-6 shadow-xl flex flex-wrap items-center justify-between gap-4">
              <div>
                <h2 className="text-sm font-bold text-white flex items-center gap-2">
                  <span>Available Lifecycle Actions</span>
                  <span className="text-[11px] font-normal text-slate-400">
                    (Authorized for current stage & role)
                  </span>
                </h2>
                <p className="text-xs text-slate-400 mt-0.5">
                  Advance the patient referral along the care journey.
                </p>
              </div>

              <div className="flex flex-wrap items-center gap-3">
                {referral.status === "PENDING_ACCEPTANCE" && (
                  <>
                    <button
                      onClick={handleAccept}
                      disabled={isSubmitting}
                      className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-lg shadow-emerald-950/30 transition disabled:opacity-50"
                    >
                      ✓ Accept Referral
                    </button>
                    <button
                      onClick={() => setIsRejectOpen(true)}
                      disabled={isSubmitting}
                      className="px-4 py-2 rounded-xl bg-rose-900/50 hover:bg-rose-800 text-rose-200 text-xs font-semibold border border-rose-700/50 transition disabled:opacity-50"
                    >
                      ✕ Reject Referral
                    </button>
                  </>
                )}

                {referral.status === "ACCEPTED" && (
                  <button
                    onClick={handleNotify}
                    disabled={isSubmitting}
                    className="px-4 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold shadow-lg shadow-cyan-950/30 transition disabled:opacity-50"
                  >
                    📢 Mark Patient Notified
                  </button>
                )}

                {(referral.status === "PATIENT_NOTIFIED" || referral.status === "ACCEPTED") && (
                  <button
                    onClick={() => setIsDepartOpen(true)}
                    disabled={isSubmitting}
                    className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-lg shadow-indigo-950/30 transition disabled:opacity-50"
                  >
                    🚑 Mark Departed (In Transit)
                  </button>
                )}

                {referral.status === "DEPARTED" && (
                  <button
                    onClick={handleArrive}
                    disabled={isSubmitting}
                    className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow-lg shadow-blue-950/30 transition disabled:opacity-50"
                  >
                    🏥 Mark Arrived at Facility
                  </button>
                )}

                {referral.status === "ARRIVED" && (
                  <button
                    onClick={handleStartService}
                    disabled={isSubmitting}
                    className="px-4 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold shadow-lg shadow-purple-950/30 transition disabled:opacity-50"
                  >
                    🩺 Start Clinical Service
                  </button>
                )}

                {referral.status === "IN_SERVICE" && (
                  <button
                    onClick={() => setIsCompleteOpen(true)}
                    disabled={isSubmitting}
                    className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-lg shadow-emerald-950/30 transition disabled:opacity-50"
                  >
                    ✓ Complete Service
                  </button>
                )}

                {referral.status === "COMPLETED" && (
                  <button
                    onClick={() => setIsBackReferOpen(true)}
                    disabled={isSubmitting}
                    className="px-4 py-2 rounded-xl bg-violet-600 hover:bg-violet-500 text-white text-xs font-semibold shadow-lg shadow-violet-950/30 transition disabled:opacity-50"
                  >
                    ↺ Issue Back-Referral Instructions
                  </button>
                )}

                {referral.status === "REJECTED" && (
                  <button
                    onClick={() => setIsRerouteOpen(true)}
                    disabled={isSubmitting}
                    className="px-4 py-2 rounded-xl bg-orange-600 hover:bg-orange-500 text-white text-xs font-semibold shadow-lg shadow-orange-950/30 transition disabled:opacity-50"
                  >
                    ➔ Reroute to Alternative Facility
                  </button>
                )}
              </div>
            </div>

            {/* Referral Details Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Patient & Care Request Card */}
              <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-4">
                <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 pb-2 border-b border-slate-800">
                  Patient & Clinical Case
                </h2>

                <dl className="space-y-3 text-xs">
                  <div>
                    <dt className="text-slate-500">Patient</dt>
                    <dd className="font-semibold text-white mt-0.5">
                      {referral.patient_name || "Anonymous Patient"} ({referral.patient_gender}, {referral.patient_age} yrs)
                    </dd>
                    <dd className="font-mono text-slate-400 text-[11px]">
                      Code: {referral.patient_code} • Phone: {referral.patient_phone || "N/A"}
                    </dd>
                  </div>

                  <div>
                    <dt className="text-slate-500">Associated Village / Location</dt>
                    <dd className="text-slate-200 mt-0.5">
                      {referral.patient_village || "Community Area"}
                    </dd>
                  </div>

                  <div>
                    <dt className="text-slate-500">Linked Care Request</dt>
                    <dd className="mt-0.5">
                      <Link
                        href={`/care-requests/${referral.care_request_id}`}
                        className="font-mono text-emerald-400 hover:underline"
                      >
                        {referral.care_request_number || referral.care_request_id}
                      </Link>
                    </dd>
                    <dd className="text-slate-400 mt-0.5">
                      Category: {referral.care_category} • Service: {referral.required_service}
                    </dd>
                  </div>

                  <div>
                    <dt className="text-slate-500">Clinical Referral Reason / Notes</dt>
                    <dd className="text-slate-200 mt-0.5 bg-slate-950 p-3 rounded-xl border border-slate-800 leading-relaxed font-sans">
                      {referral.clinical_summary || referral.referral_reason || "None specified."}
                    </dd>
                  </div>

                  {referral.back_referral_notes && (
                    <div>
                      <dt className="text-purple-400 font-semibold">Back-Referral Primary Care Guidance</dt>
                      <dd className="text-purple-200 mt-0.5 bg-purple-950/30 p-3 rounded-xl border border-purple-500/30 leading-relaxed font-sans">
                        {referral.back_referral_notes}
                      </dd>
                    </div>
                  )}
                </dl>
              </div>

              {/* Inter-Facility & Transport Card */}
              <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-4">
                <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 pb-2 border-b border-slate-800">
                  Facilities & Transit Arrangement
                </h2>

                <dl className="space-y-3 text-xs">
                  <div>
                    <dt className="text-slate-500">Destination / Receiving Facility</dt>
                    <dd className="font-bold text-emerald-400 text-sm mt-0.5">
                      <Link href={`/facilities/${referral.receiving_facility_id}`} className="hover:underline">
                        {referral.receiving_facility_name}
                      </Link>
                    </dd>
                    <dd className="text-slate-400 text-[11px]">
                      Type: {referral.receiving_facility_type?.replace(/_/g, " ")}
                    </dd>
                  </div>

                  <div>
                    <dt className="text-slate-500">Origin / Source Facility</dt>
                    <dd className="text-slate-200 mt-0.5">
                      {referral.source_facility_name || "Field Community / Village Post"}
                    </dd>
                  </div>

                  <div>
                    <dt className="text-slate-500">Transport Mode & Transit Status</dt>
                    <dd className="text-slate-200 mt-0.5 flex items-center gap-2">
                      <span className="font-mono">{referral.transport_mode || "108_AMBULANCE"}</span>
                      <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-400 text-[11px]">
                        {referral.transport_status}
                      </span>
                    </dd>
                  </div>

                  <div>
                    <dt className="text-slate-500">Timestamp Milestones</dt>
                    <dd className="text-slate-400 space-y-1 mt-1 font-mono text-[11px]">
                      <div>Initiated: {new Date(referral.initiated_at).toLocaleString("en-IN")}</div>
                      {referral.accepted_at && <div>Accepted: {new Date(referral.accepted_at).toLocaleString("en-IN")}</div>}
                      {referral.notified_at && <div>Notified: {new Date(referral.notified_at).toLocaleString("en-IN")}</div>}
                      {referral.departed_at && <div>Departed: {new Date(referral.departed_at).toLocaleString("en-IN")}</div>}
                      {referral.arrived_at && <div>Arrived: {new Date(referral.arrived_at).toLocaleString("en-IN")}</div>}
                      {referral.in_service_at && <div>In Service: {new Date(referral.in_service_at).toLocaleString("en-IN")}</div>}
                      {referral.completed_at && <div>Completed: {new Date(referral.completed_at).toLocaleString("en-IN")}</div>}
                      {referral.back_referred_at && <div>Back Referred: {new Date(referral.back_referred_at).toLocaleString("en-IN")}</div>}
                    </dd>
                  </div>
                </dl>
              </div>
            </div>

            {/* Immutable Timeline Events */}
            <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
              <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 pb-2 border-b border-slate-800 flex items-center justify-between">
                <span>Immutable Referral Timeline</span>
                <span className="text-emerald-400 font-mono font-normal">
                  {events.length} Recorded Events
                </span>
              </h2>

              <div className="relative pl-6 space-y-6 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-800">
                {events.map((ev) => (
                  <div key={ev.id} className="relative">
                    <div className="absolute -left-6 top-1 w-3.5 h-3.5 rounded-full bg-emerald-500 border-2 border-slate-950"></div>
                    <div className="bg-slate-950/80 border border-slate-800/80 rounded-xl p-4 text-xs space-y-1">
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
                        <span className="font-bold text-white text-xs">
                          {ev.event_type.replace(/_/g, " ")}
                        </span>
                        <span className="font-mono text-[11px] text-slate-500">
                          {new Date(ev.created_at).toLocaleString("en-IN")}
                        </span>
                      </div>

                      <div className="text-slate-400">
                        Transition:{" "}
                        <span className="font-mono text-slate-300">
                          {ev.previous_status || "START"} → {ev.new_status}
                        </span>
                        {ev.performer_name && (
                          <span className="text-slate-500 ml-2">
                            by {ev.performer_name} ({ev.performer_role})
                          </span>
                        )}
                      </div>

                      {ev.notes && (
                        <div className="text-slate-300 pt-1 italic font-sans">
                          &ldquo;{ev.notes}&rdquo;
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Reject Modal */}
      {isRejectOpen && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 space-y-4">
            <h3 className="text-base font-bold text-white">Reject Referral</h3>
            <p className="text-xs text-slate-400">
              Provide a structured rejection reason and notes to allow rerouting.
            </p>

            <form onSubmit={handleRejectSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">
                  Rejection Reason *
                </label>
                <select
                  value={rejectReason}
                  onChange={(e) => setRejectReason(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-rose-500"
                >
                  {REJECTION_REASONS.map((r) => (
                    <option key={r.value} value={r.value}>
                      {r.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">
                  Notes / Explanation
                </label>
                <textarea
                  rows={3}
                  value={rejectNotes}
                  onChange={(e) => setRejectNotes(e.target.value)}
                  placeholder="Explain why this referral cannot be accommodated..."
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-white focus:outline-none focus:border-rose-500"
                />
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setIsRejectOpen(false)}
                  className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 text-xs font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold disabled:opacity-50"
                >
                  Confirm Rejection
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Depart Modal */}
      {isDepartOpen && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 space-y-4">
            <h3 className="text-base font-bold text-white">Record Patient Departure</h3>
            <p className="text-xs text-slate-400">
              Confirm transport vehicle details and estimated transit time.
            </p>

            <form onSubmit={handleDepartSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">
                  Transport Mode / Ambulance
                </label>
                <input
                  type="text"
                  value={departTransport}
                  onChange={(e) => setDepartTransport(e.target.value)}
                  placeholder="e.g. 108 Ambulance OD-14-1234, Private Vehicle"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">
                  Estimated Transit Time (Minutes)
                </label>
                <input
                  type="number"
                  min={1}
                  max={1440}
                  value={departMinutes}
                  onChange={(e) => setDepartMinutes(parseInt(e.target.value) || 30)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">
                  Departure Remarks
                </label>
                <textarea
                  rows={2}
                  value={departNotes}
                  onChange={(e) => setDepartNotes(e.target.value)}
                  placeholder="Escort details, vitals upon departure..."
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setIsDepartOpen(false)}
                  className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 text-xs font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold disabled:opacity-50"
                >
                  Confirm Departure
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Complete Modal */}
      {isCompleteOpen && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 space-y-4">
            <h3 className="text-base font-bold text-white">Complete Clinical Care</h3>
            <p className="text-xs text-slate-400">
              Record diagnosis, outcome, and clinical summary for medical record.
            </p>

            <form onSubmit={handleCompleteSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">
                  Treatment Outcome / Clinical Discharge Summary
                </label>
                <textarea
                  rows={4}
                  value={completeSummary}
                  onChange={(e) => setCompleteSummary(e.target.value)}
                  placeholder="Clinical outcome, interventions performed, discharge advice..."
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-white focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">
                  Administrative / Transfer Remarks
                </label>
                <textarea
                  rows={2}
                  value={completeNotes}
                  onChange={(e) => setCompleteNotes(e.target.value)}
                  placeholder="Bed clearance, medication handoff, escort signature..."
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-white focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setIsCompleteOpen(false)}
                  className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 text-xs font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold disabled:opacity-50"
                >
                  Confirm Completion
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Back Refer Modal */}
      {isBackReferOpen && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 space-y-4">
            <h3 className="text-base font-bold text-white">Issue Back-Referral Instructions</h3>
            <p className="text-xs text-slate-400">
              Provide clinical instructions and monitoring guidelines for local ASHA / ANM / PHC workers.
            </p>

            <form onSubmit={handleBackReferSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">
                  Primary Care Instructions & Follow-up Plan *
                </label>
                <textarea
                  rows={5}
                  required
                  value={backReferNotes}
                  onChange={(e) => setBackReferNotes(e.target.value)}
                  placeholder="e.g. Continue prescribed medication for 14 days. ASHA to check blood pressure weekly. Return if chest pain recurs..."
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-white focus:outline-none focus:border-violet-500"
                />
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setIsBackReferOpen(false)}
                  className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 text-xs font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 rounded-xl bg-violet-600 hover:bg-violet-500 text-white text-xs font-semibold disabled:opacity-50"
                >
                  Issue Back-Referral
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Reroute Modal */}
      {isRerouteOpen && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 space-y-4">
            <h3 className="text-base font-bold text-white">Reroute to Alternative Facility</h3>
            <p className="text-xs text-slate-400">
              Select an eligible alternative healthcare facility to receive this patient referral.
            </p>

            <form onSubmit={handleRerouteSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">
                  Select Alternative Facility *
                </label>
                <select
                  required
                  value={rerouteFacilityId}
                  onChange={(e) => setRerouteFacilityId(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-orange-500"
                >
                  <option value="">-- Choose Facility --</option>
                  {facilities
                    .filter((f) => f.id !== referral?.receiving_facility_id)
                    .map((f) => (
                      <option key={f.id} value={f.id}>
                        {f.name} ({f.facility_type.replace(/_/g, " ")}) - {f.district}
                      </option>
                    ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">
                  Rerouting Justification
                </label>
                <textarea
                  rows={2}
                  value={rerouteReason}
                  onChange={(e) => setRerouteReason(e.target.value)}
                  placeholder="Reason for alternative facility selection..."
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-white focus:outline-none focus:border-orange-500"
                />
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setIsRerouteOpen(false)}
                  className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 text-xs font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting || !rerouteFacilityId}
                  className="px-4 py-2 rounded-xl bg-orange-600 hover:bg-orange-500 text-white text-xs font-semibold disabled:opacity-50"
                >
                  Confirm Reroute
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default function ReferralDetailPage({ params }: PageProps) {
  const resolvedParams = use(params);
  return (
    <ProtectedRoute>
      <ReferralDetailContent referralId={resolvedParams.id} />
    </ProtectedRoute>
  );
}

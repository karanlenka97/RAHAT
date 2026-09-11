"use client";

import React, { useState, useEffect, use } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { getCareRequest, updateCareRequest } from "@/lib/careRequestApi";
import { getRecommendations } from "@/lib/recommendationApi";
import {
  CareRequest,
  CareCategory,
  CareRequestUpdateInput,
} from "@/types/careRequest";
import { FacilityRecommendationItem } from "@/types/recommendation";
import { ApiError } from "@/lib/api";

const ALLOWED_EDIT_ROLES = [
  "ADMIN",
  "DISTRICT_ADMIN",
  "FACILITY_ADMIN",
  "DOCTOR",
  "MEDICAL_OFFICER",
  "CHO",
  "ANM",
  "ASHA",
];

const CATEGORIES: { value: CareCategory; label: string }[] = [
  { value: "GENERAL_MEDICINE", label: "General Medicine" },
  { value: "MATERNAL_HEALTH", label: "Maternal Health / ANC" },
  { value: "CHILD_HEALTH", label: "Child Health / Pediatrics" },
  { value: "EMERGENCY", label: "Emergency & Trauma" },
  { value: "NCD", label: "Non-Communicable Diseases (NCD)" },
  { value: "MENTAL_HEALTH", label: "Mental Health" },
  { value: "EYE_CARE", label: "Eye Care / Ophthalmology" },
  { value: "ENT", label: "ENT (Ear, Nose, Throat)" },
  { value: "DENTAL", label: "Dental Care" },
  { value: "DIAGNOSTIC", label: "Diagnostic Investigation" },
  { value: "OTHER", label: "Other Specialized Care" },
];

const COMMON_DIAGNOSTICS = [
  "12-Lead ECG",
  "CBC",
  "Chest X-Ray",
  "Obstetric Ultrasound",
  "Abdominal Ultrasound",
  "CT Scan",
  "MRI",
  "Blood Sugar",
  "HbA1c",
  "Lipid Profile",
  "Serum Creatinine",
  "Urine Routine",
  "Spirometry",
  "Troponin I",
];

interface PageProps {
  params: Promise<{ id: string }>;
}

function UrgencyBadge({ urgency }: { urgency: string }) {
  switch (urgency.toUpperCase()) {
    case "EMERGENCY":
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-md text-xs font-bold bg-rose-500/20 text-rose-400 border border-rose-500/40">
          <span className="h-1.5 w-1.5 rounded-full bg-rose-400 animate-ping"></span>
          EMERGENCY
        </span>
      );
    case "HIGH":
      return (
        <span className="inline-flex items-center px-3 py-1 rounded-md text-xs font-semibold bg-amber-500/20 text-amber-400 border border-amber-500/40">
          HIGH URGENCY
        </span>
      );
    case "MEDIUM":
      return (
        <span className="inline-flex items-center px-3 py-1 rounded-md text-xs font-medium bg-teal-500/20 text-teal-400 border border-teal-500/40">
          MEDIUM URGENCY
        </span>
      );
    case "LOW":
    default:
      return (
        <span className="inline-flex items-center px-3 py-1 rounded-md text-xs font-medium bg-slate-800 text-slate-300 border border-slate-700">
          LOW URGENCY
        </span>
      );
  }
}

function RecommendationRankBadge({ rank }: { rank: number }) {
  if (rank === 1) {
    return (
      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 shadow-sm shadow-emerald-500/10">
        <svg className="w-3.5 h-3.5 fill-emerald-400 text-emerald-400" viewBox="0 0 20 20" fill="currentColor">
          <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
        </svg>
        #1 Top Recommendation
      </span>
    );
  }
  if (rank === 2) {
    return (
      <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-teal-500/20 text-teal-300 border border-teal-500/40">
        #2 Alternative
      </span>
    );
  }
  if (rank === 3) {
    return (
      <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-cyan-500/20 text-cyan-300 border border-cyan-500/40">
        #3 Alternative
      </span>
    );
  }
  return (
    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-800 text-slate-400 border border-slate-700">
      #{rank} Option
    </span>
  );
}

function CareRequestDetailContent({ careRequestId }: { careRequestId: string }) {
  const { user, token, logout } = useAuth();
  const router = useRouter();

  const [careRequest, setCareRequest] = useState<CareRequest | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState<number>(0);

  // Recommendations State
  const [recommendations, setRecommendations] = useState<FacilityRecommendationItem[]>([]);
  const [recLoading, setRecLoading] = useState<boolean>(true);
  const [recError, setRecError] = useState<string | null>(null);
  const [recLimit, setRecLimit] = useState<number>(5);
  const [recKey, setRecKey] = useState<number>(0);

  // Edit Modal State
  const [isEditOpen, setIsEditOpen] = useState<boolean>(false);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [editError, setEditError] = useState<string | null>(null);
  const [successBanner, setSuccessBanner] = useState<string | null>(null);

  const [formData, setFormData] = useState<CareRequestUpdateInput>({});

  useEffect(() => {
    let isMounted = true;
    async function loadRequest() {
      if (!token || !careRequestId) return;
      setIsLoading(true);
      setError(null);
      try {
        const data = await getCareRequest(careRequestId, token);
        if (isMounted) {
          setCareRequest(data);
        }
      } catch (err: unknown) {
        if (isMounted) {
          const msg =
            err instanceof ApiError
              ? err.message
              : err instanceof Error
              ? err.message
              : "Unable to load care request details. Please check connection.";
          setError(msg);
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    loadRequest();

    return () => {
      isMounted = false;
    };
  }, [careRequestId, token, reloadKey]);

  // Load Recommendations Effect
  useEffect(() => {
    let isMounted = true;
    async function loadRecommendations() {
      if (!token || !careRequestId) return;
      setRecLoading(true);
      setRecError(null);
      try {
        const res = await getRecommendations(careRequestId, recLimit, token);
        if (isMounted) {
          setRecommendations(res.recommendations);
        }
      } catch (err: unknown) {
        if (isMounted) {
          const msg =
            err instanceof ApiError
              ? err.message
              : err instanceof Error
              ? err.message
              : "Unable to calculate facility recommendations.";
          setRecError(msg);
        }
      } finally {
        if (isMounted) {
          setRecLoading(false);
        }
      }
    }

    loadRecommendations();

    return () => {
      isMounted = false;
    };
  }, [careRequestId, token, recLimit, recKey, reloadKey]);

  const handleLogout = async () => {
    await logout();
    router.push("/login");
  };

  const openEditModal = () => {
    if (!careRequest) return;
    setFormData({
      care_category: careRequest.care_category,
      required_service: careRequest.required_service,
      urgency: careRequest.urgency,
      symptoms_summary: careRequest.symptoms_summary,
      diagnostic_requirements: careRequest.diagnostic_requirements || [],
      specialist_required: careRequest.specialist_required,
      notes: careRequest.notes || "",
    });
    setEditError(null);
    setIsEditOpen(true);
  };

  const handleFormChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>
  ) => {
    const { name, value, type } = e.target;
    if (type === "checkbox") {
      const { checked } = e.target as HTMLInputElement;
      setFormData((prev) => ({ ...prev, [name]: checked }));
    } else {
      setFormData((prev) => ({ ...prev, [name]: value }));
    }
  };

  const toggleDiagnostic = (item: string) => {
    setFormData((prev) => {
      const current = prev.diagnostic_requirements || [];
      const updated = current.includes(item)
        ? current.filter((x) => x !== item)
        : [...current, item];
      return { ...prev, diagnostic_requirements: updated };
    });
  };

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.symptoms_summary?.trim()) {
      setEditError("Symptoms summary cannot be empty.");
      return;
    }
    if (!formData.required_service?.trim()) {
      setEditError("Required service cannot be empty.");
      return;
    }

    setIsSubmitting(true);
    setEditError(null);

    try {
      const payload: CareRequestUpdateInput = {
        care_category: formData.care_category,
        required_service: formData.required_service.trim(),
        urgency: formData.urgency,
        symptoms_summary: formData.symptoms_summary.trim(),
        diagnostic_requirements: formData.diagnostic_requirements || [],
        specialist_required: formData.specialist_required,
        notes: formData.notes?.trim() || undefined,
      };

      const updated = await updateCareRequest(careRequestId, payload, token);
      setCareRequest(updated);
      setReloadKey((k) => k + 1);
      setIsEditOpen(false);
      setSuccessBanner("Care request requirements updated successfully.");
      setTimeout(() => setSuccessBanner(null), 5000);
    } catch (err: unknown) {
      const msg =
        err instanceof ApiError
          ? err.message
          : err instanceof Error
          ? err.message
          : "Unable to update care request. Please verify inputs.";
      setEditError(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const canEdit = user && ALLOWED_EDIT_ROLES.includes(user.role);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Top Navbar */}
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link href="/dashboard" className="flex items-center gap-2">
              <div className="h-9 w-9 rounded-lg bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center font-bold text-emerald-400 text-lg">
                R
              </div>
              <span className="text-xl font-bold tracking-tight bg-gradient-to-r from-emerald-400 to-teal-200 bg-clip-text text-transparent">
                RAHAT
              </span>
            </Link>
            <span className="hidden sm:inline-block text-xs uppercase tracking-wider text-slate-400 border-l border-slate-700 pl-2">
              Care Request Details
            </span>
          </div>

          <div className="flex items-center gap-4">
            <Link
              href="/care-requests"
              className="text-xs font-medium text-slate-300 hover:text-emerald-400 transition"
            >
              &larr; All Care Requests
            </Link>
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

      {/* Main Content */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Breadcrumb Navigation */}
        <nav className="flex items-center gap-2 text-xs text-slate-400 mb-6">
          <Link href="/dashboard" className="hover:text-emerald-400 transition">
            Dashboard
          </Link>
          <span>/</span>
          <Link href="/care-requests" className="hover:text-emerald-400 transition">
            Care Requests
          </Link>
          <span>/</span>
          <span className="text-slate-200 font-mono">{careRequest?.request_number || careRequestId}</span>
        </nav>

        {/* Success Banner */}
        {successBanner && (
          <div className="mb-6 p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm font-medium">
              <span className="h-2 w-2 rounded-full bg-emerald-400"></span>
              {successBanner}
            </div>
            <button
              onClick={() => setSuccessBanner(null)}
              className="text-xs text-emerald-400 hover:underline"
            >
              Dismiss
            </button>
          </div>
        )}

        {isLoading ? (
          <div className="py-24 text-center">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-emerald-500 border-t-transparent mx-auto mb-3"></div>
            <p className="text-sm text-slate-400">Loading care request details...</p>
          </div>
        ) : error || !careRequest ? (
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-8 text-center max-w-lg mx-auto">
            <div className="inline-flex h-12 w-12 items-center justify-center rounded-full bg-rose-500/10 text-rose-400 mb-3 font-bold text-xl">
              !
            </div>
            <h2 className="text-lg font-bold text-white mb-1">Care Request Not Found</h2>
            <p className="text-sm text-slate-400 mb-4">{error || "The requested record could not be retrieved."}</p>
            <Link
              href="/care-requests"
              className="inline-flex items-center px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold transition"
            >
              Return to Care Requests Directory
            </Link>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Header Banner */}
            <div className="bg-gradient-to-r from-slate-900 via-slate-900 to-emerald-950/30 border border-slate-800 rounded-2xl p-6 sm:p-8 flex flex-col sm:flex-row sm:items-center justify-between gap-6">
              <div className="flex items-start gap-4">
                <div className="h-16 w-16 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center font-extrabold text-2xl text-emerald-400">
                  🩺
                </div>
                <div>
                  <div className="flex flex-wrap items-center gap-3 mb-1">
                    <h1 className="text-2xl sm:text-3xl font-extrabold text-white">
                      {careRequest.request_number}
                    </h1>
                    <UrgencyBadge urgency={careRequest.urgency} />
                    <span className="px-2.5 py-1 rounded-md text-xs font-mono font-medium bg-slate-800 text-slate-300 border border-slate-700">
                      {careRequest.status}
                    </span>
                  </div>
                  <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-400">
                    <span>
                      Category: <strong className="text-slate-200">{careRequest.care_category.replace(/_/g, " ")}</strong>
                    </span>
                    <span>•</span>
                    <span>
                      Required Service: <strong className="text-emerald-400">{careRequest.required_service}</strong>
                    </span>
                    <span>•</span>
                    <span>
                      Specialist:{" "}
                      <strong className={careRequest.specialist_required ? "text-teal-400" : "text-slate-300"}>
                        {careRequest.specialist_required ? "Specialist Required" : "General Care"}
                      </strong>
                    </span>
                  </div>
                </div>
              </div>

              {canEdit && (
                <button
                  onClick={openEditModal}
                  className="inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-white text-xs font-semibold shadow-md transition cursor-pointer self-start sm:self-center"
                >
                  <span>✏️</span>
                  <span>Edit Request</span>
                </button>
              )}
            </div>

            {/* Content Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Clinical & Service Requirements */}
              <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6">
                <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-4 pb-2 border-b border-slate-800">
                  Clinical & Service Needs
                </h2>
                <dl className="space-y-3.5 text-xs">
                  <div>
                    <dt className="text-slate-400">Care Category</dt>
                    <dd className="font-semibold text-slate-200 mt-0.5">
                      {careRequest.care_category.replace(/_/g, " ")}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-slate-400">Required Service</dt>
                    <dd className="font-semibold text-emerald-400 mt-0.5">
                      {careRequest.required_service}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-slate-400">Triage Urgency</dt>
                    <dd className="mt-1">
                      <UrgencyBadge urgency={careRequest.urgency} />
                    </dd>
                  </div>
                  <div>
                    <dt className="text-slate-400">Specialist Attention</dt>
                    <dd className="mt-0.5">
                      {careRequest.specialist_required ? (
                        <span className="text-teal-400 font-semibold">
                          Yes - Specialist Consultation Required
                        </span>
                      ) : (
                        <span className="text-slate-300 font-medium">
                          No - General Medical Officer / Primary Care
                        </span>
                      )}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-slate-400 mb-1.5">Diagnostic Requirements</dt>
                    <dd className="flex flex-wrap gap-1.5">
                      {careRequest.diagnostic_requirements && careRequest.diagnostic_requirements.length > 0 ? (
                        careRequest.diagnostic_requirements.map((diag) => (
                          <span
                            key={diag}
                            className="px-2 py-0.5 rounded text-[11px] font-mono bg-slate-800 text-slate-300 border border-slate-700"
                          >
                            {diag}
                          </span>
                        ))
                      ) : (
                        <span className="text-slate-500 italic">No specific diagnostics requested</span>
                      )}
                    </dd>
                  </div>
                </dl>
              </div>

              {/* Patient Demographics */}
              <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6">
                <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-4 pb-2 border-b border-slate-800 flex items-center justify-between">
                  <span>Patient Demographics</span>
                  {careRequest.patient && (
                    <Link
                      href={`/patients/${careRequest.patient.id}`}
                      className="text-[11px] text-emerald-400 hover:underline"
                    >
                      View Profile &rarr;
                    </Link>
                  )}
                </h2>
                {careRequest.patient ? (
                  <dl className="space-y-3.5 text-xs">
                    <div>
                      <dt className="text-slate-400">Patient Code</dt>
                      <dd className="font-mono font-bold text-emerald-400 mt-0.5">
                        {careRequest.patient.patient_code}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-slate-400">Full Name</dt>
                      <dd className="font-semibold text-white mt-0.5">
                        {careRequest.patient.full_name}
                      </dd>
                    </div>
                    <div className="flex gap-4">
                      <div>
                        <dt className="text-slate-400">Age</dt>
                        <dd className="text-slate-200 mt-0.5">
                          {careRequest.patient.age ? `${careRequest.patient.age} yrs` : "N/A"}
                        </dd>
                      </div>
                      <div>
                        <dt className="text-slate-400">Gender</dt>
                        <dd className="text-slate-200 mt-0.5">{careRequest.patient.gender}</dd>
                      </div>
                    </div>
                    <div>
                      <dt className="text-slate-400">Primary Phone</dt>
                      <dd className="font-mono text-slate-200 mt-0.5">
                        {careRequest.patient.phone || <span className="text-slate-500">Unregistered</span>}
                      </dd>
                    </div>
                    {careRequest.patient.village && (
                      <div>
                        <dt className="text-slate-400">Associated Village</dt>
                        <dd className="text-slate-200 mt-0.5">
                          {careRequest.patient.village.name} ({careRequest.patient.village.district},{" "}
                          {careRequest.patient.village.state})
                        </dd>
                      </div>
                    )}
                  </dl>
                ) : (
                  <p className="text-xs text-slate-500">Patient details not linked.</p>
                )}
              </div>

              {/* System Metadata & Creator */}
              <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6">
                <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-4 pb-2 border-b border-slate-800">
                  Traceability & Audit
                </h2>
                <dl className="space-y-3.5 text-xs">
                  <div>
                    <dt className="text-slate-400">Initiated By (Creator)</dt>
                    <dd className="mt-0.5">
                      {careRequest.creator ? (
                        <div>
                          <div className="font-semibold text-white">{careRequest.creator.full_name}</div>
                          <div className="text-[11px] font-mono text-emerald-400">
                            {careRequest.creator.role}
                          </div>
                        </div>
                      ) : (
                        <span className="text-slate-500 font-mono text-[11px]">
                          UID: {careRequest.created_by || "System"}
                        </span>
                      )}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-slate-400">Created Timestamp</dt>
                    <dd className="text-slate-300 font-mono mt-0.5">
                      {new Date(careRequest.created_at).toLocaleString("en-IN")}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-slate-400">Last Modified</dt>
                    <dd className="text-slate-300 font-mono mt-0.5">
                      {new Date(careRequest.updated_at).toLocaleString("en-IN")}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-slate-400">Internal Record UUID</dt>
                    <dd className="font-mono text-slate-500 break-all text-[11px] mt-0.5">
                      {careRequest.id}
                    </dd>
                  </div>
                </dl>
              </div>
            </div>

            {/* Symptoms & Clinical Notes Full Card */}
            <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6">
              <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-4 pb-2 border-b border-slate-800">
                Symptoms Summary & Clinical Notes
              </h2>
              <div className="space-y-4 text-xs">
                <div>
                  <h3 className="text-slate-400 font-medium mb-1">Chief Complaints / Symptoms Summary:</h3>
                  <p className="text-slate-100 bg-slate-950 p-4 rounded-xl border border-slate-800 leading-relaxed font-sans">
                    {careRequest.symptoms_summary}
                  </p>
                </div>
                {careRequest.notes && (
                  <div>
                    <h3 className="text-slate-400 font-medium mb-1">Confidential Clinical Notes:</h3>
                    <p className="text-slate-300 bg-slate-950/60 p-4 rounded-xl border border-slate-800 leading-relaxed font-sans">
                      {careRequest.notes}
                    </p>
                  </div>
                )}
              </div>
            </div>

            {/* Phase 7: Smart Facility Recommendation Engine */}
            <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-6">
              {/* Header */}
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-slate-800">
                <div>
                  <div className="flex items-center gap-2">
                    <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                      </svg>
                    </div>
                    <div>
                      <h2 className="text-base font-bold text-white flex items-center gap-2">
                        Smart Facility Recommendations
                        <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 font-normal">
                          Multi-Factor Scored
                        </span>
                      </h2>
                      <p className="text-xs text-slate-400 mt-0.5">
                        Deterministic matching based on clinical domain, travel proximity, diagnostics, specialist availability, and bed workload.
                      </p>
                    </div>
                  </div>
                </div>

                {/* Controls: Limit selector & Refresh */}
                <div className="flex items-center gap-2 self-start sm:self-auto">
                  <div className="flex items-center bg-slate-950 border border-slate-800 rounded-lg p-1 text-xs text-slate-300">
                    <span className="px-2 text-slate-500 font-medium">Show:</span>
                    {[3, 5, 10].map((lim) => (
                      <button
                        key={lim}
                        onClick={() => setRecLimit(lim)}
                        className={`px-2.5 py-1 rounded font-semibold transition ${
                          recLimit === lim
                            ? "bg-emerald-600 text-white shadow-sm"
                            : "text-slate-400 hover:text-white"
                        }`}
                      >
                        Top {lim}
                      </button>
                    ))}
                  </div>
                  <button
                    onClick={() => setRecKey((k) => k + 1)}
                    disabled={recLoading}
                    className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700 transition disabled:opacity-50"
                    title="Recalculate Recommendations"
                  >
                    <svg
                      className={`w-4 h-4 ${recLoading ? "animate-spin text-emerald-400" : ""}`}
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                      />
                    </svg>
                  </button>
                </div>
              </div>

              {/* Scoring Weights Criteria Strip */}
              <div className="flex flex-wrap items-center gap-2 text-[11px] text-slate-400 bg-slate-950/60 p-3 rounded-xl border border-slate-800/80">
                <span className="font-semibold text-slate-300 mr-1 flex items-center gap-1">
                  <svg className="w-3.5 h-3.5 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  Scoring Weights:
                </span>
                <span className="bg-slate-900 px-2 py-0.5 rounded border border-slate-800 text-slate-300">
                  Service Match <strong className="text-emerald-400">30%</strong>
                </span>
                <span className="bg-slate-900 px-2 py-0.5 rounded border border-slate-800 text-slate-300">
                  Distance Proximity <strong className="text-teal-400">20%</strong>
                </span>
                <span className="bg-slate-900 px-2 py-0.5 rounded border border-slate-800 text-slate-300">
                  Diagnostics <strong className="text-cyan-400">20%</strong>
                </span>
                <span className="bg-slate-900 px-2 py-0.5 rounded border border-slate-800 text-slate-300">
                  Specialist <strong className="text-indigo-400">15%</strong>
                </span>
                <span className="bg-slate-900 px-2 py-0.5 rounded border border-slate-800 text-slate-300">
                  Availability <strong className="text-amber-400">10%</strong>
                </span>
                <span className="bg-slate-900 px-2 py-0.5 rounded border border-slate-800 text-slate-300">
                  Workload <strong className="text-purple-400">5%</strong>
                </span>
              </div>

              {/* Loading State */}
              {recLoading && (
                <div className="space-y-4">
                  {[1, 2, 3].map((i) => (
                    <div
                      key={i}
                      className="animate-pulse bg-slate-950/80 border border-slate-800 rounded-xl p-5 space-y-3"
                    >
                      <div className="flex justify-between items-center">
                        <div className="h-5 bg-slate-800 rounded w-1/3"></div>
                        <div className="h-8 bg-slate-800 rounded w-20"></div>
                      </div>
                      <div className="h-4 bg-slate-800/60 rounded w-1/2"></div>
                      <div className="h-10 bg-slate-900 rounded"></div>
                    </div>
                  ))}
                </div>
              )}

              {/* Error State */}
              {!recLoading && recError && (
                <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-xs text-rose-400 flex items-center justify-between">
                  <div>
                    <strong className="font-semibold">Recommendation Error:</strong> {recError}
                  </div>
                  <button
                    onClick={() => setRecKey((k) => k + 1)}
                    className="px-3 py-1 bg-rose-600/30 hover:bg-rose-600/50 text-white rounded-md transition font-medium"
                  >
                    Retry
                  </button>
                </div>
              )}

              {/* Empty State */}
              {!recLoading && !recError && recommendations.length === 0 && (
                <div className="text-center py-12 px-4 border border-dashed border-slate-800 rounded-xl bg-slate-950/30">
                  <div className="w-12 h-12 rounded-full bg-slate-800 flex items-center justify-center mx-auto mb-3 text-slate-500">
                    <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                    </svg>
                  </div>
                  <h3 className="text-sm font-semibold text-slate-300">No Matching Facilities Found</h3>
                  <p className="text-xs text-slate-500 mt-1 max-w-md mx-auto">
                    No active facilities in the system currently provide the required clinical capabilities for this category ({careRequest.care_category || "General"}).
                  </p>
                </div>
              )}

              {/* Recommendations List */}
              {!recLoading && !recError && recommendations.length > 0 && (
                <div className="space-y-4">
                  {recommendations.map((rec, index) => {
                    const rank = index + 1;
                    const scorePct = Math.round(rec.overall_score);
                    return (
                      <div
                        key={rec.facility_id}
                        className="bg-slate-950/70 border border-slate-800/90 hover:border-emerald-500/40 rounded-xl p-5 transition group hover:shadow-lg hover:shadow-emerald-950/20"
                      >
                        {/* Card Top: Rank, Facility Name, Score Gauge */}
                        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                          <div className="space-y-1.5 flex-1">
                            <div className="flex flex-wrap items-center gap-2">
                              <RecommendationRankBadge rank={rank} />
                              <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                                {rec.facility_type.replace(/_/g, " ")} • Tier {rec.tier_level}
                              </span>
                              {rec.specialist_available && (
                                <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/30">
                                  <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                                  </svg>
                                  Specialist Available
                                </span>
                              )}
                            </div>

                            <div className="flex items-baseline gap-2">
                              <Link
                                href={`/facilities/${rec.facility_id}`}
                                className="text-base font-bold text-white group-hover:text-emerald-400 transition"
                              >
                                {rec.facility_name}
                              </Link>
                              {rec.facility_code && (
                                <span className="text-xs font-mono text-slate-500">
                                  ({rec.facility_code})
                                </span>
                              )}
                            </div>

                            <div className="flex flex-wrap items-center gap-3 text-xs text-slate-400">
                              <span className="flex items-center gap-1">
                                <svg className="w-3.5 h-3.5 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                                </svg>
                                {rec.district}, {rec.state}
                              </span>

                              {rec.distance_km != null ? (
                                <span className="flex items-center gap-1 text-teal-400 font-medium">
                                  <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                                  </svg>
                                  {rec.distance_km.toFixed(1)} km away
                                </span>
                              ) : (
                                <span className="text-slate-500 italic">Distance N/A</span>
                              )}

                              <span className="text-slate-500">
                                Bed Load: {rec.current_load}/{rec.capacity} (
                                {Math.round((rec.current_load / (rec.capacity || 1)) * 100)}%)
                              </span>
                            </div>
                          </div>

                          {/* Overall Score Badge */}
                          <div className="flex flex-row sm:flex-col items-center sm:items-end justify-between sm:justify-start gap-1 p-3 rounded-xl bg-slate-900 border border-slate-800 shrink-0">
                            <div className="text-[11px] uppercase tracking-wider text-slate-400 font-medium">
                              Match Score
                            </div>
                            <div className="flex items-baseline gap-1">
                              <span
                                className={`text-2xl font-black ${
                                  scorePct >= 80
                                    ? "text-emerald-400"
                                    : scorePct >= 60
                                    ? "text-teal-400"
                                    : scorePct >= 40
                                    ? "text-amber-400"
                                    : "text-slate-400"
                                }`}
                              >
                                {scorePct}%
                              </span>
                              <span className="text-xs text-slate-500">/ 100</span>
                            </div>
                          </div>
                        </div>

                        {/* Deterministic Explanation Callout */}
                        <div className="mt-4 p-3 rounded-lg bg-emerald-950/20 border border-emerald-500/20 text-xs text-emerald-300 leading-relaxed flex items-start gap-2.5">
                          <svg className="w-4 h-4 text-emerald-400 mt-0.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          <div>
                            <span className="font-semibold text-emerald-200">Matching Justification: </span>
                            {rec.explanation}
                          </div>
                        </div>

                        {/* Matched Capabilities & Diagnostics Chips */}
                        <div className="mt-3.5 flex flex-wrap gap-2 text-xs">
                          {rec.matched_services.map((svc, sIdx) => (
                            <span
                              key={sIdx}
                              className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-slate-900 text-slate-300 border border-slate-800 text-[11px]"
                            >
                              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                              {svc}
                            </span>
                          ))}
                          {rec.diagnostics_available && rec.diagnostics_available.length > 0 && (
                            <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-cyan-950/30 text-cyan-300 border border-cyan-500/20 text-[11px]">
                              🔬 {rec.diagnostics_available.join(", ")}
                            </span>
                          )}
                        </div>

                        {/* Multi-Factor Breakdown Bars */}
                        <div className="mt-4 pt-3.5 border-t border-slate-900 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 text-[11px]">
                          <div>
                            <div className="flex justify-between text-slate-400 mb-1">
                              <span>Service (30%)</span>
                              <span className="text-slate-200 font-mono">
                                {Math.round(rec.factors.service_match)}%
                              </span>
                            </div>
                            <div className="w-full bg-slate-900 rounded-full h-1.5 overflow-hidden">
                              <div
                                className="bg-emerald-500 h-full rounded-full transition-all"
                                style={{ width: `${Math.min(100, Math.max(0, rec.factors.service_match))}%` }}
                              ></div>
                            </div>
                          </div>

                          <div>
                            <div className="flex justify-between text-slate-400 mb-1">
                              <span>Distance (20%)</span>
                              <span className="text-slate-200 font-mono">
                                {Math.round(rec.factors.distance)}%
                              </span>
                            </div>
                            <div className="w-full bg-slate-900 rounded-full h-1.5 overflow-hidden">
                              <div
                                className="bg-teal-500 h-full rounded-full transition-all"
                                style={{ width: `${Math.min(100, Math.max(0, rec.factors.distance))}%` }}
                              ></div>
                            </div>
                          </div>

                          <div>
                            <div className="flex justify-between text-slate-400 mb-1">
                              <span>Diagnostics (20%)</span>
                              <span className="text-slate-200 font-mono">
                                {Math.round(rec.factors.diagnostic_match)}%
                              </span>
                            </div>
                            <div className="w-full bg-slate-900 rounded-full h-1.5 overflow-hidden">
                              <div
                                className="bg-cyan-500 h-full rounded-full transition-all"
                                style={{ width: `${Math.min(100, Math.max(0, rec.factors.diagnostic_match))}%` }}
                              ></div>
                            </div>
                          </div>

                          <div>
                            <div className="flex justify-between text-slate-400 mb-1">
                              <span>Specialist (15%)</span>
                              <span className="text-slate-200 font-mono">
                                {Math.round(rec.factors.specialist_match)}%
                              </span>
                            </div>
                            <div className="w-full bg-slate-900 rounded-full h-1.5 overflow-hidden">
                              <div
                                className="bg-indigo-500 h-full rounded-full transition-all"
                                style={{ width: `${Math.min(100, Math.max(0, rec.factors.specialist_match))}%` }}
                              ></div>
                            </div>
                          </div>

                          <div>
                            <div className="flex justify-between text-slate-400 mb-1">
                              <span>Availability (10%)</span>
                              <span className="text-slate-200 font-mono">
                                {Math.round(rec.factors.availability)}%
                              </span>
                            </div>
                            <div className="w-full bg-slate-900 rounded-full h-1.5 overflow-hidden">
                              <div
                                className="bg-amber-500 h-full rounded-full transition-all"
                                style={{ width: `${Math.min(100, Math.max(0, rec.factors.availability))}%` }}
                              ></div>
                            </div>
                          </div>

                          <div>
                            <div className="flex justify-between text-slate-400 mb-1">
                              <span>Workload (5%)</span>
                              <span className="text-slate-200 font-mono">
                                {Math.round(rec.factors.workload)}%
                              </span>
                            </div>
                            <div className="w-full bg-slate-900 rounded-full h-1.5 overflow-hidden">
                              <div
                                className="bg-purple-500 h-full rounded-full transition-all"
                                style={{ width: `${Math.min(100, Math.max(0, rec.factors.workload))}%` }}
                              ></div>
                            </div>
                          </div>
                        </div>

                        {/* Card Footer Action */}
                        <div className="mt-4 pt-3 border-t border-slate-900 flex justify-end">
                          <Link
                            href={`/facilities/${rec.facility_id}`}
                            className="inline-flex items-center gap-1.5 text-xs text-emerald-400 hover:text-emerald-300 font-medium transition"
                          >
                            <span>View Full Facility Details & Capabilities</span>
                            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                            </svg>
                          </Link>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        )}
      </main>

      {/* Edit Modal */}
      {isEditOpen && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-3xl w-full p-6 sm:p-8 shadow-2xl my-8">
            <div className="flex items-center justify-between pb-4 border-b border-slate-800">
              <div>
                <h3 className="text-lg font-bold text-white">Edit Care Request</h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Update triage requirements and clinical service specifications for {careRequest?.request_number}.
                </p>
              </div>
              <button
                onClick={() => setIsEditOpen(false)}
                className="text-slate-400 hover:text-white text-lg p-1"
              >
                ✕
              </button>
            </div>

            {editError && (
              <div className="mt-4 p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-xs text-rose-400">
                {editError}
              </div>
            )}

            <form onSubmit={handleEditSubmit} className="mt-6 space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {/* Immutable Request Number */}
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1">
                    Request Number (Immutable)
                  </label>
                  <input
                    type="text"
                    disabled
                    value={careRequest?.request_number || ""}
                    className="w-full bg-slate-950/60 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-400 cursor-not-allowed font-mono font-bold"
                  />
                </div>

                {/* Immutable Patient */}
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1">
                    Patient (Immutable)
                  </label>
                  <input
                    type="text"
                    disabled
                    value={
                      careRequest?.patient
                        ? `${careRequest.patient.patient_code} - ${careRequest.patient.full_name}`
                        : "N/A"
                    }
                    className="w-full bg-slate-950/60 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-400 cursor-not-allowed"
                  />
                </div>

                {/* Care Category */}
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Care Category <span className="text-rose-400">*</span>
                  </label>
                  <select
                    name="care_category"
                    value={formData.care_category || "GENERAL_MEDICINE"}
                    onChange={handleFormChange}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-emerald-500"
                  >
                    {CATEGORIES.map((c) => (
                      <option key={c.value} value={c.value}>
                        {c.label}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Urgency */}
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Clinical Urgency <span className="text-rose-400">*</span>
                  </label>
                  <select
                    name="urgency"
                    value={formData.urgency || "LOW"}
                    onChange={handleFormChange}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-emerald-500"
                  >
                    <option value="LOW">LOW - Routine / Non-Urgent</option>
                    <option value="MEDIUM">MEDIUM - Needs Priority Review</option>
                    <option value="HIGH">HIGH - Urgent Triage</option>
                    <option value="EMERGENCY">EMERGENCY - Critical / Life Threatening</option>
                  </select>
                </div>

                {/* Required Service */}
                <div className="sm:col-span-2">
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Required Healthcare Service <span className="text-rose-400">*</span>
                  </label>
                  <input
                    type="text"
                    name="required_service"
                    required
                    value={formData.required_service || ""}
                    onChange={handleFormChange}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-emerald-500"
                  />
                </div>

                {/* Specialist Required Toggle */}
                <div className="sm:col-span-2 flex items-center gap-3 p-3 rounded-xl bg-slate-950 border border-slate-800">
                  <input
                    type="checkbox"
                    id="edit_specialist_required"
                    name="specialist_required"
                    checked={formData.specialist_required ?? false}
                    onChange={handleFormChange}
                    className="h-4 w-4 rounded bg-slate-900 border-slate-700 text-emerald-500 focus:ring-emerald-500"
                  />
                  <label htmlFor="edit_specialist_required" className="text-xs font-medium text-slate-200 cursor-pointer">
                    Requires Specialist Doctor Attention
                  </label>
                </div>

                {/* Symptoms Summary */}
                <div className="sm:col-span-2">
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Symptoms Summary & Chief Complaints <span className="text-rose-400">*</span>
                  </label>
                  <textarea
                    name="symptoms_summary"
                    required
                    rows={3}
                    value={formData.symptoms_summary || ""}
                    onChange={handleFormChange}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-emerald-500"
                  />
                </div>

                {/* Diagnostic Requirements */}
                <div className="sm:col-span-2">
                  <label className="block text-xs font-medium text-slate-300 mb-1.5">
                    Diagnostic Services Required
                  </label>
                  <div className="flex flex-wrap gap-1.5">
                    {COMMON_DIAGNOSTICS.map((diag) => {
                      const isSelected = formData.diagnostic_requirements?.includes(diag);
                      return (
                        <button
                          key={diag}
                          type="button"
                          onClick={() => toggleDiagnostic(diag)}
                          className={`px-2.5 py-1 rounded-md text-xs font-mono transition cursor-pointer ${
                            isSelected
                              ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/40"
                              : "bg-slate-950 text-slate-400 border border-slate-800 hover:border-slate-700"
                          }`}
                        >
                          {isSelected ? "✓ " : "+ "}
                          {diag}
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* Notes */}
                <div className="sm:col-span-2">
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Additional Clinical Notes (Optional)
                  </label>
                  <textarea
                    name="notes"
                    rows={2}
                    value={formData.notes || ""}
                    onChange={handleFormChange}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-emerald-500"
                  />
                </div>
              </div>

              {/* Action Buttons */}
              <div className="pt-4 flex justify-end gap-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsEditOpen(false)}
                  className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-300 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-5 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-xs font-semibold text-white transition flex items-center gap-2"
                >
                  {isSubmitting ? (
                    <>
                      <span className="h-3 w-3 animate-spin rounded-full border-2 border-white border-t-transparent"></span>
                      Saving Changes...
                    </>
                  ) : (
                    "Save Changes"
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default function CareRequestDetailPage({ params }: PageProps) {
  const unwrappedParams = use(params);
  return (
    <ProtectedRoute>
      <CareRequestDetailContent careRequestId={unwrappedParams.id} />
    </ProtectedRoute>
  );
}

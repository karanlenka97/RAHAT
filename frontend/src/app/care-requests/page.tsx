"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { getCareRequests, createCareRequest } from "@/lib/careRequestApi";
import { getPatients } from "@/lib/patientApi";
import {
  CareRequest,
  CareCategory,
  CareRequestCreateInput,
} from "@/types/careRequest";
import { Patient } from "@/types/patient";
import { ApiError } from "@/lib/api";

const ALLOWED_CREATION_ROLES = [
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

const COMMON_SERVICES = [
  "General Medicine",
  "Obstetrics & Gynecology",
  "Pediatrics",
  "Cardiology",
  "Orthopedics",
  "Neurology",
  "General Surgery",
  "Pulmonology",
  "Ophthalmology",
  "ENT",
  "Dermatology",
  "Psychiatry",
  "Diagnostic Radiology",
  "Laboratory Services",
];

function UrgencyBadge({ urgency }: { urgency: string }) {
  switch (urgency.toUpperCase()) {
    case "EMERGENCY":
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-bold bg-rose-500/20 text-rose-400 border border-rose-500/40">
          <span className="h-1.5 w-1.5 rounded-full bg-rose-400 animate-ping"></span>
          EMERGENCY
        </span>
      );
    case "HIGH":
      return (
        <span className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-semibold bg-amber-500/20 text-amber-400 border border-amber-500/40">
          HIGH
        </span>
      );
    case "MEDIUM":
      return (
        <span className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-medium bg-teal-500/20 text-teal-400 border border-teal-500/40">
          MEDIUM
        </span>
      );
    case "LOW":
    default:
      return (
        <span className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-medium bg-slate-800 text-slate-300 border border-slate-700">
          LOW
        </span>
      );
  }
}

function CareRequestsContent() {
  const { user, token, logout } = useAuth();
  const router = useRouter();

  const [careRequests, setCareRequests] = useState<CareRequest[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [page, setPage] = useState<number>(1);
  const [totalPages, setTotalPages] = useState<number>(1);
  const [pageSize] = useState<number>(10);
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [selectedUrgency, setSelectedUrgency] = useState<string>("");
  const [selectedCategory, setSelectedCategory] = useState<string>("");
  const [activeFilters, setActiveFilters] = useState<{ search: string; urgency: string; category: string }>({
    search: "",
    urgency: "",
    category: "",
  });
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState<number>(0);

  // Available Patients for Modal
  const [patients, setPatients] = useState<Patient[]>([]);

  // Create Modal State
  const [isCreateOpen, setIsCreateOpen] = useState<boolean>(false);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [modalError, setModalError] = useState<string | null>(null);
  const [successBanner, setSuccessBanner] = useState<string | null>(null);

  const initialFormData: CareRequestCreateInput = {
    patient_id: "",
    care_category: "GENERAL_MEDICINE",
    required_service: "General Medicine",
    urgency: "LOW",
    symptoms_summary: "",
    diagnostic_requirements: [],
    specialist_required: false,
    notes: "",
  };
  const [formData, setFormData] = useState<CareRequestCreateInput>(initialFormData);

  // Fetch Patients for Modal Dropdown
  useEffect(() => {
    let isMounted = true;
    if (!token) return;
    getPatients({ page: 1, page_size: 50 }, token)
      .then((data) => {
        if (isMounted) setPatients(data.items);
      })
      .catch((err) => console.error("Failed to fetch patients list for modal:", err));

    return () => {
      isMounted = false;
    };
  }, [token]);

  // Fetch Care Requests
  useEffect(() => {
    let isMounted = true;
    async function loadRequests() {
      if (!token) return;
      setIsLoading(true);
      setError(null);
      try {
        const data = await getCareRequests(
          {
            page,
            page_size: pageSize,
            search: activeFilters.search,
            urgency: activeFilters.urgency || undefined,
            care_category: activeFilters.category || undefined,
          },
          token
        );
        if (isMounted) {
          setCareRequests(data.items);
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
              : "Unable to retrieve care requests. Please check network connection.";
          setError(msg);
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    loadRequests();

    return () => {
      isMounted = false;
    };
  }, [token, page, pageSize, activeFilters, reloadKey]);

  const handleFilterSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    setActiveFilters({
      search: searchQuery,
      urgency: selectedUrgency,
      category: selectedCategory,
    });
  };

  const handleClearFilters = () => {
    setSearchQuery("");
    setSelectedUrgency("");
    setSelectedCategory("");
    setPage(1);
    setActiveFilters({ search: "", urgency: "", category: "" });
  };

  const handleLogout = async () => {
    await logout();
    router.push("/login");
  };

  const canCreate = user && ALLOWED_CREATION_ROLES.includes(user.role);

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

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.patient_id) {
      setModalError("Please select a registered patient.");
      return;
    }
    if (!formData.symptoms_summary.trim()) {
      setModalError("Symptoms summary is required.");
      return;
    }
    if (!formData.required_service.trim()) {
      setModalError("Required service is required.");
      return;
    }

    setIsSubmitting(true);
    setModalError(null);

    try {
      const payload: CareRequestCreateInput = {
        patient_id: formData.patient_id,
        care_category: formData.care_category,
        required_service: formData.required_service.trim(),
        urgency: formData.urgency,
        symptoms_summary: formData.symptoms_summary.trim(),
        diagnostic_requirements: formData.diagnostic_requirements || [],
        specialist_required: formData.specialist_required || false,
        notes: formData.notes?.trim() || undefined,
      };

      const created = await createCareRequest(payload, token);
      setIsCreateOpen(false);
      setFormData(initialFormData);
      setSuccessBanner(`Care request created successfully! Request Number: ${created.request_number}`);
      setTimeout(() => setSuccessBanner(null), 6000);
      setPage(1);
      setReloadKey((k) => k + 1);
    } catch (err: unknown) {
      const msg =
        err instanceof ApiError
          ? err.message
          : err instanceof Error
          ? err.message
          : "Unable to create care request. Please verify entered data.";
      setModalError(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

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
              Care Requests & Intake
            </span>
          </div>

          <div className="flex items-center gap-4">
            <Link
              href="/dashboard"
              className="text-xs font-medium text-slate-300 hover:text-emerald-400 transition"
            >
              Dashboard
            </Link>
            <Link
              href="/patients"
              className="text-xs font-medium text-slate-300 hover:text-emerald-400 transition"
            >
              Patients
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
        {/* Success Banner */}
        {successBanner && (
          <div className="mb-6 p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 flex items-center justify-between animate-fadeIn">
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

        {/* Header & Controls */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
          <div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              Care Requests & Intake Triage
            </h1>
            <p className="mt-1 text-sm text-slate-400">
              Manage clinical care requirements, assess triage urgency, and record diagnostic and specialist needs.
            </p>
          </div>

          {canCreate && (
            <button
              onClick={() => {
                setModalError(null);
                setIsCreateOpen(true);
              }}
              className="inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 text-white text-sm font-semibold shadow-lg shadow-emerald-950/50 transition cursor-pointer"
            >
              <span className="text-lg leading-none">+</span>
              <span>Create Care Request</span>
            </button>
          )}
        </div>

        {/* Filter Bar */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 mb-6">
          <form onSubmit={handleFilterSubmit} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            <div>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search complaint, patient code, service..."
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-emerald-500"
              />
            </div>

            <div>
              <select
                value={selectedUrgency}
                onChange={(e) => setSelectedUrgency(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-emerald-500"
              >
                <option value="">All Urgency Levels</option>
                <option value="LOW">Low Urgency</option>
                <option value="MEDIUM">Medium Urgency</option>
                <option value="HIGH">High Urgency</option>
                <option value="EMERGENCY">Emergency (Critical)</option>
              </select>
            </div>

            <div>
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-emerald-500"
              >
                <option value="">All Care Categories</option>
                {CATEGORIES.map((c) => (
                  <option key={c.value} value={c.value}>
                    {c.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex gap-2">
              <button
                type="submit"
                className="flex-1 px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold transition"
              >
                Apply Filters
              </button>
              {(activeFilters.search || activeFilters.urgency || activeFilters.category) && (
                <button
                  type="button"
                  onClick={handleClearFilters}
                  className="px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition"
                >
                  Clear
                </button>
              )}
            </div>
          </form>
        </div>

        {/* Care Requests Table Card */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
              Care Requests ({total})
            </h2>
            <span className="text-xs text-slate-500">
              Page {page} of {totalPages || 1}
            </span>
          </div>

          {isLoading ? (
            <div className="py-20 text-center">
              <div className="h-8 w-8 animate-spin rounded-full border-4 border-emerald-500 border-t-transparent mx-auto mb-3"></div>
              <p className="text-sm text-slate-400">Loading care requests...</p>
            </div>
          ) : error ? (
            <div className="p-8 text-center">
              <div className="inline-flex h-12 w-12 items-center justify-center rounded-full bg-rose-500/10 text-rose-400 mb-3 font-bold text-xl">
                !
              </div>
              <p className="text-sm text-rose-400 font-medium">{error}</p>
              <button
                onClick={() => setReloadKey((k) => k + 1)}
                className="mt-3 px-4 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs text-slate-200 transition"
              >
                Retry
              </button>
            </div>
          ) : careRequests.length === 0 ? (
            <div className="py-16 text-center px-4">
              <div className="h-12 w-12 rounded-full bg-slate-800 flex items-center justify-center mx-auto mb-3 text-slate-500 text-lg">
                🩺
              </div>
              <h3 className="text-base font-semibold text-white">No care requests found</h3>
              <p className="mt-1 text-xs text-slate-400 max-w-sm mx-auto">
                No matching care requests found for the applied filter criteria.
              </p>
              {canCreate && (
                <button
                  onClick={() => setIsCreateOpen(true)}
                  className="mt-4 px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold transition"
                >
                  + Create Care Request
                </button>
              )}
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-900/90 text-xs uppercase tracking-wider text-slate-400 border-b border-slate-800">
                  <tr>
                    <th className="px-6 py-3.5">Request Code</th>
                    <th className="px-6 py-3.5">Patient</th>
                    <th className="px-6 py-3.5">Category & Service</th>
                    <th className="px-6 py-3.5">Urgency</th>
                    <th className="px-6 py-3.5">Specialist</th>
                    <th className="px-6 py-3.5">Created Date</th>
                    <th className="px-6 py-3.5 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {careRequests.map((req) => (
                    <tr key={req.id} className="hover:bg-slate-800/30 transition">
                      <td className="px-6 py-4 whitespace-nowrap font-mono text-xs font-bold text-emerald-400">
                        {req.request_number}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {req.patient ? (
                          <div>
                            <Link
                              href={`/patients/${req.patient_id}`}
                              className="font-medium text-white hover:text-emerald-400 transition"
                            >
                              {req.patient.full_name}
                            </Link>
                            <span className="block text-[11px] font-mono text-slate-500">
                              {req.patient.patient_code}
                            </span>
                          </div>
                        ) : (
                          <span className="text-xs text-slate-500">Unknown Patient</span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="inline-block px-2 py-0.5 rounded text-[11px] font-medium bg-slate-800 text-slate-300 border border-slate-700">
                          {req.care_category.replace(/_/g, " ")}
                        </span>
                        <div className="text-xs text-slate-400 mt-1">{req.required_service}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <UrgencyBadge urgency={req.urgency} />
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-xs">
                        {req.specialist_required ? (
                          <span className="inline-flex items-center gap-1 text-teal-400 font-medium">
                            <span>👨‍⚕️</span> Specialist Req.
                          </span>
                        ) : (
                          <span className="text-slate-500">General Care</span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-xs text-slate-400 font-mono">
                        {new Date(req.created_at).toLocaleDateString("en-IN")}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right">
                        <Link
                          href={`/care-requests/${req.id}`}
                          className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 text-xs font-medium transition"
                        >
                          View Details &rarr;
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="px-6 py-4 border-t border-slate-800 flex items-center justify-between">
              <div className="text-xs text-slate-400">
                Showing {((page - 1) * pageSize) + 1} to {Math.min(page * pageSize, total)} of {total} requests
              </div>
              <div className="flex gap-2">
                <button
                  disabled={page <= 1}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed text-xs text-slate-300 transition"
                >
                  Previous
                </button>
                <div className="flex items-center px-3 text-xs font-mono text-slate-400">
                  {page} / {totalPages}
                </div>
                <button
                  disabled={page >= totalPages}
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed text-xs text-slate-300 transition"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </div>
      </main>

      {/* Create Care Request Modal */}
      {isCreateOpen && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-3xl w-full p-6 sm:p-8 shadow-2xl my-8">
            <div className="flex items-center justify-between pb-4 border-b border-slate-800">
              <div>
                <h3 className="text-lg font-bold text-white">Create Care Request</h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Initiate a clinical triage and service requirement for a registered patient.
                </p>
              </div>
              <button
                onClick={() => setIsCreateOpen(false)}
                className="text-slate-400 hover:text-white text-lg p-1"
              >
                ✕
              </button>
            </div>

            {modalError && (
              <div className="mt-4 p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-xs text-rose-400">
                {modalError}
              </div>
            )}

            <form onSubmit={handleCreateSubmit} className="mt-6 space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {/* Patient Selection */}
                <div className="sm:col-span-2">
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Select Patient <span className="text-rose-400">*</span>
                  </label>
                  <select
                    name="patient_id"
                    required
                    value={formData.patient_id}
                    onChange={handleFormChange}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500"
                  >
                    <option value="">-- Choose Patient --</option>
                    {patients.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.patient_code} - {p.full_name} ({p.age ? `${p.age}y` : "N/A"}, {p.gender})
                      </option>
                    ))}
                  </select>
                </div>

                {/* Care Category */}
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Care Category <span className="text-rose-400">*</span>
                  </label>
                  <select
                    name="care_category"
                    value={formData.care_category}
                    onChange={handleFormChange}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500"
                  >
                    {CATEGORIES.map((c) => (
                      <option key={c.value} value={c.value}>
                        {c.label}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Urgency Level */}
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Clinical Urgency <span className="text-rose-400">*</span>
                  </label>
                  <select
                    name="urgency"
                    value={formData.urgency}
                    onChange={handleFormChange}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500"
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
                    list="services-list"
                    required
                    value={formData.required_service}
                    onChange={handleFormChange}
                    placeholder="e.g. Cardiology, Obstetrics & Gynecology, General Medicine"
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500"
                  />
                  <datalist id="services-list">
                    {COMMON_SERVICES.map((s) => (
                      <option key={s} value={s} />
                    ))}
                  </datalist>
                </div>

                {/* Specialist Required Toggle */}
                <div className="sm:col-span-2 flex items-center gap-3 p-3 rounded-xl bg-slate-950 border border-slate-800">
                  <input
                    type="checkbox"
                    id="specialist_required"
                    name="specialist_required"
                    checked={formData.specialist_required}
                    onChange={handleFormChange}
                    className="h-4 w-4 rounded bg-slate-900 border-slate-700 text-emerald-500 focus:ring-emerald-500"
                  />
                  <label htmlFor="specialist_required" className="text-xs font-medium text-slate-200 cursor-pointer">
                    Requires Specialist Doctor Attention (Obstetrician, Cardiologist, Pediatrician, etc.)
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
                    value={formData.symptoms_summary}
                    onChange={handleFormChange}
                    placeholder="Describe chief complaint, onset duration, vital signs, and immediate clinical observations..."
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500"
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

                {/* Confidential Notes */}
                <div className="sm:col-span-2">
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Additional Clinical Notes (Optional)
                  </label>
                  <textarea
                    name="notes"
                    rows={2}
                    value={formData.notes || ""}
                    onChange={handleFormChange}
                    placeholder="Confidential observations, preliminary vitals, medication adherence..."
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500"
                  />
                </div>
              </div>

              {/* Action Buttons */}
              <div className="pt-4 flex justify-end gap-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsCreateOpen(false)}
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
                      Submitting...
                    </>
                  ) : (
                    "Submit Care Request"
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

export default function CareRequestsPage() {
  return (
    <ProtectedRoute>
      <CareRequestsContent />
    </ProtectedRoute>
  );
}

"use client";

import React, { useState, useEffect, use } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { getPatient, updatePatient, getVillages } from "@/lib/patientApi";
import { getCareRequests } from "@/lib/careRequestApi";
import { Patient, Village, PatientUpdateInput } from "@/types/patient";
import { CareRequest } from "@/types/careRequest";
import { ApiError } from "@/lib/api";

const ALLOWED_EDIT_ROLES = ["ADMIN", "DISTRICT_ADMIN", "FACILITY_ADMIN", "DOCTOR", "MEDICAL_OFFICER", "CHO", "ANM", "ASHA"];

interface PageProps {
  params: Promise<{ id: string }>;
}

function PatientProfileContent({ patientId }: { patientId: string }) {
  const { user, token, logout } = useAuth();
  const router = useRouter();

  const [patient, setPatient] = useState<Patient | null>(null);
  const [villages, setVillages] = useState<Village[]>([]);
  const [careRequests, setCareRequests] = useState<CareRequest[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Edit Modal State
  const [isEditOpen, setIsEditOpen] = useState<boolean>(false);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [editError, setEditError] = useState<string | null>(null);
  const [successBanner, setSuccessBanner] = useState<string | null>(null);

  const [formData, setFormData] = useState<PatientUpdateInput>({});
  const [reloadKey, setReloadKey] = useState<number>(0);

  useEffect(() => {
    let isMounted = true;
    async function loadPatient() {
      if (!token || !patientId) return;
      setIsLoading(true);
      setError(null);
      try {
        const data = await getPatient(patientId, token);
        if (isMounted) {
          setPatient(data);
        }
      } catch (err: unknown) {
        if (isMounted) {
          const msg =
            err instanceof ApiError
              ? err.message
              : err instanceof Error
              ? err.message
              : "Unable to retrieve patient profile. Please check network.";
          setError(msg);
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    loadPatient();

    return () => {
      isMounted = false;
    };
  }, [patientId, token, reloadKey]);

  // Load Villages for dropdown
  useEffect(() => {
    let isMounted = true;
    if (!token) return;
    getVillages(token)
      .then((data) => {
        if (isMounted) setVillages(data);
      })
      .catch((err) => console.error("Failed to load villages:", err));

    return () => {
      isMounted = false;
    };
  }, [token]);

  // Load Associated Care Requests
  useEffect(() => {
    let isMounted = true;
    if (!token || !patientId) return;
    getCareRequests({ patient_id: patientId }, token)
      .then((data) => {
        if (isMounted) setCareRequests(data.items);
      })
      .catch((err) => console.error("Failed to load patient care requests:", err));

    return () => {
      isMounted = false;
    };
  }, [patientId, token, reloadKey]);

  const handleLogout = async () => {
    await logout();
    router.push("/login");
  };

  const openEditModal = () => {
    if (!patient) return;
    setFormData({
      full_name: patient.full_name,
      age: patient.age ?? undefined,
      gender: patient.gender,
      phone: patient.phone ?? "",
      village_id: patient.village_id ?? "",
      address: patient.address ?? "",
      emergency_contact_name: patient.emergency_contact_name ?? "",
      emergency_contact_phone: patient.emergency_contact_phone ?? "",
      abha_reference: patient.abha_reference ?? "",
      blood_group: patient.blood_group ?? "",
    });
    setEditError(null);
    setIsEditOpen(true);
  };

  const handleFormChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: name === "age" ? (value === "" ? undefined : parseInt(value, 10)) : value,
    }));
  };

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.full_name?.trim()) {
      setEditError("Patient full name cannot be empty.");
      return;
    }

    setIsSubmitting(true);
    setEditError(null);

    try {
      const payload: PatientUpdateInput = {
        full_name: formData.full_name.trim(),
        gender: formData.gender,
        age: formData.age || undefined,
        phone: formData.phone?.trim() || undefined,
        village_id: formData.village_id ? formData.village_id : undefined,
        address: formData.address?.trim() || undefined,
        emergency_contact_name: formData.emergency_contact_name?.trim() || undefined,
        emergency_contact_phone: formData.emergency_contact_phone?.trim() || undefined,
        abha_reference: formData.abha_reference?.trim() || undefined,
        blood_group: formData.blood_group || undefined,
      };

      const updated = await updatePatient(patientId, payload, token);
      setPatient(updated);
      setReloadKey((k) => k + 1);
      setIsEditOpen(false);
      setSuccessBanner("Patient profile updated successfully.");
      setTimeout(() => setSuccessBanner(null), 5000);
    } catch (err: unknown) {
      const msg =
        err instanceof ApiError
          ? err.message
          : err instanceof Error
          ? err.message
          : "Unable to update patient. Please check the entered information.";
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
              Patient Record
            </span>
          </div>

          <div className="flex items-center gap-4">
            <Link
              href="/patients"
              className="text-xs font-medium text-slate-300 hover:text-emerald-400 transition"
            >
              &larr; Patient Registry
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
          <Link href="/patients" className="hover:text-emerald-400 transition">
            Patients
          </Link>
          <span>/</span>
          <span className="text-slate-200 font-mono">{patient?.patient_code || patientId}</span>
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
            <p className="text-sm text-slate-400">Loading patient profile...</p>
          </div>
        ) : error || !patient ? (
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-8 text-center max-w-lg mx-auto">
            <div className="inline-flex h-12 w-12 items-center justify-center rounded-full bg-rose-500/10 text-rose-400 mb-3 font-bold text-xl">
              !
            </div>
            <h2 className="text-lg font-bold text-white mb-1">Patient Not Found</h2>
            <p className="text-sm text-slate-400 mb-4">{error || "The requested patient record could not be loaded."}</p>
            <Link
              href="/patients"
              className="inline-flex items-center px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold transition"
            >
              Return to Patient Registry
            </Link>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Header Banner */}
            <div className="bg-gradient-to-r from-slate-900 via-slate-900 to-emerald-950/30 border border-slate-800 rounded-2xl p-6 sm:p-8 flex flex-col sm:flex-row sm:items-center justify-between gap-6">
              <div className="flex items-start gap-4">
                <div className="h-16 w-16 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center font-extrabold text-2xl text-emerald-400">
                  {patient.full_name.charAt(0).toUpperCase()}
                </div>
                <div>
                  <div className="flex items-center gap-3 mb-1">
                    <h1 className="text-2xl sm:text-3xl font-extrabold text-white">
                      {patient.full_name}
                    </h1>
                    <span className="px-3 py-1 rounded-md text-xs font-mono font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                      {patient.patient_code}
                    </span>
                  </div>
                  <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-400">
                    <span>
                      Age: <strong className="text-slate-200">{patient.age ? `${patient.age} yrs` : "N/A"}</strong>
                    </span>
                    <span>•</span>
                    <span>
                      Gender: <strong className="text-slate-200">{patient.gender}</strong>
                    </span>
                    {patient.blood_group && (
                      <>
                        <span>•</span>
                        <span>
                          Blood Group: <strong className="text-rose-400">{patient.blood_group}</strong>
                        </span>
                      </>
                    )}
                    {patient.village && (
                      <>
                        <span>•</span>
                        <span>
                          Village: <strong className="text-slate-200">{patient.village.name}</strong>
                        </span>
                      </>
                    )}
                  </div>
                </div>
              </div>

              {canEdit && (
                <button
                  onClick={openEditModal}
                  className="inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-white text-xs font-semibold shadow-md transition cursor-pointer self-start sm:self-center"
                >
                  <span>✏️</span>
                  <span>Edit Patient Profile</span>
                </button>
              )}
            </div>

            {/* Profile Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Demographic & Geographic Information */}
              <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6">
                <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-4 pb-2 border-b border-slate-800">
                  Demographic & Address
                </h2>
                <dl className="space-y-3.5 text-xs">
                  <div>
                    <dt className="text-slate-400">Primary Phone</dt>
                    <dd className="font-mono text-slate-200 font-semibold mt-0.5">
                      {patient.phone || <span className="text-slate-600 font-normal">Not Registered</span>}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-slate-400">Village / Sub-center</dt>
                    <dd className="text-slate-200 font-medium mt-0.5">
                      {patient.village ? (
                        <>
                          <div className="text-emerald-400 font-semibold">{patient.village.name}</div>
                          <div className="text-slate-400 text-[11px]">
                            {patient.village.district}, {patient.village.state}
                            {patient.village.pincode && ` - ${patient.village.pincode}`}
                          </div>
                        </>
                      ) : (
                        <span className="text-slate-600">Unassigned Village</span>
                      )}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-slate-400">Residential Address / Landmark</dt>
                    <dd className="text-slate-200 mt-0.5">
                      {patient.address || <span className="text-slate-600">No address provided</span>}
                    </dd>
                  </div>
                </dl>
              </div>

              {/* Emergency & Identity Details */}
              <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6">
                <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-4 pb-2 border-b border-slate-800">
                  Emergency & Identity Details
                </h2>
                <dl className="space-y-3.5 text-xs">
                  <div>
                    <dt className="text-slate-400">Emergency Contact</dt>
                    <dd className="text-slate-200 mt-0.5">
                      {patient.emergency_contact_name || patient.emergency_contact_phone ? (
                        <div>
                          <div className="font-semibold text-slate-200">
                            {patient.emergency_contact_name || "Emergency Contact"}
                          </div>
                          {patient.emergency_contact_phone && (
                            <div className="font-mono text-emerald-400">
                              {patient.emergency_contact_phone}
                            </div>
                          )}
                        </div>
                      ) : (
                        <span className="text-slate-600">None specified</span>
                      )}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-slate-400">Synthetic ABHA Reference</dt>
                    <dd className="mt-0.5">
                      {patient.abha_reference ? (
                        <div className="inline-block px-2 py-1 rounded bg-slate-800 border border-slate-700 font-mono text-slate-200">
                          {patient.abha_reference}
                        </div>
                      ) : (
                        <span className="text-slate-600">No ABHA linked</span>
                      )}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-slate-400">Blood Group</dt>
                    <dd className="font-bold text-rose-400 mt-0.5">
                      {patient.blood_group || <span className="text-slate-600 font-normal">Unrecorded</span>}
                    </dd>
                  </div>
                </dl>
              </div>

              {/* System Metadata */}
              <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6">
                <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-4 pb-2 border-b border-slate-800">
                  System Metadata
                </h2>
                <dl className="space-y-3.5 text-xs">
                  <div>
                    <dt className="text-slate-400">Internal Record ID</dt>
                    <dd className="font-mono text-slate-500 break-all mt-0.5">
                      {patient.id}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-slate-400">Created Timestamp</dt>
                    <dd className="text-slate-300 font-mono mt-0.5">
                      {new Date(patient.created_at).toLocaleString("en-IN")}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-slate-400">Last Modified</dt>
                    <dd className="text-slate-300 font-mono mt-0.5">
                      {new Date(patient.updated_at).toLocaleString("en-IN")}
                    </dd>
                  </div>
                </dl>
              </div>
            </div>

            {/* Associated Care Requests Section */}
            <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6">
              <div className="flex items-center justify-between pb-4 border-b border-slate-800 mb-4">
                <div>
                  <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                    Associated Care Requests ({careRequests.length})
                  </h2>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Clinical intake and triage requirements logged for this patient.
                  </p>
                </div>
                <Link
                  href="/care-requests"
                  className="px-3 py-1.5 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 text-xs font-medium transition"
                >
                  + New Care Request
                </Link>
              </div>

              {careRequests.length === 0 ? (
                <p className="text-xs text-slate-500 italic py-4 text-center">
                  No care requests currently logged for this patient.
                </p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-950 text-slate-400 border-b border-slate-800 uppercase tracking-wider">
                      <tr>
                        <th className="px-4 py-2.5">Request Code</th>
                        <th className="px-4 py-2.5">Care Category</th>
                        <th className="px-4 py-2.5">Required Service</th>
                        <th className="px-4 py-2.5">Urgency</th>
                        <th className="px-4 py-2.5">Specialist</th>
                        <th className="px-4 py-2.5">Logged Date</th>
                        <th className="px-4 py-2.5 text-right">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60">
                      {careRequests.map((cr) => (
                        <tr key={cr.id} className="hover:bg-slate-800/30 transition">
                          <td className="px-4 py-3 font-mono font-bold text-emerald-400">
                            {cr.request_number}
                          </td>
                          <td className="px-4 py-3 text-slate-200">
                            {cr.care_category.replace(/_/g, " ")}
                          </td>
                          <td className="px-4 py-3 text-slate-300 font-medium">
                            {cr.required_service}
                          </td>
                          <td className="px-4 py-3">
                            <span className="px-2 py-0.5 rounded font-mono font-bold text-[10px] bg-slate-800 text-slate-300 border border-slate-700">
                              {cr.urgency}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-slate-400">
                            {cr.specialist_required ? "👨‍⚕️ Required" : "General"}
                          </td>
                          <td className="px-4 py-3 text-slate-400 font-mono">
                            {new Date(cr.created_at).toLocaleDateString("en-IN")}
                          </td>
                          <td className="px-4 py-3 text-right">
                            <Link
                              href={`/care-requests/${cr.id}`}
                              className="text-emerald-400 hover:underline font-medium"
                            >
                              View &rarr;
                            </Link>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            {/* Future Referral & Recommendation Modules Placeholder */}
            <div className="bg-slate-900/30 border border-dashed border-slate-800 rounded-xl p-8 text-center">
              <div className="text-xs uppercase tracking-wider font-semibold text-slate-500 mb-1">
                Facility Match & Referral Journey
              </div>
              <p className="text-xs text-slate-500 italic max-w-md mx-auto">
                Care journey modules will appear here in later phases.
              </p>
            </div>
          </div>
        )}
      </main>

      {/* Edit Patient Modal */}
      {isEditOpen && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-2xl w-full p-6 sm:p-8 shadow-2xl my-8">
            <div className="flex items-center justify-between pb-4 border-b border-slate-800">
              <div>
                <h3 className="text-lg font-bold text-white">Edit Patient Information</h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Update demographic and contact details for {patient?.patient_code}.
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
                {/* Immutable Patient Code */}
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1">
                    Patient Code (Immutable)
                  </label>
                  <input
                    type="text"
                    disabled
                    value={patient?.patient_code || ""}
                    className="w-full bg-slate-950/60 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-400 cursor-not-allowed font-mono font-semibold"
                  />
                </div>

                {/* Immutable Internal ID */}
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1">
                    Record ID (Immutable)
                  </label>
                  <input
                    type="text"
                    disabled
                    value={patient?.id || ""}
                    className="w-full bg-slate-950/60 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-500 cursor-not-allowed font-mono"
                  />
                </div>

                {/* Full Name */}
                <div className="sm:col-span-2">
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Full Name <span className="text-rose-400">*</span>
                  </label>
                  <input
                    type="text"
                    name="full_name"
                    required
                    value={formData.full_name || ""}
                    onChange={handleFormChange}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500"
                  />
                </div>

                {/* Age */}
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Age (Years)</label>
                  <input
                    type="number"
                    name="age"
                    min="0"
                    max="130"
                    value={formData.age ?? ""}
                    onChange={handleFormChange}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500"
                  />
                </div>

                {/* Gender */}
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Gender <span className="text-rose-400">*</span>
                  </label>
                  <select
                    name="gender"
                    value={formData.gender || "MALE"}
                    onChange={handleFormChange}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500"
                  >
                    <option value="MALE">Male</option>
                    <option value="FEMALE">Female</option>
                    <option value="OTHER">Other</option>
                  </select>
                </div>

                {/* Phone */}
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Phone Number</label>
                  <input
                    type="tel"
                    name="phone"
                    value={formData.phone ?? ""}
                    onChange={handleFormChange}
                    placeholder="10-digit phone"
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500"
                  />
                </div>

                {/* Blood Group */}
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Blood Group</label>
                  <select
                    name="blood_group"
                    value={formData.blood_group ?? ""}
                    onChange={handleFormChange}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500"
                  >
                    <option value="">Select Blood Group</option>
                    <option value="A+">A+</option>
                    <option value="A-">A-</option>
                    <option value="B+">B+</option>
                    <option value="B-">B-</option>
                    <option value="AB+">AB+</option>
                    <option value="AB-">AB-</option>
                    <option value="O+">O+</option>
                    <option value="O-">O-</option>
                    <option value="UNKNOWN">Unknown</option>
                  </select>
                </div>

                {/* Village */}
                <div className="sm:col-span-2">
                  <label className="block text-xs font-medium text-slate-300 mb-1">Associated Village</label>
                  <select
                    name="village_id"
                    value={formData.village_id ?? ""}
                    onChange={handleFormChange}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500"
                  >
                    <option value="">-- Select Village --</option>
                    {villages.map((v) => (
                      <option key={v.id} value={v.id}>
                        {v.name} ({v.district}, {v.state})
                      </option>
                    ))}
                  </select>
                </div>

                {/* Address */}
                <div className="sm:col-span-2">
                  <label className="block text-xs font-medium text-slate-300 mb-1">Address / Landmark</label>
                  <input
                    type="text"
                    name="address"
                    value={formData.address ?? ""}
                    onChange={handleFormChange}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500"
                  />
                </div>

                {/* Emergency Contact Name */}
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Emergency Contact Name</label>
                  <input
                    type="text"
                    name="emergency_contact_name"
                    value={formData.emergency_contact_name ?? ""}
                    onChange={handleFormChange}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500"
                  />
                </div>

                {/* Emergency Contact Phone */}
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Emergency Contact Phone</label>
                  <input
                    type="tel"
                    name="emergency_contact_phone"
                    value={formData.emergency_contact_phone ?? ""}
                    onChange={handleFormChange}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500"
                  />
                </div>

                {/* Synthetic ABHA */}
                <div className="sm:col-span-2">
                  <label className="block text-xs font-medium text-slate-300 mb-1">Synthetic ABHA Reference</label>
                  <input
                    type="text"
                    name="abha_reference"
                    value={formData.abha_reference ?? ""}
                    onChange={handleFormChange}
                    placeholder="Synthetic identifier"
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500"
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

export default function PatientDetailPage({ params }: PageProps) {
  const unwrappedParams = use(params);
  return (
    <ProtectedRoute>
      <PatientProfileContent patientId={unwrappedParams.id} />
    </ProtectedRoute>
  );
}

"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { useOffline } from "@/context/OfflineContext";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { SyncStatusBadge } from "@/components/SyncStatusBadge";
import { getPatients, createPatient, getVillages } from "@/lib/patientApi";
import { Village, PatientCreateInput } from "@/types/patient";
import { ApiError } from "@/lib/api";
import { offlineDb, OfflinePatient } from "@/lib/offline/db";
import { queueOfflinePatient, cachePatientsLocally } from "@/lib/offline/syncEngine";

const ALLOWED_REGISTRATION_ROLES = ["ADMIN", "DISTRICT_ADMIN", "FACILITY_ADMIN", "DOCTOR", "MEDICAL_OFFICER", "CHO", "ANM", "ASHA"];

function PatientsDirectoryContent() {
  const { user, token, logout } = useAuth();
  const { isOnline, refreshPendingCount } = useOffline();
  const router = useRouter();

  // Patients state
  const [patients, setPatients] = useState<OfflinePatient[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [page, setPage] = useState<number>(1);
  const [totalPages, setTotalPages] = useState<number>(1);
  const [pageSize] = useState<number>(10);
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [activeSearch, setActiveSearch] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [isCachedView, setIsCachedView] = useState<boolean>(false);

  // Villages for dropdown
  const [villages, setVillages] = useState<Village[]>([]);

  // Registration Modal State
  const [isRegisterOpen, setIsRegisterOpen] = useState<boolean>(false);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [modalError, setModalError] = useState<string | null>(null);
  const [successBanner, setSuccessBanner] = useState<string | null>(null);

  // Registration Form State
  const initialFormData: PatientCreateInput = {
    full_name: "",
    age: undefined,
    gender: "MALE",
    phone: "",
    village_id: "",
    address: "",
    emergency_contact_name: "",
    emergency_contact_phone: "",
    abha_reference: "",
    blood_group: "",
  };
  const [formData, setFormData] = useState<PatientCreateInput>(initialFormData);

  // Fetch Villages
  useEffect(() => {
    if (!token) return;
    getVillages(token)
      .then((data) => setVillages(data))
      .catch((err) => console.error("Failed to load villages list:", err));
  }, [token]);

  // Fetch Patients
  const [reloadKey, setReloadKey] = useState<number>(0);

  useEffect(() => {
    let isMounted = true;
    async function loadPatients() {
      if (!token) return;
      setIsLoading(true);
      setError(null);
      setIsCachedView(false);

      try {
        const data = await getPatients(
          { page, page_size: pageSize, search: activeSearch },
          token
        );
        if (isMounted) {
          setPatients(data.items);
          setTotal(data.total);
          setTotalPages(data.total_pages);
          await cachePatientsLocally(data.items);
        }
      } catch (err: unknown) {
        // Fallback to local Dexie IndexedDB cache
        const localList = await offlineDb.patients.toArray();
        if (localList.length > 0 && isMounted) {
          setIsCachedView(true);
          setPatients(localList);
          setTotal(localList.length);
          setTotalPages(Math.ceil(localList.length / pageSize));
        } else if (isMounted) {
          const msg =
            err instanceof ApiError
              ? err.message
              : err instanceof Error
              ? err.message
              : "Unable to retrieve patient directory. Please check network.";
          setError(msg);
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    loadPatients();

    return () => {
      isMounted = false;
    };
  }, [token, page, pageSize, activeSearch, reloadKey]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    setActiveSearch(searchQuery);
  };

  const handleClearSearch = () => {
    setSearchQuery("");
    setActiveSearch("");
    setPage(1);
  };

  const handleLogout = async () => {
    await logout();
    router.push("/login");
  };

  const canRegister = user && ALLOWED_REGISTRATION_ROLES.includes(user.role);

  const handleFormChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: name === "age" ? (value === "" ? undefined : parseInt(value, 10)) : value,
    }));
  };

  const handleRegisterSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.full_name.trim()) {
      setModalError("Patient full name is required.");
      return;
    }

    setIsSubmitting(true);
    setModalError(null);

    const payload: PatientCreateInput = {
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

    // If offline, queue mutation locally
    if (!isOnline) {
      try {
        const offlinePatient = await queueOfflinePatient(payload);
        await refreshPendingCount();
        setIsRegisterOpen(false);
        setFormData(initialFormData);
        setPatients((prev) => [offlinePatient, ...prev]);
        setSuccessBanner(`Patient registered offline (Code: ${offlinePatient.patient_code}). Queued for automatic sync.`);
        setTimeout(() => setSuccessBanner(null), 8000);
      } catch (err: unknown) {
        setModalError(err instanceof Error ? err.message : "Failed to store patient locally.");
      } finally {
        setIsSubmitting(false);
      }
      return;
    }

    try {
      const created = await createPatient(payload, token);
      await cachePatientsLocally([created]);
      setIsRegisterOpen(false);
      setFormData(initialFormData);
      setSuccessBanner(`Patient registered successfully! Patient Code: ${created.patient_code}`);
      setTimeout(() => setSuccessBanner(null), 6000);
      setPage(1);
      setReloadKey((k) => k + 1);
    } catch (err: unknown) {
      // If network failed during online attempt, offer offline fallback
      try {
        const offlinePatient = await queueOfflinePatient(payload);
        await refreshPendingCount();
        setIsRegisterOpen(false);
        setFormData(initialFormData);
        setPatients((prev) => [offlinePatient, ...prev]);
        setSuccessBanner(`Network interrupted. Patient saved offline (Code: ${offlinePatient.patient_code}) and queued for sync.`);
        setTimeout(() => setSuccessBanner(null), 8000);
      } catch {
        const msg =
          err instanceof ApiError
            ? err.message
            : err instanceof Error
            ? err.message
            : "Unable to register the patient. Please check the entered information.";
        setModalError(msg);
      }
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
              Patient Registry
            </span>
          </div>

          <div className="flex items-center gap-4">
            <SyncStatusBadge />
            <Link
              href="/dashboard"
              className="text-xs font-medium text-slate-300 hover:text-emerald-400 transition"
            >
              Dashboard
            </Link>
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
        {/* Offline Cache Mode Banner */}
        {isCachedView && (
          <div className="mb-6 p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-400 flex items-center justify-between animate-fadeIn">
            <div className="flex items-center gap-2 text-sm font-medium">
              <span className="text-base">⚠️</span>
              <span>
                Operating in <strong>Offline Mode</strong>. Displaying locally cached patient registry. New registrations will queue automatically for synchronization upon reconnect.
              </span>
            </div>
            <span className="font-mono text-xs bg-amber-500/20 px-2.5 py-1 rounded-md border border-amber-500/30">
              Dexie Cache Active
            </span>
          </div>
        )}

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
              Patient Registry
            </h1>
            <p className="mt-1 text-sm text-slate-400">
              Manage and access rural citizen healthcare demographics and village registries.
            </p>
          </div>

          {canRegister && (
            <button
              onClick={() => {
                setModalError(null);
                setIsRegisterOpen(true);
              }}
              className="inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 text-white text-sm font-semibold shadow-lg shadow-emerald-950/50 transition cursor-pointer"
            >
              <span className="text-lg leading-none">+</span>
              <span>Register Patient</span>
            </button>
          )}
        </div>

        {/* Search & Filter Bar */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 mb-6">
          <form onSubmit={handleSearchSubmit} className="flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search by Patient Code (e.g. RAHAT-P-000001), Name, Phone, or ABHA..."
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition"
              />
            </div>
            <div className="flex gap-2">
              <button
                type="submit"
                className="px-5 py-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-medium transition cursor-pointer"
              >
                Search
              </button>
              {activeSearch && (
                <button
                  type="button"
                  onClick={handleClearSearch}
                  className="px-4 py-2.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm font-medium transition cursor-pointer"
                >
                  Clear
                </button>
              )}
            </div>
          </form>

          {activeSearch && (
            <div className="mt-3 text-xs text-slate-400">
              Showing search results for: <span className="text-emerald-400 font-mono font-medium">{activeSearch}</span>
            </div>
          )}
        </div>

        {/* Patients Table Card */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
              Registered Patients ({total})
            </h2>
            <span className="text-xs text-slate-500">
              Page {page} of {totalPages || 1}
            </span>
          </div>

          {isLoading ? (
            <div className="py-20 text-center">
              <div className="h-8 w-8 animate-spin rounded-full border-4 border-emerald-500 border-t-transparent mx-auto mb-3"></div>
              <p className="text-sm text-slate-400">Loading patient records...</p>
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
                Retry Request
              </button>
            </div>
          ) : patients.length === 0 ? (
            <div className="py-16 text-center px-4">
              <div className="h-12 w-12 rounded-full bg-slate-800 flex items-center justify-center mx-auto mb-3 text-slate-500 text-lg">
                📋
              </div>
              <h3 className="text-base font-semibold text-white">No patients found</h3>
              <p className="mt-1 text-xs text-slate-400 max-w-sm mx-auto">
                {activeSearch
                  ? "No matching records found for your search query. Try searching with a different keyword."
                  : "No patients have been registered yet in the system."}
              </p>
              {canRegister && !activeSearch && (
                <button
                  onClick={() => setIsRegisterOpen(true)}
                  className="mt-4 px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold transition"
                >
                  + Register First Patient
                </button>
              )}
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-900/90 text-xs uppercase tracking-wider text-slate-400 border-b border-slate-800">
                  <tr>
                    <th className="px-6 py-3.5">Patient Code</th>
                    <th className="px-6 py-3.5">Full Name</th>
                    <th className="px-6 py-3.5">Age / Gender</th>
                    <th className="px-6 py-3.5">Village / District</th>
                    <th className="px-6 py-3.5">Phone Number</th>
                    <th className="px-6 py-3.5 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {patients.map((patient) => (
                    <tr key={patient.id} className="hover:bg-slate-800/30 transition">
                      <td className="px-6 py-4 whitespace-nowrap font-mono text-xs font-semibold text-emerald-400">
                        {patient.patient_code}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="font-medium text-white">{patient.full_name}</div>
                        {patient.abha_reference && (
                          <span className="text-[10px] font-mono text-slate-500">
                            ABHA: {patient.abha_reference}
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-slate-300">
                        {patient.age ? `${patient.age} yrs` : "N/A"} •{" "}
                        <span className="text-xs text-slate-400">{patient.gender}</span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-slate-300">
                        {patient.village ? (
                          <div>
                            <span className="font-medium text-slate-200">{patient.village.name}</span>
                            <span className="block text-xs text-slate-500">
                              {patient.village.district}, {patient.village.state}
                            </span>
                          </div>
                        ) : (
                          <span className="text-xs text-slate-500">Unassigned</span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap font-mono text-xs text-slate-300">
                        {patient.phone || <span className="text-slate-600">None</span>}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right">
                        <Link
                          href={`/patients/${patient.id}`}
                          className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 text-xs font-medium transition"
                        >
                          View Profile &rarr;
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Pagination Controls */}
          {totalPages > 1 && (
            <div className="px-6 py-4 border-t border-slate-800 flex items-center justify-between">
              <div className="text-xs text-slate-400">
                Showing {((page - 1) * pageSize) + 1} to {Math.min(page * pageSize, total)} of {total} records
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

      {/* Patient Registration Modal */}
      {isRegisterOpen && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-2xl w-full p-6 sm:p-8 shadow-2xl my-8">
            <div className="flex items-center justify-between pb-4 border-b border-slate-800">
              <div>
                <h3 className="text-lg font-bold text-white">Register New Patient</h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Enter demographic and village information to generate a unique patient code.
                </p>
              </div>
              <button
                onClick={() => setIsRegisterOpen(false)}
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

            <form onSubmit={handleRegisterSubmit} className="mt-6 space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {/* Full Name */}
                <div className="sm:col-span-2">
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Full Name <span className="text-rose-400">*</span>
                  </label>
                  <input
                    type="text"
                    name="full_name"
                    required
                    value={formData.full_name}
                    onChange={handleFormChange}
                    placeholder="e.g. Ramesh Kumar"
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
                    placeholder="e.g. 42"
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
                    value={formData.gender}
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
                    placeholder="e.g. 9876543210"
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
                    placeholder="e.g. Near Panchayat Bhavan, Ward 3"
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
                    placeholder="e.g. Geeta Devi"
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
                    placeholder="e.g. 9876500000"
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500"
                  />
                </div>

                {/* Synthetic ABHA Reference */}
                <div className="sm:col-span-2">
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Synthetic ABHA Reference (Optional)
                  </label>
                  <input
                    type="text"
                    name="abha_reference"
                    value={formData.abha_reference ?? ""}
                    onChange={handleFormChange}
                    placeholder="e.g. 12-3456-7890-1234 (Synthetic Reference)"
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500"
                  />
                  <p className="mt-1 text-[11px] text-slate-500">
                    * Prototype mode: Synthetic demo identifier only. No live ABDM connection is initiated.
                  </p>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="pt-4 flex justify-end gap-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsRegisterOpen(false)}
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
                      Registering...
                    </>
                  ) : (
                    "Register Patient"
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

export default function PatientsPage() {
  return (
    <ProtectedRoute>
      <PatientsDirectoryContent />
    </ProtectedRoute>
  );
}

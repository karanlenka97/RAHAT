"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import {
  getFacility,
  updateFacility,
  createFacilityCapability,
  updateFacilityCapability,
} from "@/lib/facilityApi";
import {
  Facility,
  FacilityCapability,
  FacilityType,
  ServiceCategory,
  AvailabilityStatus,
  FacilityUpdateInput,
  FacilityCapabilityCreateInput,
  FacilityCapabilityUpdateInput,
} from "@/types/facility";
import { ApiError } from "@/lib/api";

const ALLOWED_MANAGE_ROLES = ["ADMIN", "DISTRICT_ADMIN", "FACILITY_ADMIN"];

const SERVICE_CATEGORIES: { value: ServiceCategory; label: string }[] = [
  { value: "GENERAL_MEDICINE", label: "General Medicine" },
  { value: "CARDIOLOGY", label: "Cardiology" },
  { value: "OBSTETRICS", label: "Obstetrics & Gynecology" },
  { value: "PEDIATRICS", label: "Pediatrics & Neonatology" },
  { value: "ORTHOPEDICS", label: "Orthopedics & Trauma" },
  { value: "LABORATORY", label: "Diagnostic Laboratory" },
  { value: "X_RAY", label: "Digital X-Ray Radiography" },
  { value: "ULTRASOUND", label: "Ultrasound & Sonography" },
  { value: "CT", label: "CT Scanning & Computed Tomography" },
  { value: "DIALYSIS", label: "Nephrology & Hemodialysis" },
  { value: "MENTAL_HEALTH", label: "Mental Health & Psychiatry" },
  { value: "EYE_CARE", label: "Ophthalmology / Eye Care" },
  { value: "ENT", label: "ENT (Ear, Nose, Throat)" },
  { value: "DENTAL", label: "Dental Care" },
  { value: "EMERGENCY", label: "24x7 Emergency & Resuscitation" },
  { value: "OTHER", label: "Other Specialized Care" },
];

function AvailabilityBadge({ status }: { status: string }) {
  switch (status.toUpperCase()) {
    case "AVAILABLE":
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-400"></span>
          Operational
        </span>
      );
    case "LIMITED":
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/20 text-amber-300 border border-amber-500/40">
          <span className="h-1.5 w-1.5 rounded-full bg-amber-400"></span>
          Limited
        </span>
      );
    case "HIGH_LOAD":
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-orange-500/20 text-orange-300 border border-orange-500/40">
          <span className="h-1.5 w-1.5 rounded-full bg-orange-400 animate-pulse"></span>
          High Load
        </span>
      );
    case "UNAVAILABLE":
    default:
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-500/20 text-rose-300 border border-rose-500/40">
          <span className="h-1.5 w-1.5 rounded-full bg-rose-400"></span>
          Unavailable
        </span>
      );
  }
}

function FacilityDetailContent() {
  const { id } = useParams<{ id: string }>();
  const { user, token } = useAuth();

  const [facility, setFacility] = useState<Facility | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Edit Facility Modal
  const [showEditFacilityModal, setShowEditFacilityModal] = useState(false);
  const [editFacilityData, setEditFacilityData] = useState<FacilityUpdateInput>({});
  const [editFacilitySubmitting, setEditFacilitySubmitting] = useState(false);
  const [editFacilityError, setEditFacilityError] = useState<string | null>(null);

  // Add Capability Modal
  const [showAddCapModal, setShowAddCapModal] = useState(false);
  const [newCapData, setNewCapData] = useState<FacilityCapabilityCreateInput>({
    service_name: "",
    service_category: "GENERAL_MEDICINE",
    available: true,
    availability_status: "AVAILABLE",
    capacity: 50,
    current_load: 10,
    specialist_required: false,
    diagnostic_required: false,
    operating_hours: "24x7",
  });
  const [capSubmitting, setCapSubmitting] = useState(false);
  const [capError, setCapError] = useState<string | null>(null);

  // Edit Capability Modal
  const [editingCapability, setEditingCapability] = useState<FacilityCapability | null>(null);
  const [editCapData, setEditCapData] = useState<FacilityCapabilityUpdateInput>({});
  const [editCapSubmitting, setEditCapSubmitting] = useState(false);
  const [editCapError, setEditCapError] = useState<string | null>(null);

  const canManage = user?.role && ALLOWED_MANAGE_ROLES.includes(user.role);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    if (!id) return;
    let isMounted = true;

    async function loadFacility() {
      try {
        const data = await getFacility(id, token);
        if (isMounted) {
          setFacility(data);
          setError(null);
        }
      } catch (err: unknown) {
        if (isMounted) {
          if (err instanceof ApiError) {
            setError(err.message);
          } else {
            setError("Failed to load facility profile.");
          }
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    }

    loadFacility();

    return () => {
      isMounted = false;
    };
  }, [id, reloadKey, token]);

  // Handle Edit Facility Submit
  const handleEditFacilitySubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!facility) return;
    setEditFacilitySubmitting(true);
    setEditFacilityError(null);
    try {
      const updated = await updateFacility(facility.id, editFacilityData, token);
      setFacility(updated);
      setShowEditFacilityModal(false);
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setEditFacilityError(err.message);
      } else {
        setEditFacilityError("Failed to update facility details.");
      }
    } finally {
      setEditFacilitySubmitting(false);
    }
  };

  // Handle Add Capability Submit
  const handleAddCapabilitySubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!facility) return;
    setCapSubmitting(true);
    setCapError(null);
    try {
      await createFacilityCapability(facility.id, newCapData, token);
      setShowAddCapModal(false);
      setNewCapData({
        service_name: "",
        service_category: "GENERAL_MEDICINE",
        available: true,
        availability_status: "AVAILABLE",
        capacity: 50,
        current_load: 10,
        specialist_required: false,
        diagnostic_required: false,
        operating_hours: "24x7",
      });
      setReloadKey((k) => k + 1);
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setCapError(err.message);
      } else {
        setCapError("Failed to add capability.");
      }
    } finally {
      setCapSubmitting(false);
    }
  };

  // Handle Edit Capability Submit
  const handleEditCapabilitySubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!facility || !editingCapability) return;
    setEditCapSubmitting(true);
    setEditCapError(null);
    try {
      await updateFacilityCapability(
        facility.id,
        editingCapability.id,
        editCapData,
        token
      );
      setEditingCapability(null);
      setReloadKey((k) => k + 1);
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setEditCapError(err.message);
      } else {
        setEditCapError("Failed to update capability.");
      }
    } finally {
      setEditCapSubmitting(false);
    }
  };

  const openEditFacilityModal = () => {
    if (!facility) return;
    setEditFacilityData({
      name: facility.name,
      facility_type: facility.facility_type as FacilityType,
      district: facility.district,
      state: facility.state,
      address: facility.address || "",
      pincode: facility.pincode || "",
      phone: facility.phone || "",
      operating_hours: facility.operating_hours || "24x7",
      is_active: facility.is_active,
      total_beds: facility.total_beds,
      available_beds: facility.available_beds,
      icu_beds: facility.icu_beds,
      available_icu_beds: facility.available_icu_beds,
    });
    setEditFacilityError(null);
    setShowEditFacilityModal(true);
  };

  const openEditCapModal = (cap: FacilityCapability) => {
    setEditingCapability(cap);
    setEditCapData({
      service_name: cap.service_name,
      service_category: cap.service_category as ServiceCategory,
      available: cap.available,
      availability_status: cap.availability_status as AvailabilityStatus,
      capacity: cap.capacity,
      current_load: cap.current_load,
      specialist_required: cap.specialist_required,
      diagnostic_required: cap.diagnostic_required,
      operating_hours: cap.operating_hours || "24x7",
    });
    setEditCapError(null);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center p-8">
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin"></div>
          <p className="text-xs text-slate-400">Loading healthcare facility profile...</p>
        </div>
      </div>
    );
  }

  if (error || !facility) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center p-8">
        <div className="max-w-md w-full p-6 bg-slate-900 border border-slate-800 rounded-2xl text-center">
          <div className="text-3xl mb-2">⚠️</div>
          <h2 className="text-base font-bold text-white">Facility Not Found</h2>
          <p className="mt-1 text-xs text-rose-400">{error || "Requested facility does not exist."}</p>
          <Link
            href="/facilities"
            className="mt-4 inline-block px-4 py-2 text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg transition"
          >
            &larr; Back to Facility Directory
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Top Navbar */}
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link href="/facilities" className="flex items-center gap-2">
              <div className="h-9 w-9 rounded-lg bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center font-bold text-emerald-400 text-lg">
                R
              </div>
              <span className="text-xl font-bold tracking-tight bg-gradient-to-r from-emerald-400 to-teal-200 bg-clip-text text-transparent">
                RAHAT
              </span>
            </Link>
            <span className="text-xs uppercase tracking-wider text-slate-400 border-l border-slate-700 pl-3">
              Facility Profile
            </span>
          </div>

          <div className="flex items-center gap-3">
            <Link
              href="/facilities"
              className="px-3 py-1.5 text-xs font-medium text-slate-400 hover:text-white border border-slate-800 rounded-lg hover:bg-slate-800/60 transition"
            >
              &larr; Directory
            </Link>
            {canManage && (
              <button
                onClick={openEditFacilityModal}
                className="px-3.5 py-1.5 text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-lg transition"
              >
                ✏️ Edit Details
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Facility Header Banner */}
        <div className="p-6 sm:p-8 rounded-2xl bg-gradient-to-r from-slate-900 via-slate-900 to-emerald-950/30 border border-slate-800 shadow-xl mb-8">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <div className="flex flex-wrap items-center gap-2 mb-2">
                <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
                  Tier {facility.tier_level} • {facility.facility_type}
                </span>
                <span
                  className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium ${
                    facility.is_active
                      ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                      : "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                  }`}
                >
                  <span
                    className={`h-1.5 w-1.5 rounded-full ${
                      facility.is_active ? "bg-emerald-400" : "bg-rose-400"
                    }`}
                  ></span>
                  {facility.is_active ? "Network Operational" : "Inactive"}
                </span>
                {facility.code && (
                  <span className="px-2 py-0.5 rounded text-xs font-mono bg-slate-800 text-slate-300 border border-slate-700">
                    {facility.code}
                  </span>
                )}
              </div>

              <h1 className="text-2xl sm:text-3xl font-extrabold text-white">{facility.name}</h1>
              <p className="mt-1 text-xs sm:text-sm text-slate-400 flex items-center gap-2">
                <span>📍 {facility.address ? `${facility.address}, ` : ""}{facility.district}, {facility.state}</span>
              </p>
            </div>

            <div className="flex flex-col sm:items-end gap-2 text-xs">
              {facility.phone && (
                <div className="flex items-center gap-2 bg-slate-950/80 px-3 py-1.5 rounded-lg border border-slate-800">
                  <span className="text-slate-500">Helpline:</span>
                  <span className="font-mono text-emerald-400 font-semibold">{facility.phone}</span>
                </div>
              )}
              <div className="flex items-center gap-2 bg-slate-950/80 px-3 py-1.5 rounded-lg border border-slate-800">
                <span className="text-slate-500">Operating Hours:</span>
                <span className="text-slate-300 font-medium">{facility.operating_hours || "24x7"}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Info Grid: Location & Bed Stats */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          {/* Location & GPS Card */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-4">
              Geographic Coordinates & Registry
            </h2>
            <dl className="space-y-2.5 text-xs">
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <dt className="text-slate-400">Latitude</dt>
                <dd className="font-mono text-white font-semibold">{facility.latitude.toFixed(6)}</dd>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <dt className="text-slate-400">Longitude</dt>
                <dd className="font-mono text-white font-semibold">{facility.longitude.toFixed(6)}</dd>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <dt className="text-slate-400">Postal Pincode</dt>
                <dd className="font-mono text-slate-300">{facility.pincode || "N/A"}</dd>
              </div>
              <div className="flex justify-between py-1">
                <dt className="text-slate-400">District / State</dt>
                <dd className="text-slate-300">{facility.district}, {facility.state}</dd>
              </div>
            </dl>
          </div>

          {/* General Inpatient Beds Card */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-2">
                <h2 className="text-xs font-semibold uppercase tracking-wider text-emerald-400">
                  General Inpatient Beds
                </h2>
                <span className="text-xs font-mono font-bold text-white">
                  {facility.available_beds} / {facility.total_beds} Vacant
                </span>
              </div>
              <div className="w-full bg-slate-950 rounded-full h-2.5 mb-4 border border-slate-800">
                <div
                  className="bg-emerald-500 h-2.5 rounded-full transition-all"
                  style={{
                    width: `${
                      facility.total_beds > 0
                        ? Math.min(100, ((facility.total_beds - facility.available_beds) / facility.total_beds) * 100)
                        : 0
                    }%`,
                  }}
                ></div>
              </div>
            </div>
            <p className="text-[11px] text-slate-500">
              Sanctioned non-critical admission capacity for rural referrals.
            </p>
          </div>

          {/* ICU & Critical Beds Card */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-2">
                <h2 className="text-xs font-semibold uppercase tracking-wider text-cyan-400">
                  ICU / Critical Care Beds
                </h2>
                <span className="text-xs font-mono font-bold text-white">
                  {facility.available_icu_beds} / {facility.icu_beds} Vacant
                </span>
              </div>
              <div className="w-full bg-slate-950 rounded-full h-2.5 mb-4 border border-slate-800">
                <div
                  className="bg-cyan-500 h-2.5 rounded-full transition-all"
                  style={{
                    width: `${
                      facility.icu_beds > 0
                        ? Math.min(
                            100,
                            ((facility.icu_beds - facility.available_icu_beds) / facility.icu_beds) * 100
                          )
                        : 0
                    }%`,
                  }}
                ></div>
              </div>
            </div>
            <p className="text-[11px] text-slate-500">
              Emergency intensive care ventilator and resuscitation beds.
            </p>
          </div>
        </div>

        {/* Facility Capabilities Section */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 mb-6 border-b border-slate-800">
            <div>
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <span>🩺</span> Verified Facility Capabilities ({facility.capabilities?.length || 0})
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Specialized clinical departments, diagnostic modalities, daily workload capacities, and availability.
              </p>
            </div>
            {canManage && (
              <button
                onClick={() => setShowAddCapModal(true)}
                className="px-3.5 py-1.5 text-xs font-semibold bg-emerald-500 hover:bg-emerald-400 text-slate-950 rounded-lg shadow-md shadow-emerald-500/20 transition flex items-center gap-1.5"
              >
                <span>+</span> Add Capability
              </button>
            )}
          </div>

          {/* Capabilities List */}
          {(!facility.capabilities || facility.capabilities.length === 0) ? (
            <div className="text-center py-12 text-slate-500 text-xs">
              No specific capabilities or services cataloged for this facility yet.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {facility.capabilities.map((cap) => (
                <div
                  key={cap.id}
                  className="bg-slate-950/70 border border-slate-800 hover:border-slate-700 rounded-xl p-5 transition flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <span className="px-2.5 py-0.5 rounded text-[11px] font-mono font-semibold bg-slate-800 text-slate-300 border border-slate-700">
                        {cap.service_category}
                      </span>
                      <AvailabilityBadge status={cap.availability_status} />
                    </div>

                    <h3 className="text-sm font-bold text-white mb-2">{cap.service_name}</h3>

                    {/* Requirements Tags */}
                    <div className="flex flex-wrap gap-1.5 mb-3">
                      {cap.specialist_required && (
                        <span className="px-2 py-0.5 text-[10px] font-medium bg-purple-500/10 text-purple-300 border border-purple-500/30 rounded">
                          👨‍⚕️ Specialist Required
                        </span>
                      )}
                      {cap.diagnostic_required && (
                        <span className="px-2 py-0.5 text-[10px] font-medium bg-cyan-500/10 text-cyan-300 border border-cyan-500/30 rounded">
                          🔬 Diagnostic Equipment
                        </span>
                      )}
                      <span className="px-2 py-0.5 text-[10px] bg-slate-800 text-slate-400 rounded">
                        🕒 {cap.operating_hours || "24x7"}
                      </span>
                    </div>

                    {/* Capacity and Current Load */}
                    <div className="space-y-1 text-xs">
                      <div className="flex justify-between text-slate-400 text-[11px]">
                        <span>Daily Capacity & Load</span>
                        <span className="font-mono text-white">
                          {cap.current_load} / {cap.capacity} patients
                        </span>
                      </div>
                      <div className="w-full bg-slate-900 rounded-full h-1.5 border border-slate-800">
                        <div
                          className={`h-1.5 rounded-full ${
                            cap.current_load > cap.capacity * 0.85
                              ? "bg-rose-500"
                              : cap.current_load > cap.capacity * 0.6
                              ? "bg-amber-500"
                              : "bg-emerald-500"
                          }`}
                          style={{
                            width: `${
                              cap.capacity > 0
                                ? Math.min(100, (cap.current_load / cap.capacity) * 100)
                                : 0
                            }%`,
                          }}
                        ></div>
                      </div>
                    </div>
                  </div>

                  {canManage && (
                    <div className="mt-4 pt-3 border-t border-slate-800/80 flex justify-end">
                      <button
                        onClick={() => openEditCapModal(cap)}
                        className="px-2.5 py-1 text-[11px] font-semibold bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-md transition"
                      >
                        Edit Load & Status
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </main>

      {/* MODAL 1: EDIT FACILITY */}
      {showEditFacilityModal && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-xl w-full p-6 shadow-2xl my-8">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h3 className="text-base font-bold text-white">Edit Facility Details</h3>
              <button
                onClick={() => setShowEditFacilityModal(false)}
                className="text-slate-400 hover:text-white text-lg"
              >
                &times;
              </button>
            </div>

            {editFacilityError && (
              <div className="my-3 p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs">
                {editFacilityError}
              </div>
            )}

            <form onSubmit={handleEditFacilitySubmit} className="mt-4 space-y-4">
              <div>
                <label className="block text-xs text-slate-400 mb-1">Facility Name</label>
                <input
                  type="text"
                  value={editFacilityData.name || ""}
                  onChange={(e) =>
                    setEditFacilityData({ ...editFacilityData, name: e.target.value })
                  }
                  className="w-full px-3 py-2 text-xs bg-slate-950 border border-slate-800 rounded-lg text-white"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Helpline Phone</label>
                  <input
                    type="text"
                    value={editFacilityData.phone || ""}
                    onChange={(e) =>
                      setEditFacilityData({ ...editFacilityData, phone: e.target.value })
                    }
                    className="w-full px-3 py-2 text-xs bg-slate-950 border border-slate-800 rounded-lg text-white font-mono"
                  />
                </div>
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Operating Hours</label>
                  <input
                    type="text"
                    value={editFacilityData.operating_hours || ""}
                    onChange={(e) =>
                      setEditFacilityData({
                        ...editFacilityData,
                        operating_hours: e.target.value,
                      })
                    }
                    className="w-full px-3 py-2 text-xs bg-slate-950 border border-slate-800 rounded-lg text-white"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Total Beds</label>
                  <input
                    type="number"
                    min="0"
                    value={editFacilityData.total_beds ?? 0}
                    onChange={(e) =>
                      setEditFacilityData({
                        ...editFacilityData,
                        total_beds: parseInt(e.target.value) || 0,
                      })
                    }
                    className="w-full px-3 py-2 text-xs bg-slate-950 border border-slate-800 rounded-lg text-white font-mono"
                  />
                </div>
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Available Beds</label>
                  <input
                    type="number"
                    min="0"
                    value={editFacilityData.available_beds ?? 0}
                    onChange={(e) =>
                      setEditFacilityData({
                        ...editFacilityData,
                        available_beds: parseInt(e.target.value) || 0,
                      })
                    }
                    className="w-full px-3 py-2 text-xs bg-slate-950 border border-slate-800 rounded-lg text-white font-mono"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Total ICU Beds</label>
                  <input
                    type="number"
                    min="0"
                    value={editFacilityData.icu_beds ?? 0}
                    onChange={(e) =>
                      setEditFacilityData({
                        ...editFacilityData,
                        icu_beds: parseInt(e.target.value) || 0,
                      })
                    }
                    className="w-full px-3 py-2 text-xs bg-slate-950 border border-slate-800 rounded-lg text-white font-mono"
                  />
                </div>
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Available ICU Beds</label>
                  <input
                    type="number"
                    min="0"
                    value={editFacilityData.available_icu_beds ?? 0}
                    onChange={(e) =>
                      setEditFacilityData({
                        ...editFacilityData,
                        available_icu_beds: parseInt(e.target.value) || 0,
                      })
                    }
                    className="w-full px-3 py-2 text-xs bg-slate-950 border border-slate-800 rounded-lg text-white font-mono"
                  />
                </div>
              </div>

              <div className="flex items-center gap-2 pt-2">
                <input
                  type="checkbox"
                  id="edit_is_active"
                  checked={editFacilityData.is_active ?? true}
                  onChange={(e) =>
                    setEditFacilityData({
                      ...editFacilityData,
                      is_active: e.target.checked,
                    })
                  }
                  className="rounded border-slate-800 text-emerald-500"
                />
                <label htmlFor="edit_is_active" className="text-xs text-slate-300">
                  Facility is actively accepting care requests
                </label>
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowEditFacilityModal(false)}
                  className="px-4 py-2 text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={editFacilitySubmitting}
                  className="px-5 py-2 text-xs font-bold bg-emerald-500 hover:bg-emerald-400 text-slate-950 rounded-lg transition disabled:opacity-50"
                >
                  {editFacilitySubmitting ? "Saving..." : "Save Changes"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 2: ADD CAPABILITY */}
      {showAddCapModal && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl my-8">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h3 className="text-base font-bold text-white">Add Facility Capability</h3>
              <button
                onClick={() => setShowAddCapModal(false)}
                className="text-slate-400 hover:text-white text-lg"
              >
                &times;
              </button>
            </div>

            {capError && (
              <div className="my-3 p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs">
                {capError}
              </div>
            )}

            <form onSubmit={handleAddCapabilitySubmit} className="mt-4 space-y-4">
              <div>
                <label className="block text-xs text-slate-300 mb-1">Service / Procedure Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. 128-Slice Computed Tomography (CT)"
                  value={newCapData.service_name}
                  onChange={(e) =>
                    setNewCapData({ ...newCapData, service_name: e.target.value })
                  }
                  className="w-full px-3 py-2 text-xs bg-slate-950 border border-slate-800 rounded-lg text-white"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-slate-300 mb-1">Service Category *</label>
                  <select
                    value={newCapData.service_category}
                    onChange={(e) =>
                      setNewCapData({
                        ...newCapData,
                        service_category: e.target.value as ServiceCategory,
                      })
                    }
                    className="w-full px-3 py-2 text-xs bg-slate-950 border border-slate-800 rounded-lg text-white"
                  >
                    {SERVICE_CATEGORIES.map((cat) => (
                      <option key={cat.value} value={cat.value}>
                        {cat.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs text-slate-300 mb-1">Availability Status</label>
                  <select
                    value={newCapData.availability_status}
                    onChange={(e) =>
                      setNewCapData({
                        ...newCapData,
                        availability_status: e.target.value as AvailabilityStatus,
                      })
                    }
                    className="w-full px-3 py-2 text-xs bg-slate-950 border border-slate-800 rounded-lg text-white"
                  >
                    <option value="AVAILABLE">AVAILABLE (Operational)</option>
                    <option value="LIMITED">LIMITED</option>
                    <option value="HIGH_LOAD">HIGH_LOAD</option>
                    <option value="UNAVAILABLE">UNAVAILABLE</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-slate-300 mb-1">Daily Capacity (Max)</label>
                  <input
                    type="number"
                    min="0"
                    value={newCapData.capacity}
                    onChange={(e) =>
                      setNewCapData({
                        ...newCapData,
                        capacity: parseInt(e.target.value) || 0,
                      })
                    }
                    className="w-full px-3 py-2 text-xs bg-slate-950 border border-slate-800 rounded-lg text-white font-mono"
                  />
                </div>

                <div>
                  <label className="block text-xs text-slate-300 mb-1">Current Load / Queue</label>
                  <input
                    type="number"
                    min="0"
                    value={newCapData.current_load}
                    onChange={(e) =>
                      setNewCapData({
                        ...newCapData,
                        current_load: parseInt(e.target.value) || 0,
                      })
                    }
                    className="w-full px-3 py-2 text-xs bg-slate-950 border border-slate-800 rounded-lg text-white font-mono"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs text-slate-300 mb-1">Operating Hours</label>
                <input
                  type="text"
                  placeholder="24x7 or 08:00 - 20:00"
                  value={newCapData.operating_hours || "24x7"}
                  onChange={(e) =>
                    setNewCapData({ ...newCapData, operating_hours: e.target.value })
                  }
                  className="w-full px-3 py-2 text-xs bg-slate-950 border border-slate-800 rounded-lg text-white"
                />
              </div>

              <div className="space-y-2 pt-1">
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="spec_req"
                    checked={newCapData.specialist_required}
                    onChange={(e) =>
                      setNewCapData({
                        ...newCapData,
                        specialist_required: e.target.checked,
                      })
                    }
                    className="rounded border-slate-800 text-emerald-500"
                  />
                  <label htmlFor="spec_req" className="text-xs text-slate-300">
                    Specialist Doctor presence required
                  </label>
                </div>

                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="diag_req"
                    checked={newCapData.diagnostic_required}
                    onChange={(e) =>
                      setNewCapData({
                        ...newCapData,
                        diagnostic_required: e.target.checked,
                      })
                    }
                    className="rounded border-slate-800 text-emerald-500"
                  />
                  <label htmlFor="diag_req" className="text-xs text-slate-300">
                    Specialized diagnostic instrumentation involved
                  </label>
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowAddCapModal(false)}
                  className="px-4 py-2 text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={capSubmitting}
                  className="px-5 py-2 text-xs font-bold bg-emerald-500 hover:bg-emerald-400 text-slate-950 rounded-lg transition disabled:opacity-50"
                >
                  {capSubmitting ? "Adding..." : "Add Capability"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 3: EDIT CAPABILITY */}
      {editingCapability && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl my-8">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h3 className="text-base font-bold text-white">
                Update Capability: {editingCapability.service_name}
              </h3>
              <button
                onClick={() => setEditingCapability(null)}
                className="text-slate-400 hover:text-white text-lg"
              >
                &times;
              </button>
            </div>

            {editCapError && (
              <div className="my-3 p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs">
                {editCapError}
              </div>
            )}

            <form onSubmit={handleEditCapabilitySubmit} className="mt-4 space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-slate-300 mb-1">Availability Status</label>
                  <select
                    value={editCapData.availability_status}
                    onChange={(e) =>
                      setEditCapData({
                        ...editCapData,
                        availability_status: e.target.value as AvailabilityStatus,
                      })
                    }
                    className="w-full px-3 py-2 text-xs bg-slate-950 border border-slate-800 rounded-lg text-white"
                  >
                    <option value="AVAILABLE">AVAILABLE (Operational)</option>
                    <option value="LIMITED">LIMITED</option>
                    <option value="HIGH_LOAD">HIGH_LOAD</option>
                    <option value="UNAVAILABLE">UNAVAILABLE</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs text-slate-300 mb-1">Operating Hours</label>
                  <input
                    type="text"
                    value={editCapData.operating_hours || ""}
                    onChange={(e) =>
                      setEditCapData({ ...editCapData, operating_hours: e.target.value })
                    }
                    className="w-full px-3 py-2 text-xs bg-slate-950 border border-slate-800 rounded-lg text-white"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-slate-300 mb-1">Capacity</label>
                  <input
                    type="number"
                    min="0"
                    value={editCapData.capacity ?? 0}
                    onChange={(e) =>
                      setEditCapData({
                        ...editCapData,
                        capacity: parseInt(e.target.value) || 0,
                      })
                    }
                    className="w-full px-3 py-2 text-xs bg-slate-950 border border-slate-800 rounded-lg text-white font-mono"
                  />
                </div>

                <div>
                  <label className="block text-xs text-slate-300 mb-1">Current Load</label>
                  <input
                    type="number"
                    min="0"
                    value={editCapData.current_load ?? 0}
                    onChange={(e) =>
                      setEditCapData({
                        ...editCapData,
                        current_load: parseInt(e.target.value) || 0,
                      })
                    }
                    className="w-full px-3 py-2 text-xs bg-slate-950 border border-slate-800 rounded-lg text-white font-mono"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setEditingCapability(null)}
                  className="px-4 py-2 text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={editCapSubmitting}
                  className="px-5 py-2 text-xs font-bold bg-emerald-500 hover:bg-emerald-400 text-slate-950 rounded-lg transition disabled:opacity-50"
                >
                  {editCapSubmitting ? "Updating..." : "Save Capability"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default function FacilityDetailPage() {
  return (
    <ProtectedRoute>
      <FacilityDetailContent />
    </ProtectedRoute>
  );
}

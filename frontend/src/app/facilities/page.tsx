"use client";

import React, { useState, useEffect, useTransition } from "react";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import {
  getFacilities,
  getNearbyFacilities,
  createFacility,
} from "@/lib/facilityApi";
import {
  Facility,
  FacilityType,
  FacilityCreateInput,
  NearbyFacilityItem,
} from "@/types/facility";
import { ApiError } from "@/lib/api";

const ALLOWED_MANAGE_ROLES = ["ADMIN", "DISTRICT_ADMIN", "FACILITY_ADMIN"];

const FACILITY_TYPES: { value: FacilityType; label: string; tier: number }[] = [
  { value: "AAM", label: "Ayushman Arogya Mandir (AAM)", tier: 1 },
  { value: "SUB_CENTER", label: "Health Sub-Center", tier: 1 },
  { value: "PHC", label: "Primary Health Centre (PHC)", tier: 2 },
  { value: "CHC", label: "Community Health Centre (CHC)", tier: 3 },
  { value: "RURAL_HOSPITAL", label: "Sub-Divisional / Rural Hospital", tier: 4 },
  { value: "DISTRICT_HOSPITAL", label: "District Headquarters Hospital (DHH)", tier: 4 },
  { value: "DIAGNOSTIC_CENTER", label: "Diagnostic & Imaging Centre", tier: 4 },
  { value: "SPECIALTY_HOSPITAL", label: "Tertiary / Specialty Hospital", tier: 5 },
];

function FacilityTypeBadge({ type }: { type: string }) {
  switch (type) {
    case "SPECIALTY_HOSPITAL":
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-purple-500/20 text-purple-300 border border-purple-500/40">
          Tier 5 • Specialty Hospital
        </span>
      );
    case "DISTRICT_HOSPITAL":
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-blue-500/20 text-blue-300 border border-blue-500/40">
          Tier 4 • District Hospital
        </span>
      );
    case "RURAL_HOSPITAL":
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/40">
          Tier 4 • Rural Hospital
        </span>
      );
    case "DIAGNOSTIC_CENTER":
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/20 text-amber-300 border border-amber-500/40">
          Tier 4 • Diagnostic Center
        </span>
      );
    case "CHC":
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
          Tier 3 • CHC
        </span>
      );
    case "PHC":
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-teal-500/20 text-teal-300 border border-teal-500/40">
          Tier 2 • PHC
        </span>
      );
    case "SUB_CENTER":
    case "AAM":
    default:
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-800 text-slate-300 border border-slate-700">
          Tier 1 • Primary Care
        </span>
      );
  }
}

function FacilitiesContent() {
  const { user, token } = useAuth();
  const [, startTransition] = useTransition();

  // Mode: Directory list vs Geospatial Proximity Search
  const [activeTab, setActiveTab] = useState<"directory" | "nearby">("directory");

  // Directory State
  const [facilities, setFacilities] = useState<Facility[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [searchTerm, setSearchTerm] = useState("");
  const [filterType, setFilterType] = useState<string>("");
  const [filterDistrict, setFilterDistrict] = useState<string>("");
  const [filterActive, setFilterActive] = useState<string>("");

  // Geospatial Search State
  const [geoLat, setGeoLat] = useState<number>(22.25);
  const [geoLon, setGeoLon] = useState<number>(84.88);
  const [geoRadius, setGeoRadius] = useState<number>(25);
  const [nearbyResults, setNearbyResults] = useState<NearbyFacilityItem[]>([]);
  const [nearbyLoading, setNearbyLoading] = useState(false);
  const [nearbySearched, setNearbySearched] = useState(false);

  // Create Facility Modal State
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [createSubmitting, setCreateSubmitting] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);
  const [createSuccess, setCreateSuccess] = useState(false);

  const [formData, setFormData] = useState<FacilityCreateInput>({
    name: "",
    code: "",
    facility_type: "PHC",
    district: "Sundargarh",
    state: "Odisha",
    address: "",
    pincode: "770001",
    latitude: 22.25,
    longitude: 84.88,
    phone: "",
    operating_hours: "24x7",
    is_active: true,
    total_beds: 10,
    available_beds: 6,
    icu_beds: 0,
    available_icu_beds: 0,
  });

  const canManage = user?.role && ALLOWED_MANAGE_ROLES.includes(user.role);

  const [activeFilters, setActiveFilters] = useState({
    search: "",
    type: "",
    district: "",
    active: "",
  });
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    let isMounted = true;

    async function loadFacilities() {
      try {
        const activeParam =
          activeFilters.active === "true"
            ? true
            : activeFilters.active === "false"
            ? false
            : undefined;
        const res = await getFacilities(
          {
            page,
            page_size: 9,
            facility_type: activeFilters.type || undefined,
            district: activeFilters.district || undefined,
            is_active: activeParam,
            search: activeFilters.search || undefined,
          },
          token
        );
        if (isMounted) {
          setFacilities(res.items);
          setTotal(res.total);
          setPage(res.page);
          setTotalPages(res.total_pages);
          setError(null);
        }
      } catch (err: unknown) {
        if (isMounted) {
          if (err instanceof ApiError) {
            setError(err.message);
          } else {
            setError("Failed to load facilities. Please check network connection.");
          }
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    }

    loadFacilities();

    return () => {
      isMounted = false;
    };
  }, [page, activeFilters, reloadKey, token]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setPage(1);
    setActiveFilters({
      search: searchTerm,
      type: filterType,
      district: filterDistrict,
      active: filterActive,
    });
  };

  const handleNearbySearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setNearbyLoading(true);
    setError(null);
    try {
      const res = await getNearbyFacilities(
        {
          latitude: geoLat,
          longitude: geoLon,
          radius_km: geoRadius,
        },
        token
      );
      setNearbyResults(res.items);
      setNearbySearched(true);
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to execute nearby facility lookup.");
      }
    } finally {
      setNearbyLoading(false);
    }
  };

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreateSubmitting(true);
    setCreateError(null);
    try {
      await createFacility(formData, token);
      setCreateSuccess(true);
      setTimeout(() => {
        setShowCreateModal(false);
        setCreateSuccess(false);
        setFormData({
          name: "",
          code: "",
          facility_type: "PHC",
          district: "Sundargarh",
          state: "Odisha",
          address: "",
          pincode: "770001",
          latitude: 22.25,
          longitude: 84.88,
          phone: "",
          operating_hours: "24x7",
          is_active: true,
          total_beds: 10,
          available_beds: 6,
          icu_beds: 0,
          available_icu_beds: 0,
        });
        setReloadKey((k) => k + 1);
      }, 1000);
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setCreateError(err.message);
      } else {
        setCreateError("Failed to register facility. Please verify inputs.");
      }
    } finally {
      setCreateSubmitting(false);
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
            <span className="hidden sm:inline-block text-xs uppercase tracking-wider text-slate-400 border-l border-slate-700 pl-3">
              Facility Infrastructure Directory
            </span>
          </div>

          <div className="flex items-center gap-3">
            <Link
              href="/dashboard"
              className="px-3 py-1.5 text-xs font-medium text-slate-400 hover:text-white border border-slate-800 rounded-lg hover:bg-slate-800/60 transition"
            >
              Dashboard
            </Link>
            {canManage && (
              <button
                onClick={() => setShowCreateModal(true)}
                className="px-3.5 py-1.5 text-xs font-semibold bg-emerald-500 hover:bg-emerald-400 text-slate-950 rounded-lg shadow-lg shadow-emerald-500/20 transition flex items-center gap-1.5"
              >
                <span>+</span> Add Facility
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Module Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
          <div>
            <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded-full text-xs font-medium bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 mb-2">
              <span className="h-1.5 w-1.5 rounded-full bg-cyan-400"></span>
              Infrastructure Registry & Geospatial Network
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              Healthcare Facilities & Capabilities
            </h1>
            <p className="mt-1 text-xs sm:text-sm text-slate-400">
              Browse public health institutions, inspect verified specialized services, bed capacity, and locate nearby centers.
            </p>
          </div>

          {/* Mode Tabs */}
          <div className="flex items-center bg-slate-900 border border-slate-800 p-1 rounded-xl">
            <button
              onClick={() => {
                setActiveTab("directory");
                startTransition(() => {});
              }}
              className={`px-4 py-2 text-xs font-semibold rounded-lg transition ${
                activeTab === "directory"
                  ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 shadow-sm"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              🏢 Directory ({total})
            </button>
            <button
              onClick={() => {
                setActiveTab("nearby");
                startTransition(() => {});
              }}
              className={`px-4 py-2 text-xs font-semibold rounded-lg transition ${
                activeTab === "nearby"
                  ? "bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 shadow-sm"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              📍 Nearby Radius Lookup
            </button>
          </div>
        </div>

        {/* TAB 1: DIRECTORY VIEW */}
        {activeTab === "directory" && (
          <>
            {/* Filter & Search Toolbar */}
            <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 mb-6">
              <form onSubmit={handleSearchSubmit} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
                <div className="lg:col-span-2">
                  <input
                    type="text"
                    placeholder="Search by facility name, code, town, or address..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full px-3.5 py-2 text-xs bg-slate-950 border border-slate-800 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500"
                  />
                </div>

                <div>
                  <select
                    value={filterType}
                    onChange={(e) => setFilterType(e.target.value)}
                    className="w-full px-3 py-2 text-xs bg-slate-950 border border-slate-800 rounded-lg text-slate-300 focus:outline-none focus:border-emerald-500"
                  >
                    <option value="">All Facility Types</option>
                    {FACILITY_TYPES.map((t) => (
                      <option key={t.value} value={t.value}>
                        {t.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <select
                    value={filterDistrict}
                    onChange={(e) => setFilterDistrict(e.target.value)}
                    className="w-full px-3 py-2 text-xs bg-slate-950 border border-slate-800 rounded-lg text-slate-300 focus:outline-none focus:border-emerald-500"
                  >
                    <option value="">All Districts</option>
                    <option value="Sundargarh">Sundargarh</option>
                    <option value="Sambalpur">Sambalpur</option>
                    <option value="Jharsuguda">Jharsuguda</option>
                  </select>
                </div>

                <div className="flex items-center gap-2">
                  <select
                    value={filterActive}
                    onChange={(e) => setFilterActive(e.target.value)}
                    className="w-full px-3 py-2 text-xs bg-slate-950 border border-slate-800 rounded-lg text-slate-300 focus:outline-none focus:border-emerald-500"
                  >
                    <option value="">All Statuses</option>
                    <option value="true">Active Only</option>
                    <option value="false">Inactive</option>
                  </select>
                  <button
                    type="submit"
                    className="px-4 py-2 text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg transition"
                  >
                    Search
                  </button>
                </div>
              </form>
            </div>

            {/* Error Alert */}
            {error && (
              <div className="p-4 mb-6 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs">
                {error}
              </div>
            )}

            {/* Loading State */}
            {loading && (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {[1, 2, 3, 4, 5, 6].map((i) => (
                  <div
                    key={i}
                    className="h-64 rounded-xl bg-slate-900/40 border border-slate-800 animate-pulse p-6"
                  ></div>
                ))}
              </div>
            )}

            {/* Empty State */}
            {!loading && facilities.length === 0 && (
              <div className="text-center py-16 bg-slate-900/30 border border-slate-800/80 rounded-2xl p-8">
                <div className="text-4xl mb-3">🏥</div>
                <h3 className="text-base font-bold text-white">No Healthcare Facilities Found</h3>
                <p className="mt-1 text-xs text-slate-400 max-w-sm mx-auto">
                  No registered health infrastructure matches your current search and filter settings.
                </p>
                <button
                  onClick={() => {
                    setSearchTerm("");
                    setFilterType("");
                    setFilterDistrict("");
                    setFilterActive("");
                    setPage(1);
                    setActiveFilters({ search: "", type: "", district: "", active: "" });
                  }}
                  className="mt-4 px-4 py-1.5 text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition"
                >
                  Clear All Filters
                </button>
              </div>
            )}

            {/* Facilities Cards Grid */}
            {!loading && facilities.length > 0 && (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {facilities.map((fac) => (
                  <div
                    key={fac.id}
                    className="group bg-slate-900/60 hover:bg-slate-900/90 border border-slate-800 hover:border-emerald-500/40 rounded-2xl p-6 transition flex flex-col justify-between shadow-lg"
                  >
                    <div>
                      {/* Card Header: Type Badge & Status */}
                      <div className="flex items-start justify-between gap-2 mb-3">
                        <FacilityTypeBadge type={fac.facility_type} />
                        <span
                          className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono uppercase ${
                            fac.is_active
                              ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                              : "bg-slate-800 text-slate-400"
                          }`}
                        >
                          <span
                            className={`h-1.5 w-1.5 rounded-full ${
                              fac.is_active ? "bg-emerald-400" : "bg-slate-500"
                            }`}
                          ></span>
                          {fac.is_active ? "Active" : "Inactive"}
                        </span>
                      </div>

                      {/* Name & Code */}
                      <h3 className="text-base font-bold text-white group-hover:text-emerald-400 transition">
                        {fac.name}
                      </h3>
                      {fac.code && (
                        <p className="text-[11px] font-mono text-slate-400 mt-0.5">
                          Code: {fac.code}
                        </p>
                      )}

                      {/* Location & Contact */}
                      <div className="mt-3 space-y-1 text-xs text-slate-400">
                        <p className="flex items-center gap-1.5">
                          <span>📍</span>
                          <span>
                            {fac.address ? `${fac.address}, ` : ""}
                            {fac.district}, {fac.state}
                          </span>
                        </p>
                        {fac.phone && (
                          <p className="flex items-center gap-1.5 font-mono text-slate-300">
                            <span>📞</span> {fac.phone}
                          </p>
                        )}
                        <p className="flex items-center gap-1.5 text-slate-400 text-[11px]">
                          <span>🕒</span> Hours: {fac.operating_hours || "24x7"}
                        </p>
                      </div>

                      {/* Bed & Capability Summary */}
                      <div className="mt-4 pt-3 border-t border-slate-800/80 grid grid-cols-2 gap-2 text-xs">
                        <div className="bg-slate-950/60 p-2 rounded-lg border border-slate-800/60">
                          <span className="text-[10px] text-slate-500 block uppercase">Inpatient Beds</span>
                          <span className="font-mono font-semibold text-emerald-400">
                            {fac.available_beds} / {fac.total_beds} Avail
                          </span>
                        </div>
                        <div className="bg-slate-950/60 p-2 rounded-lg border border-slate-800/60">
                          <span className="text-[10px] text-slate-500 block uppercase">ICU Beds</span>
                          <span className="font-mono font-semibold text-cyan-400">
                            {fac.available_icu_beds} / {fac.icu_beds} Avail
                          </span>
                        </div>
                      </div>

                      {/* Capabilities Snapshot */}
                      <div className="mt-3">
                        <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
                          Services ({fac.capabilities?.length || 0})
                        </span>
                        <div className="flex flex-wrap gap-1">
                          {(fac.capabilities || []).slice(0, 3).map((cap) => (
                            <span
                              key={cap.id}
                              className="px-2 py-0.5 text-[10px] bg-slate-800 text-slate-300 rounded border border-slate-700/60 truncate max-w-[140px]"
                            >
                              {cap.service_name}
                            </span>
                          ))}
                          {(fac.capabilities || []).length > 3 && (
                            <span className="px-1.5 py-0.5 text-[10px] bg-slate-800 text-slate-400 rounded">
                              +{(fac.capabilities || []).length - 3} more
                            </span>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Action Button */}
                    <div className="mt-6 pt-4 border-t border-slate-800 flex items-center justify-between">
                      <span className="text-[11px] font-mono text-slate-500">
                        Lat: {fac.latitude.toFixed(2)}, Lon: {fac.longitude.toFixed(2)}
                      </span>
                      <Link
                        href={`/facilities/${fac.id}`}
                        className="px-3 py-1.5 text-xs font-semibold bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 rounded-lg transition flex items-center gap-1"
                      >
                        View Profile &rarr;
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Pagination */}
            {!loading && totalPages > 1 && (
              <div className="mt-8 flex items-center justify-between bg-slate-900/60 border border-slate-800 rounded-xl px-4 py-3 text-xs">
                <span className="text-slate-400">
                  Page <strong className="text-white">{page}</strong> of{" "}
                  <strong className="text-white">{totalPages}</strong> ({total} facilities)
                </span>
                <div className="flex gap-2">
                  <button
                    disabled={page <= 1}
                    onClick={() => {
                      setLoading(true);
                      setPage((p) => Math.max(1, p - 1));
                    }}
                    className="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 disabled:opacity-40 disabled:cursor-not-allowed rounded-lg transition"
                  >
                    Previous
                  </button>
                  <button
                    disabled={page >= totalPages}
                    onClick={() => {
                      setLoading(true);
                      setPage((p) => p + 1);
                    }}
                    className="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 disabled:opacity-40 disabled:cursor-not-allowed rounded-lg transition"
                  >
                    Next
                  </button>
                </div>
              </div>
            )}
          </>
        )}

        {/* TAB 2: GEOSPATIAL NEARBY LOOKUP */}
        {activeTab === "nearby" && (
          <div className="space-y-6">
            {/* Coordinates & Radius Control Panel */}
            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6">
              <h2 className="text-sm font-semibold uppercase tracking-wider text-cyan-400 mb-2">
                Geographic Proximity Search (Haversine Radius Lookup)
              </h2>
              <p className="text-xs text-slate-400 mb-5">
                Calculate real-time distances to active healthcare infrastructure within a specified kilometer radius.
              </p>

              <form onSubmit={handleNearbySearch} className="space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-xs text-slate-400 mb-1">Center Latitude</label>
                    <input
                      type="number"
                      step="any"
                      value={geoLat}
                      onChange={(e) => setGeoLat(parseFloat(e.target.value))}
                      className="w-full px-3 py-2 text-xs bg-slate-950 border border-slate-800 rounded-lg text-white font-mono focus:outline-none focus:border-cyan-500"
                    />
                  </div>

                  <div>
                    <label className="block text-xs text-slate-400 mb-1">Center Longitude</label>
                    <input
                      type="number"
                      step="any"
                      value={geoLon}
                      onChange={(e) => setGeoLon(parseFloat(e.target.value))}
                      className="w-full px-3 py-2 text-xs bg-slate-950 border border-slate-800 rounded-lg text-white font-mono focus:outline-none focus:border-cyan-500"
                    />
                  </div>

                  <div>
                    <div className="flex justify-between items-center mb-1">
                      <label className="text-xs text-slate-400">Search Radius</label>
                      <span className="text-xs font-mono text-cyan-400 font-bold">{geoRadius} km</span>
                    </div>
                    <input
                      type="range"
                      min="1"
                      max="100"
                      value={geoRadius}
                      onChange={(e) => setGeoRadius(parseInt(e.target.value))}
                      className="w-full accent-cyan-400 cursor-pointer"
                    />
                  </div>
                </div>

                {/* Quick Coordinates Presets */}
                <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-slate-800/80">
                  <span className="text-[11px] text-slate-500 uppercase tracking-wider">Presets:</span>
                  <button
                    type="button"
                    onClick={() => {
                      setGeoLat(22.2499);
                      setGeoLon(84.8828);
                    }}
                    className="px-2.5 py-1 text-[11px] bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-md transition"
                  >
                    Rourkela (22.25, 84.88)
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setGeoLat(22.1812);
                      setGeoLon(84.7315);
                    }}
                    className="px-2.5 py-1 text-[11px] bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-md transition"
                  >
                    Kansbahal (22.18, 84.73)
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setGeoLat(22.1200);
                      setGeoLon(84.0300);
                    }}
                    className="px-2.5 py-1 text-[11px] bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-md transition"
                  >
                    Sundargarh Town (22.12, 84.03)
                  </button>
                </div>

                <div className="flex justify-end pt-2">
                  <button
                    type="submit"
                    disabled={nearbyLoading}
                    className="px-5 py-2 text-xs font-bold bg-cyan-500 hover:bg-cyan-400 text-slate-950 rounded-xl transition shadow-lg shadow-cyan-500/20 disabled:opacity-50"
                  >
                    {nearbyLoading ? "Searching Radius..." : "Lookup Facilities in Radius"}
                  </button>
                </div>
              </form>
            </div>

            {/* Nearby Results */}
            {nearbySearched && (
              <div>
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-bold text-white">
                    Found {nearbyResults.length} active facilities within {geoRadius} km
                  </h3>
                  <span className="text-xs font-mono text-slate-400">
                    Center: ({geoLat.toFixed(4)}, {geoLon.toFixed(4)})
                  </span>
                </div>

                {nearbyResults.length === 0 ? (
                  <div className="p-8 text-center bg-slate-900/40 border border-slate-800 rounded-xl text-slate-400 text-xs">
                    No active facilities found within {geoRadius} km of these coordinates. Try expanding the radius slider.
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {nearbyResults.map(({ facility, distance_km }) => (
                      <div
                        key={facility.id}
                        className="bg-slate-900/80 border border-slate-800 hover:border-cyan-500/40 rounded-2xl p-6 transition flex flex-col justify-between shadow-lg"
                      >
                        <div>
                          <div className="flex items-start justify-between gap-2 mb-3">
                            <FacilityTypeBadge type={facility.facility_type} />
                            <span className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-mono font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/40">
                              📍 {distance_km.toFixed(2)} km
                            </span>
                          </div>

                          <h4 className="text-base font-bold text-white mb-1">{facility.name}</h4>
                          <p className="text-xs text-slate-400 mb-3">
                            {facility.address ? `${facility.address}, ` : ""}
                            {facility.district}
                          </p>

                          <div className="grid grid-cols-2 gap-2 text-xs mb-3">
                            <div className="bg-slate-950/60 p-2 rounded-lg border border-slate-800/60">
                              <span className="text-[10px] text-slate-500 block uppercase">Beds Avail</span>
                              <span className="font-mono font-semibold text-emerald-400">
                                {facility.available_beds} / {facility.total_beds}
                              </span>
                            </div>
                            <div className="bg-slate-950/60 p-2 rounded-lg border border-slate-800/60">
                              <span className="text-[10px] text-slate-500 block uppercase">ICU Avail</span>
                              <span className="font-mono font-semibold text-cyan-400">
                                {facility.available_icu_beds} / {facility.icu_beds}
                              </span>
                            </div>
                          </div>
                        </div>

                        <div className="pt-4 border-t border-slate-800 flex justify-end">
                          <Link
                            href={`/facilities/${facility.id}`}
                            className="px-3 py-1.5 text-xs font-semibold bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 rounded-lg transition"
                          >
                            View Facility & Capabilities &rarr;
                          </Link>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </main>

      {/* CREATE FACILITY MODAL */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-2xl w-full p-6 shadow-2xl my-8">
            <div className="flex items-center justify-between pb-4 border-b border-slate-800">
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <span>🏥</span> Register Healthcare Facility
              </h2>
              <button
                onClick={() => setShowCreateModal(false)}
                className="text-slate-400 hover:text-white text-lg leading-none"
              >
                &times;
              </button>
            </div>

            {createError && (
              <div className="my-4 p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs">
                {createError}
              </div>
            )}

            {createSuccess && (
              <div className="my-4 p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs">
                Facility registered successfully! Refreshing registry...
              </div>
            )}

            <form onSubmit={handleCreateSubmit} className="mt-4 space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="sm:col-span-2">
                  <label className="block text-xs text-slate-300 font-medium mb-1">
                    Facility Name *
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Primary Health Centre - Lathikata"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full px-3.5 py-2 text-xs bg-slate-950 border border-slate-800 rounded-lg text-white focus:outline-none focus:border-emerald-500"
                  />
                </div>

                <div>
                  <label className="block text-xs text-slate-300 font-medium mb-1">
                    Facility Type *
                  </label>
                  <select
                    value={formData.facility_type}
                    onChange={(e) =>
                      setFormData({ ...formData, facility_type: e.target.value as FacilityType })
                    }
                    className="w-full px-3 py-2 text-xs bg-slate-950 border border-slate-800 rounded-lg text-slate-200 focus:outline-none focus:border-emerald-500"
                  >
                    {FACILITY_TYPES.map((t) => (
                      <option key={t.value} value={t.value}>
                        {t.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs text-slate-300 font-medium mb-1">
                    Facility Code (ABDM / NIN)
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. FAC-OR-SNG-PHC01"
                    value={formData.code || ""}
                    onChange={(e) => setFormData({ ...formData, code: e.target.value })}
                    className="w-full px-3.5 py-2 text-xs bg-slate-950 border border-slate-800 rounded-lg text-white font-mono focus:outline-none focus:border-emerald-500"
                  />
                </div>

                <div>
                  <label className="block text-xs text-slate-300 font-medium mb-1">District *</label>
                  <input
                    type="text"
                    required
                    value={formData.district}
                    onChange={(e) => setFormData({ ...formData, district: e.target.value })}
                    className="w-full px-3.5 py-2 text-xs bg-slate-950 border border-slate-800 rounded-lg text-white focus:outline-none focus:border-emerald-500"
                  />
                </div>

                <div>
                  <label className="block text-xs text-slate-300 font-medium mb-1">State *</label>
                  <input
                    type="text"
                    required
                    value={formData.state}
                    onChange={(e) => setFormData({ ...formData, state: e.target.value })}
                    className="w-full px-3.5 py-2 text-xs bg-slate-950 border border-slate-800 rounded-lg text-white focus:outline-none focus:border-emerald-500"
                  />
                </div>

                <div className="sm:col-span-2">
                  <label className="block text-xs text-slate-300 font-medium mb-1">
                    Street Address / Landmark
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. Main Hospital Road, Block Headquarters"
                    value={formData.address || ""}
                    onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                    className="w-full px-3.5 py-2 text-xs bg-slate-950 border border-slate-800 rounded-lg text-white focus:outline-none focus:border-emerald-500"
                  />
                </div>

                <div>
                  <label className="block text-xs text-slate-300 font-medium mb-1">
                    GPS Latitude (-90 to 90) *
                  </label>
                  <input
                    type="number"
                    step="any"
                    required
                    value={formData.latitude}
                    onChange={(e) =>
                      setFormData({ ...formData, latitude: parseFloat(e.target.value) || 0 })
                    }
                    className="w-full px-3.5 py-2 text-xs bg-slate-950 border border-slate-800 rounded-lg text-white font-mono focus:outline-none focus:border-emerald-500"
                  />
                </div>

                <div>
                  <label className="block text-xs text-slate-300 font-medium mb-1">
                    GPS Longitude (-180 to 180) *
                  </label>
                  <input
                    type="number"
                    step="any"
                    required
                    value={formData.longitude}
                    onChange={(e) =>
                      setFormData({ ...formData, longitude: parseFloat(e.target.value) || 0 })
                    }
                    className="w-full px-3.5 py-2 text-xs bg-slate-950 border border-slate-800 rounded-lg text-white font-mono focus:outline-none focus:border-emerald-500"
                  />
                </div>

                <div>
                  <label className="block text-xs text-slate-300 font-medium mb-1">
                    Helpline / Phone
                  </label>
                  <input
                    type="text"
                    placeholder="+916624200000"
                    value={formData.phone || ""}
                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                    className="w-full px-3.5 py-2 text-xs bg-slate-950 border border-slate-800 rounded-lg text-white font-mono focus:outline-none focus:border-emerald-500"
                  />
                </div>

                <div>
                  <label className="block text-xs text-slate-300 font-medium mb-1">
                    Operating Hours
                  </label>
                  <input
                    type="text"
                    placeholder="24x7 or 09:00 - 17:00"
                    value={formData.operating_hours || "24x7"}
                    onChange={(e) =>
                      setFormData({ ...formData, operating_hours: e.target.value })
                    }
                    className="w-full px-3.5 py-2 text-xs bg-slate-950 border border-slate-800 rounded-lg text-white focus:outline-none focus:border-emerald-500"
                  />
                </div>

                <div>
                  <label className="block text-xs text-slate-300 font-medium mb-1">
                    Total Inpatient Beds
                  </label>
                  <input
                    type="number"
                    min="0"
                    value={formData.total_beds}
                    onChange={(e) =>
                      setFormData({ ...formData, total_beds: parseInt(e.target.value) || 0 })
                    }
                    className="w-full px-3.5 py-2 text-xs bg-slate-950 border border-slate-800 rounded-lg text-white font-mono focus:outline-none focus:border-emerald-500"
                  />
                </div>

                <div>
                  <label className="block text-xs text-slate-300 font-medium mb-1">
                    Available Beds
                  </label>
                  <input
                    type="number"
                    min="0"
                    value={formData.available_beds}
                    onChange={(e) =>
                      setFormData({ ...formData, available_beds: parseInt(e.target.value) || 0 })
                    }
                    className="w-full px-3.5 py-2 text-xs bg-slate-950 border border-slate-800 rounded-lg text-white font-mono focus:outline-none focus:border-emerald-500"
                  />
                </div>

                <div>
                  <label className="block text-xs text-slate-300 font-medium mb-1">
                    Total ICU Beds
                  </label>
                  <input
                    type="number"
                    min="0"
                    value={formData.icu_beds}
                    onChange={(e) =>
                      setFormData({ ...formData, icu_beds: parseInt(e.target.value) || 0 })
                    }
                    className="w-full px-3.5 py-2 text-xs bg-slate-950 border border-slate-800 rounded-lg text-white font-mono focus:outline-none focus:border-emerald-500"
                  />
                </div>

                <div>
                  <label className="block text-xs text-slate-300 font-medium mb-1">
                    Available ICU Beds
                  </label>
                  <input
                    type="number"
                    min="0"
                    value={formData.available_icu_beds}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        available_icu_beds: parseInt(e.target.value) || 0,
                      })
                    }
                    className="w-full px-3.5 py-2 text-xs bg-slate-950 border border-slate-800 rounded-lg text-white font-mono focus:outline-none focus:border-emerald-500"
                  />
                </div>
              </div>

              <div className="flex items-center gap-2 pt-2">
                <input
                  type="checkbox"
                  id="is_active"
                  checked={formData.is_active}
                  onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                  className="rounded border-slate-800 text-emerald-500 focus:ring-emerald-500"
                />
                <label htmlFor="is_active" className="text-xs text-slate-300">
                  Facility is currently active and accepting referrals
                </label>
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createSubmitting}
                  className="px-5 py-2 text-xs font-bold bg-emerald-500 hover:bg-emerald-400 text-slate-950 rounded-lg shadow-lg shadow-emerald-500/20 transition disabled:opacity-50"
                >
                  {createSubmitting ? "Registering..." : "Save Facility"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default function FacilitiesPage() {
  return (
    <ProtectedRoute>
      <FacilitiesContent />
    </ProtectedRoute>
  );
}

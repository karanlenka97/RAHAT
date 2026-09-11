/**
 * Dashboard API client library for RAHAT Frontline, Facility, and District Portals.
 */

import { apiClient } from "./api";
import {
  FrontlineDashboardData,
  FacilityDashboardData,
  DistrictDashboardData,
  ReferralFunnelData,
  CareCompletionData,
} from "@/types/dashboard";

export async function getFrontlineDashboard(token: string): Promise<FrontlineDashboardData> {
  return apiClient<FrontlineDashboardData>("/api/v1/dashboard/frontline", {
    method: "GET",
    token,
  });
}

export async function getFacilityDashboard(
  token: string,
  facilityId?: string | null
): Promise<FacilityDashboardData> {
  const query = facilityId ? `?facility_id=${encodeURIComponent(facilityId)}` : "";
  return apiClient<FacilityDashboardData>(`/api/v1/dashboard/facility${query}`, {
    method: "GET",
    token,
  });
}

export async function getDistrictDashboard(
  token: string,
  district?: string | null,
  timeRange: string = "all"
): Promise<DistrictDashboardData> {
  const params = new URLSearchParams();
  if (district) params.append("district", district);
  if (timeRange) params.append("time_range", timeRange);

  const qs = params.toString() ? `?${params.toString()}` : "";
  return apiClient<DistrictDashboardData>(`/api/v1/dashboard/district${qs}`, {
    method: "GET",
    token,
  });
}

export async function getReferralFunnel(
  token: string,
  district?: string | null,
  facilityId?: string | null,
  timeRange: string = "all"
): Promise<ReferralFunnelData> {
  const params = new URLSearchParams();
  if (district) params.append("district", district);
  if (facilityId) params.append("facility_id", facilityId);
  if (timeRange) params.append("time_range", timeRange);

  const qs = params.toString() ? `?${params.toString()}` : "";
  return apiClient<ReferralFunnelData>(`/api/v1/dashboard/referral-funnel${qs}`, {
    method: "GET",
    token,
  });
}

export async function getCareCompletion(
  token: string,
  district?: string | null,
  timeRange: string = "all"
): Promise<CareCompletionData> {
  const params = new URLSearchParams();
  if (district) params.append("district", district);
  if (timeRange) params.append("time_range", timeRange);

  const qs = params.toString() ? `?${params.toString()}` : "";
  return apiClient<CareCompletionData>(`/api/v1/dashboard/care-completion${qs}`, {
    method: "GET",
    token,
  });
}

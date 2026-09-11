/**
 * Facility & Capabilities API Service.
 */

import { apiClient } from "./api";
import {
  Facility,
  FacilityCreateInput,
  FacilityUpdateInput,
  FacilityCapability,
  FacilityCapabilityCreateInput,
  FacilityCapabilityUpdateInput,
  PaginatedFacilities,
  NearbyFacilitiesResponse,
} from "@/types/facility";

export interface FacilityQueryParams {
  page?: number;
  page_size?: number;
  facility_type?: string;
  district?: string;
  is_active?: boolean;
  search?: string;
}

export async function getFacilities(
  params: FacilityQueryParams = {},
  token?: string | null
): Promise<PaginatedFacilities> {
  const query = new URLSearchParams();
  if (params.page) query.set("page", params.page.toString());
  if (params.page_size) query.set("page_size", params.page_size.toString());
  if (params.facility_type) query.set("facility_type", params.facility_type);
  if (params.district) query.set("district", params.district);
  if (params.is_active !== undefined) query.set("is_active", String(params.is_active));
  if (params.search && params.search.trim()) query.set("search", params.search.trim());

  const queryString = query.toString() ? `?${query.toString()}` : "";
  return apiClient<PaginatedFacilities>(`/api/v1/facilities${queryString}`, {
    token,
  });
}

export async function getFacility(
  id: string,
  token?: string | null
): Promise<Facility> {
  return apiClient<Facility>(`/api/v1/facilities/${id}`, {
    token,
  });
}

export async function getNearbyFacilities(
  params: { latitude: number; longitude: number; radius_km?: number },
  token?: string | null
): Promise<NearbyFacilitiesResponse> {
  const query = new URLSearchParams();
  query.set("latitude", params.latitude.toString());
  query.set("longitude", params.longitude.toString());
  if (params.radius_km) query.set("radius_km", params.radius_km.toString());

  return apiClient<NearbyFacilitiesResponse>(`/api/v1/facilities/nearby?${query.toString()}`, {
    token,
  });
}

export async function createFacility(
  data: FacilityCreateInput,
  token?: string | null
): Promise<Facility> {
  return apiClient<Facility>("/api/v1/facilities", {
    method: "POST",
    body: JSON.stringify(data),
    token,
  });
}

export async function updateFacility(
  id: string,
  data: FacilityUpdateInput,
  token?: string | null
): Promise<Facility> {
  return apiClient<Facility>(`/api/v1/facilities/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
    token,
  });
}

export async function getFacilityCapabilities(
  facilityId: string,
  token?: string | null
): Promise<FacilityCapability[]> {
  return apiClient<FacilityCapability[]>(`/api/v1/facilities/${facilityId}/capabilities`, {
    token,
  });
}

export async function createFacilityCapability(
  facilityId: string,
  data: FacilityCapabilityCreateInput,
  token?: string | null
): Promise<FacilityCapability> {
  return apiClient<FacilityCapability>(`/api/v1/facilities/${facilityId}/capabilities`, {
    method: "POST",
    body: JSON.stringify(data),
    token,
  });
}

export async function updateFacilityCapability(
  facilityId: string,
  capabilityId: string,
  data: FacilityCapabilityUpdateInput,
  token?: string | null
): Promise<FacilityCapability> {
  return apiClient<FacilityCapability>(
    `/api/v1/facilities/${facilityId}/capabilities/${capabilityId}`,
    {
      method: "PATCH",
      body: JSON.stringify(data),
      token,
    }
  );
}

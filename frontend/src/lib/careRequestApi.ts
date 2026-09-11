/**
 * Care Request API Service.
 */

import { apiClient } from "./api";
import {
  CareRequest,
  CareRequestCreateInput,
  CareRequestUpdateInput,
  PaginatedCareRequests,
} from "@/types/careRequest";

export interface CareRequestQueryParams {
  page?: number;
  page_size?: number;
  patient_id?: string;
  urgency?: string;
  care_category?: string;
  required_service?: string;
  search?: string;
}

export async function getCareRequests(
  params: CareRequestQueryParams = {},
  token?: string | null
): Promise<PaginatedCareRequests> {
  const query = new URLSearchParams();
  if (params.page) query.set("page", params.page.toString());
  if (params.page_size) query.set("page_size", params.page_size.toString());
  if (params.patient_id) query.set("patient_id", params.patient_id);
  if (params.urgency) query.set("urgency", params.urgency);
  if (params.care_category) query.set("care_category", params.care_category);
  if (params.required_service) query.set("required_service", params.required_service);
  if (params.search && params.search.trim()) query.set("search", params.search.trim());

  const queryString = query.toString() ? `?${query.toString()}` : "";
  return apiClient<PaginatedCareRequests>(`/api/v1/care-requests${queryString}`, {
    token,
  });
}

export async function getCareRequest(
  id: string,
  token?: string | null
): Promise<CareRequest> {
  return apiClient<CareRequest>(`/api/v1/care-requests/${id}`, {
    token,
  });
}

export async function createCareRequest(
  data: CareRequestCreateInput,
  token?: string | null
): Promise<CareRequest> {
  return apiClient<CareRequest>("/api/v1/care-requests", {
    method: "POST",
    body: JSON.stringify(data),
    token,
  });
}

export async function updateCareRequest(
  id: string,
  data: CareRequestUpdateInput,
  token?: string | null
): Promise<CareRequest> {
  return apiClient<CareRequest>(`/api/v1/care-requests/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
    token,
  });
}

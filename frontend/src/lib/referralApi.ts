/**
 * Referral Lifecycle and Tracking API Client.
 */

import { apiClient } from "./api";
import {
  Referral,
  ReferralEvent,
  ReferralListResponse,
  ReferralCreateInput,
  ReferralAcceptInput,
  ReferralRejectInput,
  ReferralNotifyInput,
  ReferralDepartInput,
  ReferralArriveInput,
  ReferralStartServiceInput,
  ReferralCompleteInput,
  ReferralBackReferInput,
  ReferralRerouteInput,
} from "@/types/referral";

export interface ReferralQueryParams {
  page?: number;
  page_size?: number;
  status?: string;
  receiving_facility_id?: string;
  origin_facility_id?: string;
  urgency?: string;
  search?: string;
}

export async function getReferrals(
  params: ReferralQueryParams = {},
  token?: string | null
): Promise<ReferralListResponse> {
  const query = new URLSearchParams();
  if (params.page) query.set("page", params.page.toString());
  if (params.page_size) query.set("page_size", params.page_size.toString());
  if (params.status) query.set("status", params.status);
  if (params.receiving_facility_id) query.set("receiving_facility_id", params.receiving_facility_id);
  if (params.origin_facility_id) query.set("origin_facility_id", params.origin_facility_id);
  if (params.urgency) query.set("urgency", params.urgency);
  if (params.search && params.search.trim()) query.set("search", params.search.trim());

  const queryString = query.toString() ? `?${query.toString()}` : "";
  return apiClient<ReferralListResponse>(`/api/v1/referrals${queryString}`, {
    token,
  });
}

export async function getReferral(
  id: string,
  token?: string | null
): Promise<Referral> {
  return apiClient<Referral>(`/api/v1/referrals/${id}`, {
    token,
  });
}

export async function getReferralEvents(
  id: string,
  token?: string | null
): Promise<ReferralEvent[]> {
  return apiClient<ReferralEvent[]>(`/api/v1/referrals/${id}/events`, {
    token,
  });
}

export async function createReferral(
  data: ReferralCreateInput,
  token?: string | null
): Promise<Referral> {
  return apiClient<Referral>("/api/v1/referrals", {
    method: "POST",
    body: JSON.stringify(data),
    token,
  });
}

export async function acceptReferral(
  id: string,
  data: ReferralAcceptInput = {},
  token?: string | null
): Promise<Referral> {
  return apiClient<Referral>(`/api/v1/referrals/${id}/accept`, {
    method: "POST",
    body: JSON.stringify(data),
    token,
  });
}

export async function rejectReferral(
  id: string,
  data: ReferralRejectInput,
  token?: string | null
): Promise<Referral> {
  return apiClient<Referral>(`/api/v1/referrals/${id}/reject`, {
    method: "POST",
    body: JSON.stringify(data),
    token,
  });
}

export async function notifyPatient(
  id: string,
  data: ReferralNotifyInput = {},
  token?: string | null
): Promise<Referral> {
  return apiClient<Referral>(`/api/v1/referrals/${id}/notify-patient`, {
    method: "POST",
    body: JSON.stringify(data),
    token,
  });
}

export async function departPatient(
  id: string,
  data: ReferralDepartInput = {},
  token?: string | null
): Promise<Referral> {
  return apiClient<Referral>(`/api/v1/referrals/${id}/depart`, {
    method: "POST",
    body: JSON.stringify(data),
    token,
  });
}

export async function arrivePatient(
  id: string,
  data: ReferralArriveInput = {},
  token?: string | null
): Promise<Referral> {
  return apiClient<Referral>(`/api/v1/referrals/${id}/arrive`, {
    method: "POST",
    body: JSON.stringify(data),
    token,
  });
}

export async function startService(
  id: string,
  data: ReferralStartServiceInput = {},
  token?: string | null
): Promise<Referral> {
  return apiClient<Referral>(`/api/v1/referrals/${id}/start-service`, {
    method: "POST",
    body: JSON.stringify(data),
    token,
  });
}

export async function completeService(
  id: string,
  data: ReferralCompleteInput = {},
  token?: string | null
): Promise<Referral> {
  return apiClient<Referral>(`/api/v1/referrals/${id}/complete`, {
    method: "POST",
    body: JSON.stringify(data),
    token,
  });
}

export async function backRefer(
  id: string,
  data: ReferralBackReferInput,
  token?: string | null
): Promise<Referral> {
  return apiClient<Referral>(`/api/v1/referrals/${id}/back-refer`, {
    method: "POST",
    body: JSON.stringify(data),
    token,
  });
}

export async function rerouteReferral(
  id: string,
  data: ReferralRerouteInput,
  token?: string | null
): Promise<Referral> {
  return apiClient<Referral>(`/api/v1/referrals/${id}/reroute`, {
    method: "POST",
    body: JSON.stringify(data),
    token,
  });
}

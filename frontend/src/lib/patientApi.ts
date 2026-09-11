/**
 * Patient Management API Service.
 */

import { apiClient } from "./api";
import {
  Patient,
  PatientCreateInput,
  PatientUpdateInput,
  PaginatedPatients,
  Village,
} from "@/types/patient";

export async function getPatients(
  params: { page?: number; page_size?: number; search?: string } = {},
  token?: string | null
): Promise<PaginatedPatients> {
  const query = new URLSearchParams();
  if (params.page) query.set("page", params.page.toString());
  if (params.page_size) query.set("page_size", params.page_size.toString());
  if (params.search && params.search.trim()) query.set("search", params.search.trim());

  const queryString = query.toString() ? `?${query.toString()}` : "";
  return apiClient<PaginatedPatients>(`/api/v1/patients${queryString}`, {
    token,
  });
}

export async function getPatient(
  id: string,
  token?: string | null
): Promise<Patient> {
  return apiClient<Patient>(`/api/v1/patients/${id}`, {
    token,
  });
}

export async function createPatient(
  data: PatientCreateInput,
  token?: string | null
): Promise<Patient> {
  return apiClient<Patient>("/api/v1/patients", {
    method: "POST",
    body: JSON.stringify(data),
    token,
  });
}

export async function updatePatient(
  id: string,
  data: PatientUpdateInput,
  token?: string | null
): Promise<Patient> {
  return apiClient<Patient>(`/api/v1/patients/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
    token,
  });
}

export async function getVillages(
  token?: string | null
): Promise<Village[]> {
  return apiClient<Village[]>("/api/v1/villages", {
    token,
  });
}

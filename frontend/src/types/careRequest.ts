/**
 * Care Request Management TypeScript definitions.
 */

import { Patient } from "./patient";

export type CareCategory =
  | "GENERAL_MEDICINE"
  | "MATERNAL_HEALTH"
  | "CHILD_HEALTH"
  | "EMERGENCY"
  | "NCD"
  | "MENTAL_HEALTH"
  | "EYE_CARE"
  | "ENT"
  | "DENTAL"
  | "DIAGNOSTIC"
  | "OTHER";

export type UrgencyLevel = "LOW" | "MEDIUM" | "HIGH" | "EMERGENCY";

export type CareRequestStatus = "SUBMITTED" | "TRIAGED" | "REFERRED" | "RESOLVED";

export interface CreatorSummary {
  id: string;
  full_name: string;
  phone?: string | null;
  role?: string | null;
}

export interface PatientCareRequestSummary {
  id: string;
  patient_code: string;
  full_name: string;
  age?: number | null;
  gender: string;
  phone?: string | null;
  village?: {
    id: string;
    name: string;
    district: string;
    state: string;
    pincode?: string | null;
  } | null;
}

export interface CareRequest {
  id: string;
  request_number: string;
  patient_id: string;
  patient?: PatientCareRequestSummary | Patient | null;
  created_by?: string | null;
  creator?: CreatorSummary | null;
  care_category: CareCategory | string;
  required_service: string;
  urgency: UrgencyLevel | string;
  symptoms_summary: string;
  diagnostic_requirements: string[];
  specialist_required: boolean;
  status: CareRequestStatus | string;
  notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface CareRequestCreateInput {
  patient_id: string;
  care_category: CareCategory | string;
  required_service: string;
  urgency: UrgencyLevel | string;
  symptoms_summary: string;
  diagnostic_requirements?: string[];
  specialist_required?: boolean;
  notes?: string | null;
}

export interface CareRequestUpdateInput {
  care_category?: CareCategory | string;
  required_service?: string;
  urgency?: UrgencyLevel | string;
  symptoms_summary?: string;
  diagnostic_requirements?: string[];
  specialist_required?: boolean;
  notes?: string | null;
}

export interface PaginatedCareRequests {
  items: CareRequest[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

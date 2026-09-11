/**
 * Referral Lifecycle and Tracking TypeScript Definitions.
 */

export type ReferralStatus =
  | "CREATED"
  | "PENDING_ACCEPTANCE"
  | "ACCEPTED"
  | "REJECTED"
  | "PATIENT_NOTIFIED"
  | "DEPARTED"
  | "ARRIVED"
  | "IN_SERVICE"
  | "COMPLETED"
  | "BACK_REFERRED"
  | "FOLLOW_UP"
  | "CLOSED"
  | "REROUTED"
  | "CANCELLED";

export type RejectionReason =
  | "SERVICE_UNAVAILABLE"
  | "CAPACITY_UNAVAILABLE"
  | "SPECIALIST_UNAVAILABLE"
  | "FACILITY_CLOSED"
  | "OTHER";

export type ReferralUrgency = "EMERGENCY" | "HIGH" | "MEDIUM" | "LOW";

export interface ReferralEvent {
  id: string;
  referral_id: string;
  event_type: string;
  previous_status?: string | null;
  new_status: string;
  performed_by?: string | null;
  performer_name?: string | null;
  performer_role?: string | null;
  notes?: string | null;
  event_metadata?: Record<string, unknown> | null;
  created_at: string;
}

export interface Referral {
  id: string;
  referral_code: string;
  care_request_id: string;
  care_request_number?: string | null;
  care_category?: string | null;
  required_service?: string | null;

  patient_id: string;
  patient_name?: string | null;
  patient_code?: string | null;
  patient_age?: number | null;
  patient_gender?: string | null;
  patient_phone?: string | null;
  patient_village?: string | null;

  source_facility_id?: string | null;
  source_facility_name?: string | null;
  receiving_facility_id: string;
  receiving_facility_name?: string | null;
  receiving_facility_type?: string | null;

  created_by?: string | null;
  creator_name?: string | null;
  creator_role?: string | null;
  parent_referral_id?: string | null;

  status: ReferralStatus;
  urgency: string;
  referral_reason?: string | null;
  clinical_summary?: string | null;
  required_specialty?: string | null;

  transport_mode?: string | null;
  transport_status?: string | null;
  estimated_transit_minutes?: number | null;
  expected_arrival_time?: string | null;

  rejection_reason?: string | null;
  rejection_notes?: string | null;
  back_referral_notes?: string | null;

  initiated_at: string;
  accepted_at?: string | null;
  notified_at?: string | null;
  departed_at?: string | null;
  arrived_at?: string | null;
  in_service_at?: string | null;
  completed_at?: string | null;
  back_referred_at?: string | null;
  closed_at?: string | null;
  created_at: string;
  updated_at: string;

  events?: ReferralEvent[] | null;
}

export interface ReferralListResponse {
  items: Referral[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ReferralCreateInput {
  care_request_id: string;
  receiving_facility_id: string;
  source_facility_id?: string | null;
  referral_reason?: string | null;
  clinical_summary?: string | null;
  urgency?: string;
  required_specialty?: string | null;
  required_capability?: string | null;
  expected_arrival_time?: string | null;
  transport_mode?: string | null;
}

export interface ReferralAcceptInput {
  notes?: string;
  expected_arrival_time?: string;
}

export interface ReferralRejectInput {
  rejection_reason: string;
  rejection_notes?: string;
}

export interface ReferralNotifyInput {
  notes?: string;
}

export interface ReferralDepartInput {
  transport_mode?: string;
  estimated_transit_minutes?: number;
  notes?: string;
}

export interface ReferralArriveInput {
  notes?: string;
}

export interface ReferralStartServiceInput {
  notes?: string;
}

export interface ReferralCompleteInput {
  clinical_summary?: string;
  notes?: string;
}

export interface ReferralBackReferInput {
  back_referral_notes: string;
  notes?: string;
}

export interface ReferralRerouteInput {
  new_receiving_facility_id: string;
  reason?: string;
  notes?: string;
}

/**
 * Dashboard TypeScript Definitions for RAHAT Frontline, Facility, and District Portals.
 */

export interface FrontlineActionItem {
  id: string;
  item_type: "CARE_REQUEST" | "REFERRAL" | string;
  patient_id: string;
  patient_name: string;
  patient_code: string;
  urgency: "EMERGENCY" | "HIGH" | "MEDIUM" | "LOW" | string;
  status: string;
  action_required: string;
  facility_name?: string | null;
  village_name?: string | null;
  elapsed_hours: number;
  created_at: string;
  updated_at?: string | null;
  deep_link: string;
}

export interface FrontlineRecentActivity {
  id: string;
  item_type: string;
  patient_name: string;
  patient_code: string;
  action_description: string;
  timestamp: string;
  deep_link: string;
}

export interface FrontlineDashboardData {
  role: string;
  user_name: string;
  total_patients: number;
  active_care_requests: number;
  urgent_care_requests: number;
  pending_referrals: number;
  action_required_count: number;
  in_transit_referrals: number;
  completed_referrals: number;
  action_queue: FrontlineActionItem[];
  recent_activity: FrontlineRecentActivity[];
  generated_at: string;
}

export interface FacilityCapabilityMetric {
  capability_id: string;
  service_name: string;
  service_category: string;
  availability_status: "AVAILABLE" | "LIMITED" | "UNAVAILABLE" | string;
  capacity: number;
  current_load: number;
  utilization_percent: number;
  specialist_required: boolean;
  diagnostic_required: boolean;
  operating_hours: string;
}

export interface FacilityReferralQueueItem {
  referral_id: string;
  referral_code: string;
  care_request_id: string;
  patient_id: string;
  patient_name: string;
  patient_code: string;
  origin_facility_name?: string | null;
  priority: string;
  status: string;
  transport_mode?: string | null;
  expected_arrival_time?: string | null;
  initiated_at: string;
  elapsed_hours: number;
  deep_link: string;
}

export interface FacilityStatusBreakdown {
  pending_acceptance: number;
  accepted: number;
  patient_notified: number;
  in_transit: number;
  arrived: number;
  in_service: number;
  completed: number;
  back_referred: number;
  rejected: number;
  rerouted: number;
}

export interface FacilityDashboardData {
  facility_id: string;
  facility_name: string;
  facility_type: string;
  tier_level: number;
  district: string;
  state: string;
  operational_status: string;
  total_beds: number;
  available_beds: number;
  occupied_beds: number;
  bed_utilization_percent: number;
  icu_beds_total: number;
  icu_beds_available: number;
  icu_beds_occupied: number;
  icu_utilization_percent: number;
  oxygen_supported_beds: number;
  available_oxygen_beds: number;
  ventilators_count: number;
  available_ventilators: number;
  active_referrals_count: number;
  status_breakdown: FacilityStatusBreakdown;
  operational_queue: FacilityReferralQueueItem[];
  total_capabilities_count: number;
  available_capabilities_count: number;
  limited_capabilities_count: number;
  unavailable_capabilities_count: number;
  capabilities: FacilityCapabilityMetric[];
  generated_at: string;
}

export interface FacilityPerformanceSummary {
  facility_id: string;
  facility_name: string;
  facility_type: string;
  tier_level: number;
  referrals_received: number;
  referrals_accepted: number;
  referrals_rejected: number;
  referrals_completed: number;
  active_referrals: number;
  acceptance_rate: number;
  avg_completion_hours?: number | null;
  available_services_count: number;
  total_beds: number;
  available_beds: number;
  bed_utilization_percent: number;
}

export interface DistrictDashboardData {
  district_name: string;
  time_range: string;
  total_care_requests: number;
  total_referrals: number;
  accepted_referrals: number;
  rejected_referrals: number;
  completed_referrals: number;
  active_referrals: number;
  urgent_emergency_count: number;
  care_completion_rate: number;
  avg_referral_completion_hours?: number | null;
  care_requests_by_category: Record<string, number>;
  care_requests_by_urgency: Record<string, number>;
  referrals_by_status: Record<string, number>;
  facility_performance: FacilityPerformanceSummary[];
  generated_at: string;
}

export interface FunnelStageItem {
  stage_key: string;
  stage_name: string;
  count: number;
  percentage_of_total: number;
  drop_off_count: number;
  drop_off_rate: number;
}

export interface ReferralFunnelData {
  district?: string | null;
  facility_id?: string | null;
  time_range: string;
  total_initiated: number;
  stages: FunnelStageItem[];
  side_branches: Record<string, number>;
  generated_at: string;
}

export interface CareCompletionByGroup {
  group_name: string;
  total_care_requests: number;
  referred_care_requests: number;
  completed_care_requests: number;
  completion_rate: number;
}

export interface CareCompletionData {
  district?: string | null;
  time_range: string;
  total_care_requests: number;
  referred_care_requests: number;
  completed_care_requests: number;
  overall_completion_rate: number;
  formula_definition: string;
  by_urgency: CareCompletionByGroup[];
  by_category: CareCompletionByGroup[];
  generated_at: string;
}

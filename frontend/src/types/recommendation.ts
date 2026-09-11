/**
 * Smart Facility Recommendation Engine TypeScript Definitions.
 */

export interface FactorScores {
  service_match: number;
  distance: number;
  diagnostic_match: number;
  specialist_match: number;
  availability: number;
  workload: number;
}

export interface FacilityRecommendationItem {
  facility_id: string;
  facility_name: string;
  facility_code?: string | null;
  facility_type: string;
  tier_level: number;
  district: string;
  state: string;
  address?: string | null;
  phone?: string | null;
  distance_km?: number | null;
  overall_score: number;
  factors: FactorScores;
  matched_services: string[];
  availability_status: string;
  specialist_available: boolean;
  diagnostics_available: string[];
  capacity: number;
  current_load: number;
  explanation: string;
}

export interface RecommendationResponse {
  care_request_id: string;
  patient_id: string;
  patient_name: string;
  care_category?: string | null;
  required_service?: string | null;
  urgency: string;
  diagnostic_requirements: string[];
  specialist_required: boolean;
  total_candidates: number;
  recommendations: FacilityRecommendationItem[];
  generated_at: string;
}

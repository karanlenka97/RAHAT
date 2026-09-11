/**
 * AI Referral Assistant TypeScript Definitions.
 */

export interface ReferralAISummaryResponse {
  care_request_id: string;
  concise_summary: string;
  presenting_information: string;
  relevant_history?: string | null;
  requested_service: string;
  diagnostic_requirements: string[];
  specialist_requirement: boolean;
  administrative_notes?: string | null;
  missing_information: string[];
  disclaimer: string;
  is_ai_assisted: boolean;
  model_used?: string | null;
}

export interface AIStructuredExtractionRequest {
  raw_text: string;
  existing_care_category?: string | null;
  existing_urgency?: string | null;
}

export interface AIStructuredExtractionResponse {
  symptoms_summary: string;
  care_category?: string | null;
  required_service?: string | null;
  diagnostic_requirements: string[];
  specialist_required: boolean;
  urgency_as_recorded?: string | null;
  missing_information: string[];
  disclaimer: string;
  is_ai_assisted: boolean;
}

export interface AIRecommendationExplanationRequest {
  care_request_id: string;
  facility_id: string;
  facility_name: string;
  overall_score: number;
  service_score?: number;
  distance_score?: number;
  diagnostic_score?: number;
  specialist_score?: number;
  availability_score?: number;
  workload_score?: number;
  matched_services?: string[];
  distance_km?: number | null;
  available_beds?: number | null;
}

export interface AIRecommendationExplanationResponse {
  facility_id: string;
  facility_name: string;
  explanation_text: string;
  key_factors: string[];
  overall_score: number;
  disclaimer: string;
  is_ai_assisted: boolean;
}

export interface ApplyAISummaryRequest {
  care_request_id: string;
  notes?: string | null;
  symptoms_summary?: string | null;
  confirmed_by_user: boolean;
}

export interface ApplyAISummaryResponse {
  care_request_id: string;
  status: string;
  message: string;
  updated_at: string;
}

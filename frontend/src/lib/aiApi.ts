/**
 * AI Referral Assistant API client functions.
 */
import { apiClient } from "./api";
import {
  ReferralAISummaryResponse,
  AIStructuredExtractionRequest,
  AIStructuredExtractionResponse,
  AIRecommendationExplanationRequest,
  AIRecommendationExplanationResponse,
  ApplyAISummaryRequest,
  ApplyAISummaryResponse,
} from "@/types/ai";

export async function getAIReferralSummary(
  careRequestId: string,
  token: string
): Promise<ReferralAISummaryResponse> {
  return apiClient<ReferralAISummaryResponse>("/api/v1/ai/referral-summary", {
    method: "POST",
    body: JSON.stringify({ care_request_id: careRequestId }),
    token,
  });
}

export async function extractAIStructuredIntake(
  payload: AIStructuredExtractionRequest,
  token: string
): Promise<AIStructuredExtractionResponse> {
  return apiClient<AIStructuredExtractionResponse>("/api/v1/ai/extract-intake", {
    method: "POST",
    body: JSON.stringify(payload),
    token,
  });
}

export async function explainAIRecommendation(
  payload: AIRecommendationExplanationRequest,
  token: string
): Promise<AIRecommendationExplanationResponse> {
  return apiClient<AIRecommendationExplanationResponse>("/api/v1/ai/explain-recommendation", {
    method: "POST",
    body: JSON.stringify(payload),
    token,
  });
}

export async function applyAISummaryToCareRequest(
  payload: ApplyAISummaryRequest,
  token: string
): Promise<ApplyAISummaryResponse> {
  return apiClient<ApplyAISummaryResponse>("/api/v1/ai/apply-summary", {
    method: "POST",
    body: JSON.stringify(payload),
    token,
  });
}

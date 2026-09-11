/**
 * Smart Facility Recommendation API Service.
 */

import { apiClient } from "./api";
import { RecommendationResponse } from "@/types/recommendation";

export async function getRecommendations(
  careRequestId: string,
  limit: number = 5,
  token?: string | null
): Promise<RecommendationResponse> {
  return apiClient<RecommendationResponse>(
    `/api/v1/recommendations/${careRequestId}?limit=${limit}`,
    {
      token,
    }
  );
}

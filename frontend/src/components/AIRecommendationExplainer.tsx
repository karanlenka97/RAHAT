"use client";

import React, { useState } from "react";
import { useOffline } from "@/context/OfflineContext";
import { explainAIRecommendation } from "@/lib/aiApi";
import { FacilityRecommendationItem } from "@/types/recommendation";
import { AIRecommendationExplanationResponse } from "@/types/ai";

interface AIRecommendationExplainerProps {
  careRequestId: string;
  recommendation: FacilityRecommendationItem;
  token: string | null;
}

export function AIRecommendationExplainer({
  careRequestId,
  recommendation,
  token,
}: AIRecommendationExplainerProps) {
  const { isOnline } = useOffline();
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [explanation, setExplanation] = useState<AIRecommendationExplanationResponse | null>(null);

  const handleFetchExplanation = async () => {
    if (isOpen) {
      setIsOpen(false);
      return;
    }
    setIsOpen(true);

    if (explanation) return;
    if (!token || !isOnline) return;

    setIsLoading(true);
    try {
      const availableBeds = Math.max(0, (recommendation.capacity || 0) - (recommendation.current_load || 0));
      const data = await explainAIRecommendation(
        {
          care_request_id: careRequestId,
          facility_id: recommendation.facility_id,
          facility_name: recommendation.facility_name,
          overall_score: recommendation.overall_score,
          service_score: recommendation.factors.service_match,
          distance_score: recommendation.factors.distance,
          diagnostic_score: recommendation.factors.diagnostic_match,
          specialist_score: recommendation.factors.specialist_match,
          availability_score: recommendation.factors.availability,
          workload_score: recommendation.factors.workload,
          matched_services: recommendation.matched_services,
          distance_km: recommendation.distance_km,
          available_beds: availableBeds,
        },
        token
      );
      setExplanation(data);
    } catch {
      // Fallback is handled automatically in the UI rendering
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="mt-2 text-xs">
      <button
        onClick={handleFetchExplanation}
        className="inline-flex items-center gap-1.5 text-xs text-indigo-400 hover:text-indigo-300 font-medium transition cursor-pointer"
      >
        <span>✨</span>
        <span>{isOpen ? "Hide match explanation" : "Why was this facility recommended?"}</span>
      </button>

      {isOpen && (
        <div className="mt-2 p-3.5 rounded-xl bg-slate-950/80 border border-indigo-500/20 text-slate-300 space-y-2.5 animate-fadeIn">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-indigo-400 flex items-center gap-1">
              <span>📊</span> Recommendation Factor Analysis
            </span>
            <span className="text-[10px] px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
              Deterministic Match: {recommendation.overall_score.toFixed(1)}%
            </span>
          </div>

          {isLoading ? (
            <div className="py-3 text-center flex items-center justify-center gap-2 text-slate-400">
              <div className="h-3 w-3 animate-spin rounded-full border-2 border-indigo-400 border-t-transparent" />
              <span>Analyzing scoring factors...</span>
            </div>
          ) : explanation ? (
            <div className="space-y-2">
              <p className="text-xs text-slate-200 leading-relaxed font-sans">{explanation.explanation_text}</p>
              {explanation.key_factors && explanation.key_factors.length > 0 && (
                <ul className="list-disc list-inside space-y-0.5 text-[11px] text-slate-300 pt-1">
                  {explanation.key_factors.map((factor, idx) => (
                    <li key={idx} className="text-slate-300">
                      {factor}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          ) : (
            /* Fallback to deterministic factors */
            <div className="space-y-1 text-xs">
              <p className="text-slate-300">
                Recommended based on deterministic clinical service match ({recommendation.factors.service_match.toFixed(0)}%),
                diagnostic readiness ({recommendation.factors.diagnostic_match.toFixed(0)}%), and transit proximity ({recommendation.distance_km?.toFixed(1) || "?"} km).
              </p>
            </div>
          )}

          <div className="pt-2 border-t border-slate-800 text-[10px] text-slate-500 italic">
            Deterministic match factors remain the authoritative basis for facility ranking.
          </div>
        </div>
      )}
    </div>
  );
}

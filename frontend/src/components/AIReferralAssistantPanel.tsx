"use client";

import React, { useState } from "react";
import { useOffline } from "@/context/OfflineContext";
import { getAIReferralSummary, applyAISummaryToCareRequest } from "@/lib/aiApi";
import { ReferralAISummaryResponse } from "@/types/ai";
import { ApiError } from "@/lib/api";

interface AIReferralAssistantPanelProps {
  careRequestId: string;
  token: string | null;
  existingNotes?: string | null;
  onSummaryApplied?: (newNotes: string) => void;
}

export function AIReferralAssistantPanel({
  careRequestId,
  token,
  existingNotes,
  onSummaryApplied,
}: AIReferralAssistantPanelProps) {
  const { isOnline } = useOffline();

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [summaryData, setSummaryData] = useState<ReferralAISummaryResponse | null>(null);

  // Review & Confirmation Modal
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [isApplying, setIsApplying] = useState(false);
  const [applySuccess, setApplySuccess] = useState<string | null>(null);

  const handleGenerateSummary = async () => {
    if (!token) return;
    if (!isOnline) {
      setError("AI Referral Assistant requires an active internet connection.");
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const data = await getAIReferralSummary(careRequestId, token);
      setSummaryData(data);
    } catch (err: unknown) {
      const msg =
        err instanceof ApiError
          ? err.message
          : err instanceof Error
          ? err.message
          : "AI Assistant is temporarily unavailable. Please proceed manually.";
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  };

  const handleApplySummary = async () => {
    if (!token || !summaryData) return;
    setIsApplying(true);
    setError(null);

    try {
      const combinedNotes = summaryData.administrative_notes
        ? `${summaryData.administrative_notes}\n\n[Summary]: ${summaryData.concise_summary}`
        : summaryData.concise_summary;

      await applyAISummaryToCareRequest(
        {
          care_request_id: careRequestId,
          notes: combinedNotes,
          confirmed_by_user: true,
        },
        token
      );

      setShowConfirmModal(false);
      setApplySuccess("AI summary successfully applied to Care Request administrative notes!");
      if (onSummaryApplied) {
        onSummaryApplied(combinedNotes);
      }
      setTimeout(() => setApplySuccess(null), 6000);
    } catch (err: unknown) {
      const msg =
        err instanceof ApiError
          ? err.message
          : err instanceof Error
          ? err.message
          : "Failed to apply summary to care request.";
      setError(msg);
    } finally {
      setIsApplying(false);
    }
  };

  return (
    <div className="bg-gradient-to-b from-indigo-950/30 to-slate-900/60 border border-indigo-500/20 rounded-2xl p-5 mb-8 shadow-xl relative overflow-hidden">
      {/* Decorative gradient blur */}
      <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-500/5 rounded-full blur-3xl pointer-events-none" />

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
        <div className="flex items-center gap-2.5">
          <div className="h-8 w-8 rounded-lg bg-indigo-500/20 border border-indigo-500/40 flex items-center justify-center text-indigo-400 font-bold text-sm">
            ✨
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-bold text-white tracking-tight">AI Referral Assistant</h3>
              <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                Assistive Only
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Summarizes intake information and drafts administrative referral justifications.
            </p>
          </div>
        </div>

        {isOnline ? (
          <button
            onClick={handleGenerateSummary}
            disabled={isLoading}
            className="inline-flex items-center justify-center gap-2 px-3.5 py-2 rounded-xl bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-500 hover:to-indigo-400 text-white text-xs font-semibold shadow-lg shadow-indigo-950/40 disabled:opacity-50 transition cursor-pointer self-start sm:self-auto"
          >
            {isLoading ? (
              <>
                <div className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white border-t-transparent" />
                <span>Generating Summary...</span>
              </>
            ) : summaryData ? (
              <>
                <span>↺</span>
                <span>Regenerate Summary</span>
              </>
            ) : (
              <>
                <span>✨</span>
                <span>Generate AI Summary</span>
              </>
            )}
          </button>
        ) : (
          <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800/80 border border-slate-700 text-slate-400 text-xs font-mono self-start sm:self-auto">
            <span>⚪</span> AI requires internet connection
          </span>
        )}
      </div>

      {/* Success Notification */}
      {applySuccess && (
        <div className="mb-4 p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs flex items-center gap-2 animate-fadeIn">
          <span>✓</span>
          <span>{applySuccess}</span>
        </div>
      )}

      {/* Error Notification */}
      {error && (
        <div className="mb-4 p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center justify-between animate-fadeIn">
          <div className="flex items-center gap-2">
            <span>!</span>
            <span>{error}</span>
          </div>
          <button onClick={() => setError(null)} className="text-rose-400 hover:underline text-xs">
            Dismiss
          </button>
        </div>
      )}

      {/* Generated Content Body */}
      {summaryData && (
        <div className="space-y-4 animate-fadeIn mt-3 pt-3 border-t border-indigo-500/20">
          {/* Mandatory Safety Notice */}
          <div className="p-2.5 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-300 text-[11px] flex items-center gap-2">
            <span className="text-sm">⚠️</span>
            <span>
              <strong>AI-assisted — requires human review.</strong> Not a clinical diagnosis or treatment recommendation.
            </span>
          </div>

          {/* Concise Clinical Summary Card */}
          <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-3.5">
            <span className="block text-[11px] uppercase tracking-wider font-semibold text-indigo-400 mb-1">
              Concise Clinical Summary
            </span>
            <p className="text-xs text-slate-200 leading-relaxed font-sans">{summaryData.concise_summary}</p>
          </div>

          {/* Presenting Information & Administrative Justification */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div className="bg-slate-950/40 border border-slate-800/80 rounded-xl p-3">
              <span className="block text-[11px] font-semibold text-slate-400 mb-1">
                Presenting Information
              </span>
              <p className="text-xs text-slate-300">{summaryData.presenting_information}</p>
              {summaryData.relevant_history && (
                <p className="text-xs text-slate-400 mt-2 italic">
                  History: {summaryData.relevant_history}
                </p>
              )}
            </div>

            <div className="bg-slate-950/40 border border-slate-800/80 rounded-xl p-3">
              <span className="block text-[11px] font-semibold text-slate-400 mb-1">
                Administrative Referral Notes
              </span>
              <p className="text-xs text-slate-300 font-sans">
                {summaryData.administrative_notes || "Referral evaluation justified based on recorded intake requirements."}
              </p>
            </div>
          </div>

          {/* Missing Information Callout */}
          {summaryData.missing_information && summaryData.missing_information.length > 0 && (
            <div className="bg-amber-500/5 border border-amber-500/20 rounded-xl p-3">
              <span className="text-xs font-semibold text-amber-400 block mb-1.5 flex items-center gap-1.5">
                <span>📋</span> Missing Information Identified for Referral
              </span>
              <ul className="list-disc list-inside space-y-1 text-xs text-slate-300">
                {summaryData.missing_information.map((item, idx) => (
                  <li key={idx} className="text-[11px] text-amber-200/90">
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Action Row */}
          <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
            <span className="text-[11px] font-mono text-slate-500">
              Model: {summaryData.model_used || "RAHAT Assistive AI"}
            </span>

            <div className="flex items-center gap-2">
              <button
                onClick={() => setSummaryData(null)}
                className="px-3 py-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-800 text-slate-400 hover:text-slate-200 text-xs font-medium transition cursor-pointer"
              >
                Dismiss
              </button>
              <button
                onClick={() => setShowConfirmModal(true)}
                className="px-3.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow transition cursor-pointer flex items-center gap-1.5"
              >
                <span>✓</span>
                <span>Use Summary in Notes</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Explicit Human Review & Confirmation Modal */}
      {showConfirmModal && summaryData && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fadeIn">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <span className="text-lg">📋</span>
                <h4 className="text-base font-bold text-white">Review & Confirm AI Summary</h4>
              </div>
              <button
                onClick={() => setShowConfirmModal(false)}
                className="text-slate-400 hover:text-white text-sm cursor-pointer"
              >
                ✕
              </button>
            </div>

            <div className="p-3 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-xs text-indigo-300 space-y-1">
              <p className="font-semibold">Human-in-the-Loop Confirmation Required</p>
              <p className="text-[11px] text-slate-300">
                You are applying an AI-assisted text summary to this Care Request&apos;s administrative notes.
                Clinical urgency, diagnosis, and patient demographics will NOT be modified.
              </p>
            </div>

            <div className="space-y-2">
              <label className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
                Proposed Notes to Save:
              </label>
              <div className="p-3 bg-slate-950 border border-slate-800 rounded-xl text-xs text-slate-200 max-h-40 overflow-y-auto font-sans leading-relaxed">
                {summaryData.administrative_notes || summaryData.concise_summary}
              </div>
            </div>

            {existingNotes && (
              <div className="text-[11px] text-slate-400">
                <strong>Current Notes:</strong> <span className="italic">{existingNotes}</span>
              </div>
            )}

            <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
              <button
                onClick={() => setShowConfirmModal(false)}
                disabled={isApplying}
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition cursor-pointer"
              >
                Cancel
              </button>
              <button
                onClick={handleApplySummary}
                disabled={isApplying}
                className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow transition cursor-pointer flex items-center gap-2"
              >
                {isApplying ? (
                  <>
                    <div className="h-3 w-3 animate-spin rounded-full border-2 border-white border-t-transparent" />
                    <span>Applying...</span>
                  </>
                ) : (
                  <>
                    <span>✓</span>
                    <span>Confirm & Apply to Care Request</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

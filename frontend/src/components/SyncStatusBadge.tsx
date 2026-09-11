"use client";

import React, { useState, useEffect } from "react";
import { useOffline } from "@/context/OfflineContext";
import { offlineDb, SyncQueueItem } from "@/lib/offline/db";

export function SyncStatusBadge() {
  const { isOnline, syncStatus, pendingCount, lastSyncedAt, syncErrors, syncNow } = useOffline();
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [queueItems, setQueueItems] = useState<SyncQueueItem[]>([]);
  const [isSyncing, setIsSyncing] = useState<boolean>(false);

  useEffect(() => {
    if (isModalOpen) {
      offlineDb.syncQueue.toArray().then(setQueueItems);
    }
  }, [isModalOpen, pendingCount, syncStatus]);

  const handleManualSync = async () => {
    setIsSyncing(true);
    await syncNow();
    const updated = await offlineDb.syncQueue.toArray();
    setQueueItems(updated);
    setIsSyncing(false);
  };

  // Badge visual config
  const getBadgeConfig = () => {
    if (syncStatus === "syncing" || isSyncing) {
      return {
        bg: "bg-amber-500/10 border-amber-500/30 text-amber-300",
        dot: "bg-amber-400 animate-spin",
        text: "Syncing...",
      };
    }
    if (!isOnline || syncStatus === "offline") {
      return {
        bg: "bg-slate-800 border-slate-700 text-slate-300",
        dot: "bg-slate-400",
        text: pendingCount > 0 ? `Offline (${pendingCount} pending)` : "Offline",
      };
    }
    if (syncStatus === "error" || syncErrors.length > 0) {
      return {
        bg: "bg-rose-500/10 border-rose-500/30 text-rose-300",
        dot: "bg-rose-400",
        text: "Sync Issue",
      };
    }
    if (pendingCount > 0) {
      return {
        bg: "bg-amber-500/10 border-amber-500/30 text-amber-300",
        dot: "bg-amber-400 animate-pulse",
        text: `${pendingCount} Pending Sync`,
      };
    }
    return {
      bg: "bg-emerald-500/10 border-emerald-500/30 text-emerald-300",
      dot: "bg-emerald-400",
      text: "Synced",
    };
  };

  const badge = getBadgeConfig();

  return (
    <>
      <button
        onClick={() => setIsModalOpen(true)}
        className={`flex items-center gap-2 px-2.5 py-1 rounded-full text-[11px] font-mono font-semibold border transition hover:opacity-80 cursor-pointer ${badge.bg}`}
        title="Click to open RAHAT Offline & Sync Center"
      >
        <span className={`h-2 w-2 rounded-full ${badge.dot}`}></span>
        <span>{badge.text}</span>
      </button>

      {/* Sync Management Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-5 animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <span className="text-xl">🔄</span>
                <h3 className="text-base font-bold text-white">RAHAT Sync & Offline Center</h3>
              </div>
              <button
                onClick={() => setIsModalOpen(false)}
                className="text-slate-400 hover:text-white text-sm px-2 py-1 rounded-lg hover:bg-slate-800 cursor-pointer"
              >
                ✕
              </button>
            </div>

            {/* Status Summary Banner */}
            <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-2">
              <div className="flex justify-between items-center text-xs">
                <span className="text-slate-400">Network Reachability:</span>
                <span className={`font-semibold ${isOnline ? "text-emerald-400" : "text-amber-400"}`}>
                  {isOnline ? "● Connected (API Online)" : "○ Offline (Local Storage Active)"}
                </span>
              </div>
              <div className="flex justify-between items-center text-xs">
                <span className="text-slate-400">Pending Sync Queue:</span>
                <span className="font-mono font-bold text-white">{pendingCount} operation(s)</span>
              </div>
              {lastSyncedAt && (
                <div className="flex justify-between items-center text-xs">
                  <span className="text-slate-400">Last Successful Sync:</span>
                  <span className="font-mono text-slate-300">{lastSyncedAt}</span>
                </div>
              )}
            </div>

            {/* Sync Errors Callout */}
            {syncErrors.length > 0 && (
              <div className="p-3 bg-rose-950/40 border border-rose-500/30 rounded-xl space-y-1">
                <span className="text-xs font-bold text-rose-300 flex items-center gap-1.5">
                  <span>⚠️</span> Synchronization Error:
                </span>
                {syncErrors.map((err, i) => (
                  <p key={i} className="text-[11px] text-rose-300/90 font-mono">
                    {err}
                  </p>
                ))}
              </div>
            )}

            {/* Pending Queue List */}
            <div className="space-y-2">
              <span className="text-xs uppercase tracking-wider text-slate-400 font-bold block">
                Queued Local Mutations ({queueItems.length})
              </span>
              {queueItems.length === 0 ? (
                <div className="text-center py-6 text-slate-500 text-xs bg-slate-950/30 rounded-xl border border-slate-800/50">
                  No pending offline mutations. All data synchronized with server.
                </div>
              ) : (
                <div className="max-h-48 overflow-y-auto space-y-2 pr-1">
                  {queueItems.map((item) => (
                    <div
                      key={item.operation_id}
                      className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 flex items-center justify-between text-xs"
                    >
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-white">{item.entity_type}</span>
                          <span className="px-1.5 py-0.2 rounded text-[10px] bg-slate-800 text-slate-300 font-mono">
                            {item.operation_type}
                          </span>
                        </div>
                        <span className="text-[10px] text-slate-500 font-mono">
                          ID: {item.entity_id.slice(0, 8)}... • Retries: {item.retry_count}
                        </span>
                      </div>
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          item.status === "COMPLETED"
                            ? "bg-emerald-500/20 text-emerald-400"
                            : item.status === "FAILED"
                            ? "bg-rose-500/20 text-rose-400"
                            : "bg-amber-500/20 text-amber-400"
                        }`}
                      >
                        {item.status}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Action Bar */}
            <div className="flex items-center justify-between pt-2 border-t border-slate-800">
              <span className="text-[11px] text-slate-500">Auto-syncs on network recovery</span>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setIsModalOpen(false)}
                  className="px-3.5 py-1.5 text-xs text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition cursor-pointer"
                >
                  Close
                </button>
                <button
                  onClick={handleManualSync}
                  disabled={!isOnline || isSyncing}
                  className="px-4 py-1.5 text-xs font-semibold bg-emerald-500 hover:bg-emerald-400 text-slate-950 rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer flex items-center gap-2"
                >
                  {isSyncing ? (
                    <>
                      <span className="h-3 w-3 border-2 border-slate-950 border-t-transparent rounded-full animate-spin"></span>
                      Syncing...
                    </>
                  ) : (
                    "Sync Now ➔"
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

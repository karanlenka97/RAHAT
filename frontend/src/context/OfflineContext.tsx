"use client";

import React, { createContext, useContext, useState, useEffect, useCallback, useMemo } from "react";
import { useAuth } from "./AuthContext";
import { offlineDb } from "@/lib/offline/db";
import { checkBackendReachability, processSyncQueue, SyncResult } from "@/lib/offline/syncEngine";

export type SyncState = "synced" | "syncing" | "pending" | "error" | "offline";

interface OfflineContextType {
  isOnline: boolean;
  syncStatus: SyncState;
  pendingCount: number;
  lastSyncedAt: string | null;
  syncErrors: string[];
  syncNow: () => Promise<SyncResult | null>;
  refreshPendingCount: () => Promise<number>;
}

const OfflineContext = createContext<OfflineContextType | undefined>(undefined);

export function OfflineProvider({ children }: { children: React.ReactNode }) {
  const { token } = useAuth();

  const [isOnline, setIsOnline] = useState<boolean>(true);
  const [syncStatus, setSyncStatus] = useState<SyncState>("synced");
  const [pendingCount, setPendingCount] = useState<number>(0);
  const [lastSyncedAt, setLastSyncedAt] = useState<string | null>(null);
  const [syncErrors, setSyncErrors] = useState<string[]>([]);

  // Refresh pending count from IndexedDB
  const refreshPendingCount = useCallback(async (): Promise<number> => {
    try {
      const count = await offlineDb.syncQueue.where("status").anyOf(["PENDING", "FAILED"]).count();
      setPendingCount(count);
      return count;
    } catch {
      return 0;
    }
  }, []);

  // Manual or automatic synchronization trigger
  const syncNow = useCallback(async (): Promise<SyncResult | null> => {
    if (!token) return null;

    setSyncStatus("syncing");
    setSyncErrors([]);

    try {
      const result = await processSyncQueue(token);
      await refreshPendingCount();

      if (result.errors.length > 0) {
        setSyncStatus("error");
        setSyncErrors(result.errors);
      } else {
        setSyncStatus("synced");
        setLastSyncedAt(new Date().toLocaleTimeString());
      }
      return result;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Sync failed";
      setSyncStatus("error");
      setSyncErrors([msg]);
      return null;
    }
  }, [token, refreshPendingCount]);

  // Connectivity probe and auto-sync on recovery
  useEffect(() => {
    let isMounted = true;

    async function probe() {
      const reachable = await checkBackendReachability();
      if (!isMounted) return;

      setIsOnline(reachable);
      const pending = await refreshPendingCount();

      if (!reachable) {
        setSyncStatus("offline");
      } else if (pending > 0 && syncStatus !== "syncing") {
        setSyncStatus("pending");
        // Auto-sync when online and pending items exist
        if (token) {
          syncNow();
        }
      } else if (pending === 0 && syncStatus !== "syncing" && syncStatus !== "error") {
        setSyncStatus("synced");
      }
    }

    probe();
    const interval = setInterval(probe, 20000); // Probe every 20 seconds

    const handleOnline = () => probe();
    const handleOffline = () => {
      setIsOnline(false);
      setSyncStatus("offline");
    };

    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);

    return () => {
      isMounted = false;
      clearInterval(interval);
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
    };
  }, [token, syncStatus, syncNow, refreshPendingCount]);

  const value = useMemo(
    () => ({
      isOnline,
      syncStatus,
      pendingCount,
      lastSyncedAt,
      syncErrors,
      syncNow,
      refreshPendingCount,
    }),
    [isOnline, syncStatus, pendingCount, lastSyncedAt, syncErrors, syncNow, refreshPendingCount]
  );

  return <OfflineContext.Provider value={value}>{children}</OfflineContext.Provider>;
}

export function useOffline(): OfflineContextType {
  const context = useContext(OfflineContext);
  if (!context) {
    throw new Error("useOffline must be used within an OfflineProvider");
  }
  return context;
}

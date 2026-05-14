import { create } from "zustand";
import { persist } from "zustand/middleware";
import { useEffect, useState } from "react";
import type { User, ContractListItem } from "@/types";

interface AuthState {
  token: string | null;
  user: User | null;
  setAuth: (token: string, user: User) => void;
  clearAuth: () => void;
  // Contract cache (in-memory, not persisted)
  contracts: ContractListItem[];
  contractsFetchedAt: number;
  setContracts: (contracts: ContractListItem[]) => void;
  isContractsStale: () => boolean;
}

const STALE_MS = 30_000; // 30 seconds

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      token: null,
      user: null,
      contracts: [],
      contractsFetchedAt: 0,
      setAuth: (token, user) => set({ token, user }),
      clearAuth: () => {
        set({ token: null, user: null, contracts: [], contractsFetchedAt: 0 });
        // Nuke all stored data
        try {
          localStorage.clear();
          sessionStorage.clear();
          // Clear any service worker caches
          if ('caches' in window) {
            caches.keys().then((names) => names.forEach((n) => caches.delete(n)));
          }
        } catch {
          // Ignore storage access errors
        }
      },
      setContracts: (contracts) => set({ contracts, contractsFetchedAt: Date.now() }),
      isContractsStale: () => Date.now() - get().contractsFetchedAt > STALE_MS,
    }),
    {
      name: "legalai-auth",
      partialize: (state) => ({
        token: state.token,
        user: state.user,
        // Don't persist contracts — they're fetched fresh each session
      }),
    }
  )
);

// Waits for Zustand to rehydrate from localStorage before returning true.
// Use this in every protected page before checking token.
export function useHasHydrated() {
  const [hydrated, setHydrated] = useState(false);
  useEffect(() => {
    const unsub = useAuthStore.persist.onFinishHydration(() => setHydrated(true));
    setHydrated(useAuthStore.persist.hasHydrated());
    return unsub;
  }, []);
  return hydrated;
}

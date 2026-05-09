import toast from "react-hot-toast";
import { create } from "zustand";
import { immer } from "zustand/middleware/immer";
import * as api from "@/lib/api";

interface AlertStore {
  email: string | null;
  watches: api.WatchEntry[];
  alerts: api.CaseAlert[];
  loading: boolean;
  lastChecked: Date | null;

  setEmail: (email: string) => void;
  addWatch: (type: api.WatchType, value: string, county: api.County, email: string) => Promise<void>;
  removeWatch: (watchId: string) => Promise<void>;
  fetchAlerts: () => Promise<void>;
  checkNow: (watchId: string) => Promise<void>;
}

let pollTimer: number | null = null;

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer);
    pollTimer = null;
  }
}

export const useAlertStore = create<AlertStore>()(
  immer((set, get) => ({
    email: null,
    watches: [],
    alerts: [],
    loading: false,
    lastChecked: null,

    setEmail: (email) => {
      const normalizedEmail = email.trim();
      set((state) => {
        state.email = normalizedEmail || null;
      });

      stopPolling();

      if (normalizedEmail && typeof window !== "undefined") {
        void get().fetchAlerts();
        pollTimer = window.setInterval(() => {
          void get().fetchAlerts();
        }, 60000);
      }
    },

    addWatch: async (type, value, county, email) => {
      set((state) => {
        state.loading = true;
      });

      try {
        const watch = await api.createWatch(type, value, county, email);
        set((state) => {
          state.email = email;
          const exists = state.watches.some((existingWatch) => existingWatch.id === watch.id);
          if (!exists) {
            state.watches.push(watch);
          }
          state.loading = false;
        });
        toast.success("Watch saved. TxAlert is monitoring public court records.");
        get().setEmail(email);
      } catch (error) {
        set((state) => {
          state.loading = false;
        });
        toast.error("Could not save this watch. Please try again.");
        console.error(error);
        throw error;
      }
    },
    
    removeWatch: async (watchId) => {
      const previousWatches = get().watches;
      const previousAlerts = get().alerts;

      set((state) => {
        state.watches = state.watches.filter((watch) => watch.id !== watchId);
        state.alerts = state.alerts.filter((alert) => alert.watchId !== watchId);
      });

      try {
        await api.deleteWatch(watchId);
        toast.success("Watch removed.");
      } catch (error) {
        set((state) => {
          state.watches = previousWatches;
          state.alerts = previousAlerts;
        });
        toast.error("Could not remove this watch.");
        console.error(error);
      }
    },
    
    fetchAlerts: async () => {
      const email = get().email;
      if (!email) return;

      set((state) => {
        state.loading = true;
      });

      try {
        const alerts = await api.getAlerts(email);
        set((state) => {
          state.alerts = alerts;
          state.lastChecked = new Date();
          state.loading = false;
        });
      } catch (error) {
        set((state) => {
          state.lastChecked = new Date();
          state.loading = false;
        });
        toast.error("Could not refresh alerts.");
        console.error(error);
      }
    },
    
    checkNow: async (watchId) => {
      set((state) => {
        state.loading = true;
      });

      try {
        const alerts = await api.checkNow(watchId);
        set((state) => {
          const otherAlerts = state.alerts.filter((alert) => alert.watchId !== watchId);
          state.alerts = [...otherAlerts, ...alerts];
          state.lastChecked = new Date();
          state.loading = false;
        });
        toast.success("Public records check complete.");
      } catch (error) {
        set((state) => {
          state.lastChecked = new Date();
          state.loading = false;
        });
        toast.error("Check failed. TxAlert will retry on the next cycle.");
        console.error(error);
      }
    },
  }))
);

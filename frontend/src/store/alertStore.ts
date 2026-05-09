import toast from "react-hot-toast";
import { create } from 'zustand';
import { immer } from 'zustand/middleware/immer';
import * as api from "@/lib/api";

interface AlertStore {
  email: string | null;
  watches: api.WatchEntry[];
  alerts: api.CaseAlert[];
  loading: boolean;
  lastChecked: Date | null;
  
  setEmail: (email: string) => void;
  addWatch: (watch: api.WatchEntry) => void;
  createWatch: (type: api.WatchType, value: string, county: api.County, email: string) => Promise<void>;
  removeWatch: (watchId: string) => void;
  fetchAlerts: () => Promise<void>;
  checkNow: (watchId: string) => Promise<void>;
}

export const demoAlerts: api.CaseAlert[] = [
  {
    id: "demo-alert-1",
    watchId: "demo-watch-1",
    caseNumber: "JP-24-CV-18492",
    filingDate: "2026-05-04",
    plaintiff: "Lone Star Recovery LLC",
    defendant: "Demo Resident",
    county: "Harris",
    amount: 1840,
    deadlineDate: "2026-05-18",
    daysRemaining: 9,
    urgency: "WARNING",
    limitationsStatus: "Possible old-debt defense. Last payment date needs review.",
    collectorWinRate: 0.71,
    defaultRiskScore: 82,
    riskConfidence: 0.76,
    pattern: {
      severity: "high",
      description: "Bulk filing pattern detected against similar defendants this week.",
      anomalyScore: 0.84,
    },
    miroBoardUrl: "https://miro.com/app/board/demo",
    answerText:
      "Defendant generally denies each claim and asks the court to require the plaintiff to prove its case. Defendant reserves all defenses, including limitations, improper service, mistaken identity, and lack of standing.",
    legalAid: [
      { name: "Lone Star Legal Aid", phone: "1-800-733-8394", url: "https://www.lonestarlegal.org" },
      { name: "TexasLawHelp", url: "https://texaslawhelp.org" },
    ],
  },
  {
    id: "demo-alert-2",
    watchId: "demo-watch-2",
    caseNumber: "DC-26-05519",
    filingDate: "2026-05-01",
    plaintiff: "Gulf Coast Credit Fund",
    defendant: "Demo Resident",
    county: "Dallas",
    amount: 6200,
    deadlineDate: "2026-05-25",
    daysRemaining: 16,
    urgency: "MONITOR",
    limitationsStatus: "No limitations flag from available dates.",
    collectorWinRate: 0.48,
    defaultRiskScore: 54,
    riskConfidence: 0.62,
    pattern: null,
  },
];

const demoWatches: api.WatchEntry[] = [
  {
    id: "demo-watch-1",
    type: "name",
    value: "Demo Resident",
    county: "Harris",
    email: "demo@txalert.org",
    createdAt: "2026-05-09T18:00:00.000Z",
  },
  {
    id: "demo-watch-2",
    type: "address",
    value: "1200 Main St",
    county: "Dallas",
    email: "demo@txalert.org",
    createdAt: "2026-05-09T18:00:00.000Z",
  },
];

export const useAlertStore = create<AlertStore>()(
  immer((set, get) => ({
    email: null,
    watches: demoWatches,
    alerts: demoAlerts,
    loading: false,
    lastChecked: null,
    
    setEmail: (email) => set({ email }),
    
    addWatch: (watch) => set((state) => {
      state.watches.push(watch);
    }),

    createWatch: async (type, value, county, email) => {
      set((state) => {
        state.loading = true;
      });

      try {
        const watch = await api.createWatch(type, value, county, email);
        set((state) => {
          state.email = email;
          state.watches.push(watch);
          state.loading = false;
        });
        toast.success("Watch saved. TxAlert is monitoring public court records.");
        await get().fetchAlerts();
      } catch (error) {
        const fallbackWatch: api.WatchEntry = {
          id: `local-${Date.now()}`,
          type,
          value,
          county,
          email,
          createdAt: new Date().toISOString(),
        };
        set((state) => {
          state.email = email;
          state.watches.push(fallbackWatch);
          state.loading = false;
        });
        toast.error("Backend is not reachable yet. Saved locally for the demo.");
        console.error(error);
      }
    },
    
    removeWatch: (watchId) => set((state) => {
      state.watches = state.watches.filter(w => w.id !== watchId);
    }),
    
    fetchAlerts: async () => {
      const email = get().email;
      if (!email) return;

      set((state) => {
        state.loading = true;
      });

      try {
        const alerts = await api.getAlerts(email);
        set((state) => {
          state.alerts = alerts.length ? alerts : state.alerts;
          state.lastChecked = new Date();
          state.loading = false;
        });
      } catch (error) {
        set((state) => {
          state.lastChecked = new Date();
          state.loading = false;
        });
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
          state.alerts = alerts.length ? alerts : state.alerts;
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

'use client';

import { useEffect, useMemo, useState } from "react";
import { Activity, RefreshCw, ShieldCheck } from "lucide-react";
import type { CaseAlert } from "@/lib/api";
import AnswerModal from "@/components/AnswerModal";
import CaseCard from "@/components/CaseCard";
import { useAlertStore } from "@/store/alertStore";

export default function AlertDashboard() {
  const { alerts, watches, lastChecked, loading, email, fetchAlerts, checkNow } = useAlertStore();
  const [selectedAlert, setSelectedAlert] = useState<CaseAlert | null>(null);

  useEffect(() => {
    if (!email) return;
    void fetchAlerts();
    const timer = window.setInterval(() => {
      void fetchAlerts();
    }, 60000);

    return () => window.clearInterval(timer);
  }, [email, fetchAlerts]);

  const sortedAlerts = useMemo(
    () =>
      [...alerts].sort((first, second) => {
        const a = first.daysRemaining ?? Number.MAX_SAFE_INTEGER;
        const b = second.daysRemaining ?? Number.MAX_SAFE_INTEGER;
        return a - b;
      }),
    [alerts],
  );

  async function checkAll() {
    if (!watches.length) {
      await fetchAlerts();
      return;
    }

    await Promise.all(watches.map((watch) => checkNow(watch.id)));
  }

  return (
    <section className="space-y-4">
      <div className="flex flex-col gap-3 rounded-lg border border-white/10 bg-zinc-950/70 p-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-zinc-500">Monitoring cycle</p>
          <h2 className="mt-1 text-xl font-semibold text-white">Court record alerts</h2>
        </div>
        <button
          type="button"
          onClick={() => void checkAll()}
          disabled={loading}
          className="flex h-10 items-center justify-center gap-2 rounded-md border border-white/10 px-4 text-sm font-semibold text-zinc-100 hover:bg-white/10 disabled:cursor-not-allowed disabled:text-zinc-500"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} aria-hidden="true" />
          Check Now
        </button>
      </div>

      <div className="grid gap-3 sm:grid-cols-3">
        <Metric label="Watching" value={String(watches.length)} />
        <Metric label="Active cases" value={String(sortedAlerts.length)} />
        <Metric label="Last checked" value={lastChecked ? lastChecked.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" }) : "Demo data"} />
      </div>

      {sortedAlerts.length === 0 ? (
        <div className="flex min-h-64 items-center justify-center rounded-lg border border-white/10 bg-zinc-950/70 p-8 text-center">
          <div>
            <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-emerald-500/10 text-emerald-300">
              <span className="h-3 w-3 animate-pulse rounded-full bg-emerald-400" />
            </div>
            <ShieldCheck className="mx-auto mb-3 h-7 w-7 text-emerald-300" aria-hidden="true" />
            <p className="text-lg font-semibold text-white">No active lawsuits found. We&apos;re watching.</p>
            <p className="mt-2 text-sm text-zinc-400">TxAlert will keep checking bounded public court data.</p>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          {sortedAlerts.map((alert) => (
            <CaseCard key={alert.id} alert={alert} onAnswer={setSelectedAlert} />
          ))}
        </div>
      )}

      <AnswerModal alert={selectedAlert} onClose={() => setSelectedAlert(null)} />
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-white/10 bg-zinc-950/70 p-4">
      <div className="flex items-center gap-2 text-zinc-500">
        <Activity className="h-4 w-4" aria-hidden="true" />
        <p className="text-xs font-semibold uppercase tracking-[0.14em]">{label}</p>
      </div>
      <p className="mt-2 text-2xl font-semibold text-white">{value}</p>
    </div>
  );
}

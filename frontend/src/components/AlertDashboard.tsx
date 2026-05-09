'use client';

import { useMemo, useState } from "react";
import { Activity, AlertCircle, BellRing, Clock3, RefreshCw, ShieldCheck, type LucideIcon } from "lucide-react";
import type { CaseAlert } from "@/lib/api";
import AnswerModal from "@/components/AnswerModal";
import CaseCard from "@/components/CaseCard";
import { useAlertStore } from "@/store/alertStore";

type DashboardUrgency = "CRITICAL" | "URGENT" | "WARNING" | "MONITOR";

const urgencyRank: Record<DashboardUrgency, number> = {
  CRITICAL: 0,
  URGENT: 1,
  WARNING: 2,
  MONITOR: 3,
};

const urgencyStyles: Record<DashboardUrgency, string> = {
  CRITICAL: "border-red-400/40 bg-red-500/15 text-red-100",
  URGENT: "border-orange-300/40 bg-orange-500/15 text-orange-100",
  WARNING: "border-yellow-300/40 bg-yellow-500/15 text-yellow-100",
  MONITOR: "border-sky-300/40 bg-sky-500/15 text-sky-100",
};

export default function AlertDashboard() {
  const { alerts, watches, lastChecked, loading, fetchAlerts, checkNow } = useAlertStore();
  const [selectedAlert, setSelectedAlert] = useState<CaseAlert | null>(null);

  const sortedAlerts = useMemo(
    () =>
      [...alerts].sort((first, second) => {
        const a = first.daysRemaining ?? Number.MAX_SAFE_INTEGER;
        const b = second.daysRemaining ?? Number.MAX_SAFE_INTEGER;
        if (a !== b) return a - b;
        return urgencyRank[getUrgency(first.daysRemaining)] - urgencyRank[getUrgency(second.daysRemaining)];
      }),
    [alerts],
  );

  const highestUrgency = sortedAlerts[0] ? getUrgency(sortedAlerts[0].daysRemaining) : "MONITOR";
  const criticalCount = sortedAlerts.filter((alert) => getUrgency(alert.daysRemaining) === "CRITICAL").length;
  const nextDeadline = sortedAlerts.find((alert) => alert.deadlineDate)?.deadlineDate;

  async function checkAll() {
    if (!watches.length) {
      await fetchAlerts();
      return;
    }

    await Promise.all(watches.map((watch) => checkNow(watch.id)));
  }

  return (
    <section className="space-y-4">
      <div className="flex flex-col gap-3 rounded-lg border border-white/10 bg-[#0F0F0F] p-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-zinc-500">Alert dashboard</p>
          <h2 className="mt-1 text-xl font-semibold text-white">Court record matches</h2>
          <p className="mt-1 text-sm text-zinc-400">Sorted by days remaining.</p>
        </div>
        <button
          type="button"
          onClick={() => void checkAll()}
          disabled={loading}
          className="flex h-10 items-center justify-center gap-2 rounded-md bg-[#FF4444] px-4 text-sm font-semibold text-white hover:bg-red-500 disabled:cursor-not-allowed disabled:bg-zinc-700 disabled:text-zinc-400"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} aria-hidden="true" />
          {loading ? "Checking" : "Check Now"}
        </button>
      </div>

      <div className="grid gap-3 rounded-lg border border-white/10 bg-zinc-950/70 p-3 sm:grid-cols-2 xl:grid-cols-4">
        <Metric icon={BellRing} label="Watching" value={String(watches.length)} />
        <Metric icon={AlertCircle} label="Active cases" value={String(sortedAlerts.length)} detail={criticalCount ? `${criticalCount} critical` : undefined} />
        <Metric icon={Clock3} label="Next deadline" value={nextDeadline ?? "None"} />
        <Metric
          icon={Activity}
          label="Last checked"
          value={lastChecked ? lastChecked.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" }) : "Not checked"}
        />
      </div>

      {sortedAlerts.length === 0 ? (
        <div className="flex min-h-64 items-center justify-center rounded-lg border border-white/10 bg-[#0F0F0F] p-8 text-center">
          <div>
            <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full border border-emerald-300/20 bg-emerald-500/10 text-emerald-300">
              <span className="h-3 w-3 animate-pulse rounded-full bg-emerald-400 shadow-[0_0_18px_rgba(52,211,153,0.7)]" />
            </div>
            <ShieldCheck className="mx-auto mb-3 h-7 w-7 text-emerald-300" aria-hidden="true" />
            <p className="text-lg font-semibold text-white">No active lawsuits found. We&apos;re watching.</p>
            <p className="mt-2 text-sm text-zinc-400">Add a watch or run a check when you need a fresh public-record review.</p>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          <div className={`flex flex-col gap-2 rounded-lg border p-3 text-sm sm:flex-row sm:items-center sm:justify-between ${urgencyStyles[highestUrgency]}`}>
            <span className="font-semibold">{highestUrgency}</span>
            <span className="opacity-90">
              {highestUrgencyMessage(highestUrgency)}
            </span>
          </div>
          {sortedAlerts.map((alert) => (
            <CaseCard key={alert.id} alert={alert} onAnswer={setSelectedAlert} />
          ))}
        </div>
      )}

      <AnswerModal alert={selectedAlert} onClose={() => setSelectedAlert(null)} />
    </section>
  );
}

function getUrgency(daysRemaining: number | null): DashboardUrgency {
  if (daysRemaining == null) return "MONITOR";
  if (daysRemaining <= 3) return "CRITICAL";
  if (daysRemaining <= 7) return "URGENT";
  if (daysRemaining <= 14) return "WARNING";
  return "MONITOR";
}

function highestUrgencyMessage(urgency: DashboardUrgency) {
  if (urgency === "CRITICAL") return "A response deadline may be within 3 days.";
  if (urgency === "URGENT") return "A response deadline may be within 7 days.";
  if (urgency === "WARNING") return "A response deadline may be within 14 days.";
  return "No immediate response deadline is flagged.";
}

function Metric({
  detail,
  icon: Icon,
  label,
  value,
}: {
  detail?: string;
  icon: LucideIcon;
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-md border border-white/10 bg-white/[0.04] p-4">
      <div className="flex items-center gap-2 text-zinc-500">
        <Icon className="h-4 w-4" aria-hidden="true" />
        <p className="text-xs font-semibold uppercase tracking-[0.14em]">{label}</p>
      </div>
      <div className="mt-2 flex items-end justify-between gap-2">
        <p className="text-2xl font-semibold text-white">{value}</p>
        {detail ? <p className="pb-1 text-xs font-medium text-red-200">{detail}</p> : null}
      </div>
    </div>
  );
}

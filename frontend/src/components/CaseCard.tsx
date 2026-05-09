'use client';

import { ExternalLink, FileText, Scale } from "lucide-react";
import type { CaseAlert } from "@/lib/api";
import PatternAlert from "@/components/PatternAlert";
import RiskScoreCard from "@/components/RiskScoreCard";

interface CaseCardProps {
  alert: CaseAlert;
  onAnswer: (alert: CaseAlert) => void;
}

const urgencyStyles: Record<CaseAlert["urgency"], string> = {
  CRITICAL: "border-red-400/50 bg-red-500/15 text-red-100",
  URGENT: "border-orange-300/50 bg-orange-500/15 text-orange-100",
  WARNING: "border-yellow-300/50 bg-yellow-500/15 text-yellow-100",
  MONITOR: "border-sky-300/40 bg-sky-500/15 text-sky-100",
};

function money(amount: number | null) {
  if (amount == null) return "Amount not listed";
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(amount);
}

export default function CaseCard({ alert, onAnswer }: CaseCardProps) {
  return (
    <div className="rounded-lg border border-white/10 bg-zinc-950/80 p-4 shadow-lg">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="font-mono text-lg font-semibold text-white">{alert.caseNumber}</h3>
            {alert.pattern ? (
              <span className="rounded bg-alert/20 px-2 py-1 text-xs font-semibold text-red-100">Pattern</span>
            ) : null}
          </div>
          <p className="mt-1 text-sm text-zinc-400">
            Filed {alert.filingDate} in {alert.county} County
          </p>
        </div>
        <div className={`rounded-md border px-3 py-2 text-right ${urgencyStyles[alert.urgency]}`}>
          <p className="text-xs font-semibold uppercase">{alert.urgency}</p>
          <p className="text-2xl font-semibold">
            {alert.daysRemaining == null ? "--" : alert.daysRemaining}
            <span className="ml-1 text-xs font-medium">days</span>
          </p>
        </div>
      </div>

      <div className="mt-4 grid gap-3 md:grid-cols-[1.2fr_0.8fr]">
        <div className="space-y-3">
          <div className="grid gap-3 sm:grid-cols-2">
            <Info label="Plaintiff" value={alert.plaintiff} />
            <Info label="Claim" value={money(alert.amount)} />
            <Info label="Deadline" value={alert.deadlineDate ?? "Not calculated yet"} />
            <Info
              label="Collector win rate"
              value={alert.collectorWinRate == null ? "Unknown" : `${Math.round(alert.collectorWinRate * 100)}%`}
            />
          </div>
          {alert.limitationsStatus ? (
            <div className="rounded-md border border-white/10 bg-white/5 p-3 text-sm text-zinc-300">
              <span className="font-semibold text-zinc-100">Limitations: </span>
              {alert.limitationsStatus}
            </div>
          ) : null}
          <PatternAlert
            description={alert.pattern?.description}
            severity={alert.pattern?.severity}
            anomalyScore={alert.pattern?.anomalyScore}
          />
        </div>

        <div className="space-y-3">
          <RiskScoreCard score={alert.defaultRiskScore} confidence={alert.riskConfidence} />
          <button
            type="button"
            onClick={() => onAnswer(alert)}
            className="flex h-11 w-full items-center justify-center gap-2 rounded-md bg-alert px-4 text-sm font-semibold text-white hover:bg-red-500"
          >
            <FileText className="h-4 w-4" aria-hidden="true" />
            Get Answer Form
          </button>
          <a
            href="https://texaslawhelp.org"
            target="_blank"
            rel="noreferrer"
            className="flex h-11 w-full items-center justify-center gap-2 rounded-md border border-white/10 px-4 text-sm font-semibold text-zinc-100 hover:bg-white/10"
          >
            <Scale className="h-4 w-4" aria-hidden="true" />
            Find Legal Aid
          </a>
          {alert.miroBoardUrl ? (
            <a
              href={alert.miroBoardUrl}
              target="_blank"
              rel="noreferrer"
              className="flex h-10 w-full items-center justify-center gap-2 rounded-md text-sm font-medium text-zinc-300 hover:bg-white/10 hover:text-white"
            >
              <ExternalLink className="h-4 w-4" aria-hidden="true" />
              Miro board
            </a>
          ) : null}
        </div>
      </div>
    </div>
  );
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-white/10 bg-white/5 p-3">
      <p className="text-xs font-semibold uppercase tracking-[0.12em] text-zinc-500">{label}</p>
      <p className="mt-1 text-sm font-medium text-zinc-100">{value}</p>
    </div>
  );
}

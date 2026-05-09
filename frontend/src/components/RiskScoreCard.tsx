'use client';

import { Gauge } from "lucide-react";

interface RiskScoreCardProps {
  score?: number | null;
  confidence?: number | null;
}

function percentValue(value: number) {
  const normalized = value <= 1 ? value * 100 : value;
  return Math.max(0, Math.min(100, Math.round(normalized)));
}

function tone(score: number) {
  if (score >= 75) {
    return {
      label: "High",
      shell: "border-red-400/30 bg-red-500/10 text-red-100",
      fill: "bg-red-400",
    };
  }
  if (score >= 50) {
    return {
      label: "Elevated",
      shell: "border-amber-300/30 bg-amber-500/10 text-amber-100",
      fill: "bg-amber-300",
    };
  }
  return {
    label: "Lower",
    shell: "border-emerald-300/30 bg-emerald-500/10 text-emerald-100",
    fill: "bg-emerald-300",
  };
}

export default function RiskScoreCard({ score, confidence }: RiskScoreCardProps) {
  if (score == null) {
    return (
      <div className="rounded-md border border-white/10 bg-white/[0.04] p-3">
        <div className="flex items-center gap-2 text-zinc-500">
          <Gauge className="h-4 w-4" aria-hidden="true" />
          <p className="text-xs font-semibold uppercase tracking-[0.14em]">Default risk</p>
        </div>
        <p className="mt-2 text-sm text-zinc-300">Risk assessment unavailable</p>
      </div>
    );
  }

  const clampedScore = percentValue(score);
  const confidencePercent = confidence == null ? null : percentValue(confidence);
  const style = tone(clampedScore);

  return (
    <div className={`rounded-md border p-3 ${style.shell}`}>
      <div className="flex items-center gap-2 opacity-90">
        <Gauge className="h-4 w-4" aria-hidden="true" />
        <p className="text-xs font-semibold uppercase tracking-[0.14em]">Default risk</p>
        <span className="ml-auto rounded bg-black/20 px-2 py-1 text-[11px] font-semibold uppercase">
          {style.label}
        </span>
      </div>
      <div className="mt-3 flex items-end justify-between gap-3">
        <p className="text-3xl font-semibold">{clampedScore}%</p>
        {confidencePercent != null ? (
          <p className="pb-1 text-xs opacity-80">{confidencePercent}% confidence</p>
        ) : null}
      </div>
      <div className="mt-3 h-2 overflow-hidden rounded-full bg-black/30">
        <div className={`h-full rounded-full ${style.fill}`} style={{ width: `${clampedScore}%` }} />
      </div>
    </div>
  );
}

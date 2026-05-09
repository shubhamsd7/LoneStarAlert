'use client';

import { AlertTriangle } from "lucide-react";

interface PatternAlertProps {
  description?: string;
  severity?: 'low' | 'medium' | 'high';
  anomalyScore?: number;
}

function percentValue(value: number) {
  const normalized = value <= 1 ? value * 100 : value;
  return Math.max(0, Math.min(100, Math.round(normalized)));
}

export default function PatternAlert({ anomalyScore, description, severity }: PatternAlertProps) {
  if (!description || !severity) return null;

  const color =
    severity === "high"
      ? "border-red-400/30 bg-red-500/10 text-red-100"
      : severity === "medium"
        ? "border-amber-300/30 bg-amber-500/10 text-amber-100"
        : "border-sky-300/30 bg-sky-500/10 text-sky-100";

  return (
    <div className={`rounded-md border p-3 ${color}`}>
      <div className="flex items-center gap-2">
        <AlertTriangle className="h-4 w-4" aria-hidden="true" />
        <h3 className="text-sm font-semibold">Pattern detected</h3>
        <span className="ml-auto rounded bg-black/20 px-2 py-1 text-[11px] font-semibold uppercase">
          {severity}
        </span>
      </div>
      <p className="mt-2 text-sm leading-5 opacity-90">{description}</p>
      {anomalyScore != null ? (
        <p className="mt-2 text-xs font-medium opacity-75">
          Pattern score {percentValue(anomalyScore)}%
        </p>
      ) : null}
    </div>
  );
}

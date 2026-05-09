'use client';

interface RiskScoreCardProps {
  score?: number | null;
  confidence?: number | null;
}

function tone(score: number) {
  if (score >= 75) return "text-red-300 bg-red-500/10 border-red-400/30";
  if (score >= 50) return "text-amber-200 bg-amber-500/10 border-amber-300/30";
  return "text-sky-200 bg-sky-500/10 border-sky-300/30";
}

export default function RiskScoreCard({ score, confidence }: RiskScoreCardProps) {
  if (score == null) {
    return (
      <div className="rounded-md border border-white/10 bg-white/5 p-3">
        <p className="text-xs font-semibold uppercase tracking-[0.14em] text-zinc-500">Default risk</p>
        <p className="mt-2 text-sm text-zinc-300">Risk assessment unavailable</p>
      </div>
    );
  }

  return (
    <div className={`rounded-md border p-3 ${tone(score)}`}>
      <p className="text-xs font-semibold uppercase tracking-[0.14em] opacity-80">Default risk</p>
      <div className="mt-2 flex items-end justify-between gap-3">
        <p className="text-3xl font-semibold">{Math.round(score)}%</p>
        {confidence != null ? (
          <p className="pb-1 text-xs opacity-80">{Math.round(confidence * 100)}% confidence</p>
        ) : null}
      </div>
    </div>
  );
}

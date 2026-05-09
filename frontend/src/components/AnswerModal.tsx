'use client';

import { ExternalLink, MapPinned, Printer, Scale, X } from "lucide-react";
import type { CaseAlert } from "@/lib/api";

interface AnswerModalProps {
  alert: CaseAlert | null;
  onClose: () => void;
}

const fallbackAnswer =
  "Defendant generally denies each claim and asks the court to require the plaintiff to prove its case. Defendant reserves all defenses available under Texas law.";

function countdownLabel(daysRemaining: number | null) {
  if (daysRemaining == null) return "Pending";
  if (daysRemaining < 0) return `${Math.abs(daysRemaining)} days past`;
  if (daysRemaining === 0) return "Due today";
  if (daysRemaining === 1) return "1 day left";
  return `${daysRemaining} days left`;
}

export default function AnswerModal({ alert, onClose }: AnswerModalProps) {
  if (!alert) return null;

  const legalAid = alert.legalAid?.length
    ? alert.legalAid
    : [{ name: "TexasLawHelp", url: "https://texaslawhelp.org" }];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4">
      <div
        className="max-h-[90vh] w-full max-w-3xl overflow-y-auto rounded-lg border border-white/10 bg-[#0F0F0F] shadow-urgent"
        role="dialog"
        aria-modal="true"
        aria-labelledby="answer-modal-title"
      >
        <div className="sticky top-0 flex items-center justify-between gap-3 border-b border-white/10 bg-[#0F0F0F] p-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-[#FF4444]">Answer draft</p>
            <h2 id="answer-modal-title" className="mt-1 text-lg font-semibold text-white">{alert.caseNumber}</h2>
            <p className="mt-1 text-sm text-zinc-400">{alert.plaintiff}</p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-md p-2 text-zinc-400 hover:bg-white/10 hover:text-white"
            aria-label="Close answer modal"
          >
            <X className="h-5 w-5" aria-hidden="true" />
          </button>
        </div>

        <div className="space-y-5 p-4">
          <div className="grid gap-3 sm:grid-cols-3">
            <Summary label="Deadline" value={alert.deadlineDate ?? "Pending"} />
            <Summary label="Countdown" value={countdownLabel(alert.daysRemaining)} />
            <Summary label="County" value={`${alert.county} County`} />
          </div>

          <div className="rounded-md border border-white/10 bg-black p-4">
            <p className="mb-3 text-xs font-semibold uppercase tracking-[0.14em] text-zinc-500">Prefilled answer text</p>
            <pre className="whitespace-pre-wrap font-mono text-sm leading-6 text-zinc-200">{alert.answerText ?? fallbackAnswer}</pre>
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            <button
              type="button"
              onClick={() => window.print()}
              className="flex h-11 items-center justify-center gap-2 rounded-md bg-[#FF4444] px-4 text-sm font-semibold text-white hover:bg-red-500"
            >
              <Printer className="h-4 w-4" aria-hidden="true" />
              Print answer
            </button>
            {alert.miroBoardUrl ? (
              <a
                href={alert.miroBoardUrl}
                target="_blank"
                rel="noreferrer"
                className="flex h-11 items-center justify-center gap-2 rounded-md border border-white/10 px-4 text-sm font-semibold text-zinc-100 hover:bg-white/10"
              >
                <ExternalLink className="h-4 w-4" aria-hidden="true" />
                Open board
              </a>
            ) : null}
          </div>

          <div>
            <div className="flex items-center gap-2 text-white">
              <Scale className="h-4 w-4" aria-hidden="true" />
              <h3 className="text-sm font-semibold">Legal aid</h3>
            </div>
            <div className="mt-2 grid gap-2 sm:grid-cols-2">
              {legalAid.map((resource) => (
                <div key={resource.name} className="rounded-md border border-white/10 bg-white/[0.04] p-3 text-sm text-zinc-300">
                  <p className="font-medium text-white">{resource.name}</p>
                  {resource.phone ? <p className="mt-1">{resource.phone}</p> : null}
                  {resource.url ? (
                    <a href={resource.url} target="_blank" rel="noreferrer" className="mt-1 inline-flex items-center gap-1 text-red-200 hover:text-red-100">
                      Visit resource
                      <ExternalLink className="h-3.5 w-3.5" aria-hidden="true" />
                    </a>
                  ) : null}
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-md border border-sky-300/20 bg-sky-500/10 p-3 text-sm text-sky-100">
            <div className="flex items-center gap-2">
              <MapPinned className="h-4 w-4" aria-hidden="true" />
              <p className="font-semibold">
                {alert.miroBoardUrl ? "Miro case board ready" : "Miro case board pending"}
              </p>
            </div>
            <p className="mt-1 opacity-85">
              {alert.miroBoardUrl
                ? "Timeline and checklist are available from the board link."
                : "The timeline and checklist link will appear after board generation succeeds."}
            </p>
          </div>

          <p className="rounded-md border border-amber-300/20 bg-amber-500/10 p-3 text-sm text-amber-100">
            This is not legal advice. Contact a licensed attorney.
          </p>
        </div>
      </div>
    </div>
  );
}

function Summary({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-white/10 bg-white/[0.04] p-3">
      <p className="text-xs font-semibold uppercase tracking-[0.12em] text-zinc-500">{label}</p>
      <p className="mt-1 text-sm font-medium text-white">{value}</p>
    </div>
  );
}

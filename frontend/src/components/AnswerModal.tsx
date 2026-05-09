'use client';

import { ExternalLink, Printer, X } from "lucide-react";
import type { CaseAlert } from "@/lib/api";

interface AnswerModalProps {
  alert: CaseAlert | null;
  onClose: () => void;
}

const fallbackAnswer =
  "Defendant generally denies each claim and asks the court to require the plaintiff to prove its case. Defendant reserves all defenses available under Texas law.";

export default function AnswerModal({ alert, onClose }: AnswerModalProps) {
  if (!alert) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4">
      <div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-lg border border-white/10 bg-zinc-950 shadow-urgent">
        <div className="sticky top-0 flex items-center justify-between gap-3 border-b border-white/10 bg-zinc-950 p-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-alert">Answer draft</p>
            <h2 className="mt-1 text-lg font-semibold text-white">{alert.caseNumber}</h2>
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
          <div className="rounded-md border border-white/10 bg-black p-4 font-mono text-sm leading-6 text-zinc-200">
            {alert.answerText ?? fallbackAnswer}
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            <button
              type="button"
              onClick={() => window.print()}
              className="flex h-11 items-center justify-center gap-2 rounded-md bg-alert px-4 text-sm font-semibold text-white hover:bg-red-500"
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
            <h3 className="text-sm font-semibold text-white">Legal aid</h3>
            <div className="mt-2 space-y-2">
              {(alert.legalAid?.length ? alert.legalAid : [{ name: "TexasLawHelp", url: "https://texaslawhelp.org" }]).map(
                (resource) => (
                  <div key={resource.name} className="rounded-md border border-white/10 bg-white/5 p-3 text-sm text-zinc-300">
                    <p className="font-medium text-white">{resource.name}</p>
                    {resource.phone ? <p>{resource.phone}</p> : null}
                    {resource.url ? (
                      <a href={resource.url} target="_blank" rel="noreferrer" className="text-red-200 hover:text-red-100">
                        {resource.url}
                      </a>
                    ) : null}
                  </div>
                ),
              )}
            </div>
          </div>

          <p className="rounded-md border border-amber-300/20 bg-amber-500/10 p-3 text-sm text-amber-100">
            This is not legal advice. Contact a licensed attorney.
          </p>
        </div>
      </div>
    </div>
  );
}

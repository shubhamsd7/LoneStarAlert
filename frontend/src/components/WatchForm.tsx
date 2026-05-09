'use client';

import { FormEvent, useState } from "react";
import { CheckCircle2, Home, Loader2, Mail, MapPin, Search, UserRound } from "lucide-react";
import type { County, WatchType } from "@/lib/api";
import { useAlertStore } from "@/store/alertStore";

const counties: County[] = ["Harris", "Travis", "Dallas", "Bexar"];

const watchCopy = {
  name: {
    label: "Full name",
    placeholder: "Maria R. Garcia",
    hint: "Use the name that would appear on court papers.",
    success: "Name watch ready",
  },
  address: {
    label: "Street address",
    placeholder: "1200 Congress Ave",
    hint: "Street number and street name are enough to start.",
    success: "Address watch ready",
  },
} satisfies Record<WatchType, { label: string; placeholder: string; hint: string; success: string }>;

export default function WatchForm() {
  const [type, setType] = useState<WatchType>("name");
  const [value, setValue] = useState("");
  const [county, setCounty] = useState<County>("Harris");
  const [email, setEmail] = useState("");
  const [attemptedSubmit, setAttemptedSubmit] = useState(false);
  const { addWatch, loading } = useAlertStore();

  const trimmedValue = value.trim();
  const trimmedEmail = email.trim();
  const valueIsReady = trimmedValue.length >= 3;
  const emailIsReady = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(trimmedEmail);
  const canSubmit = valueIsReady && emailIsReady && !loading;
  const copy = watchCopy[type];

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setAttemptedSubmit(true);

    if (!canSubmit) return;

    try {
      await addWatch(type, trimmedValue, county, trimmedEmail);
      setValue("");
      setAttemptedSubmit(false);
    } catch {
      // The store already shows the failure toast.
    }
  }

  return (
    <section className="rounded-lg border border-white/10 bg-[#0F0F0F] p-4 shadow-urgent sm:p-5">
      <div className="mb-5 flex items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[#FF4444]">Start a watch</p>
          <h1 className="mt-2 text-2xl font-semibold text-white">Watch court records</h1>
          <p className="mt-2 text-sm leading-5 text-zinc-400">
            Save a name or address. TxAlert checks public Texas court records and emails you when something matches.
          </p>
        </div>
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-[#FF4444]/10 text-[#FF4444]">
          <Search className="h-5 w-5" aria-hidden="true" />
        </div>
      </div>

      <div className="mb-5 grid grid-cols-2 rounded-md border border-white/10 bg-white/[0.04] p-1">
        {[
          { label: "Watch My Name", value: "name" as const, icon: UserRound },
          { label: "Watch My Address", value: "address" as const, icon: Home },
        ].map((tab) => {
          const Icon = tab.icon;
          const active = type === tab.value;

          return (
            <button
              key={tab.value}
              type="button"
              onClick={() => setType(tab.value)}
              aria-pressed={active}
              className={`flex min-h-11 items-center justify-center gap-2 rounded px-2 text-center text-sm font-medium transition sm:px-3 ${
                active ? "bg-[#FF4444] text-white" : "text-zinc-300 hover:bg-white/10"
              }`}
            >
              <Icon className="h-4 w-4" aria-hidden="true" />
              <span className="leading-tight">{tab.label}</span>
            </button>
          );
        })}
      </div>

      <form onSubmit={onSubmit} className="space-y-4">
        <label className="block">
          <span className="mb-2 flex items-center justify-between gap-3 text-sm font-medium text-zinc-200">
            {copy.label}
            {valueIsReady ? <CheckCircle2 className="h-4 w-4 text-emerald-300" aria-hidden="true" /> : null}
          </span>
          <div className="relative">
            {type === "name" ? (
              <UserRound className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-500" aria-hidden="true" />
            ) : (
              <Home className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-500" aria-hidden="true" />
            )}
            <input
              required
              value={value}
              onChange={(event) => setValue(event.target.value)}
              placeholder={copy.placeholder}
              autoComplete={type === "name" ? "name" : "street-address"}
              aria-invalid={attemptedSubmit && !valueIsReady}
              className="h-12 w-full rounded-md border border-white/10 bg-black pl-10 pr-3 font-mono text-sm text-white outline-none ring-[#FF4444]/40 placeholder:text-zinc-600 focus:ring-2"
            />
          </div>
          <p className={`mt-2 text-xs ${attemptedSubmit && !valueIsReady ? "text-red-200" : "text-zinc-500"}`}>
            {attemptedSubmit && !valueIsReady ? `Enter a ${copy.label.toLowerCase()} with at least 3 characters.` : copy.hint}
          </p>
        </label>

        <div className="grid gap-4 sm:grid-cols-2">
          <label className="block">
            <span className="mb-2 block text-sm font-medium text-zinc-200">County</span>
            <div className="relative">
              <MapPin className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-500" aria-hidden="true" />
              <select
                value={county}
                onChange={(event) => setCounty(event.target.value as County)}
                className="h-12 w-full appearance-none rounded-md border border-white/10 bg-black pl-10 pr-8 font-mono text-sm text-white outline-none ring-[#FF4444]/40 focus:ring-2"
              >
                {counties.map((countyName) => (
                  <option key={countyName} value={countyName}>
                    {countyName}
                  </option>
                ))}
              </select>
            </div>
          </label>

          <label className="block">
            <span className="mb-2 flex items-center justify-between gap-3 text-sm font-medium text-zinc-200">
              Alert email
              {emailIsReady ? <CheckCircle2 className="h-4 w-4 text-emerald-300" aria-hidden="true" /> : null}
            </span>
            <div className="relative">
              <Mail className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-500" aria-hidden="true" />
              <input
                required
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                placeholder="you@example.org"
                autoComplete="email"
                aria-invalid={attemptedSubmit && !emailIsReady}
                className="h-12 w-full rounded-md border border-white/10 bg-black pl-10 pr-3 font-mono text-sm text-white outline-none ring-[#FF4444]/40 placeholder:text-zinc-600 focus:ring-2"
              />
            </div>
            {attemptedSubmit && !emailIsReady ? (
              <p className="mt-2 text-xs text-red-200">Enter an email address for alerts.</p>
            ) : null}
          </label>
        </div>

        <div className="rounded-md border border-white/10 bg-white/[0.04] p-3 text-sm text-zinc-300">
          <p className="font-medium text-white">{copy.success}</p>
          <p className="mt-1 text-xs leading-5 text-zinc-500">
            {county} County public records. We only check the watch you save.
          </p>
        </div>

        <button
          type="submit"
          disabled={!canSubmit}
          className="flex h-12 w-full items-center justify-center gap-2 rounded-md bg-[#FF4444] px-4 text-sm font-semibold text-white transition hover:bg-red-500 disabled:cursor-not-allowed disabled:bg-zinc-700 disabled:text-zinc-400"
        >
          {loading ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" /> : null}
          {loading ? "Saving watch" : "Save watch"}
        </button>
      </form>
    </section>
  );
}

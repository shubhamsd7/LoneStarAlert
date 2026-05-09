'use client';

import { FormEvent, useState } from "react";
import { Home, Loader2, MapPin, UserRound } from "lucide-react";
import type { County, WatchType } from "@/lib/api";
import { useAlertStore } from "@/store/alertStore";

const counties: County[] = ["Harris", "Travis", "Dallas", "Bexar"];

export default function WatchForm() {
  const [type, setType] = useState<WatchType>("name");
  const [value, setValue] = useState("");
  const [county, setCounty] = useState<County>("Harris");
  const [email, setEmail] = useState("");
  const { createWatch, loading } = useAlertStore();

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await createWatch(type, value.trim(), county, email.trim());
    setValue("");
  }

  return (
    <section className="rounded-lg border border-white/10 bg-zinc-950/80 p-5 shadow-urgent">
      <div className="mb-5 flex items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-alert">Start a watch</p>
          <h1 className="mt-2 text-2xl font-semibold text-white">Monitor a name or address</h1>
        </div>
        <MapPin className="mt-1 h-6 w-6 text-alert" aria-hidden="true" />
      </div>

      <div className="mb-5 grid grid-cols-2 rounded-md border border-white/10 bg-white/5 p-1">
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
              className={`flex min-h-10 items-center justify-center gap-2 rounded px-3 text-sm font-medium transition ${
                active ? "bg-alert text-white" : "text-zinc-300 hover:bg-white/10"
              }`}
            >
              <Icon className="h-4 w-4" aria-hidden="true" />
              {tab.label}
            </button>
          );
        })}
      </div>

      <form onSubmit={onSubmit} className="space-y-4">
        <label className="block">
          <span className="mb-2 block text-sm font-medium text-zinc-200">
            {type === "name" ? "Full name" : "Street address"}
          </span>
          <input
            required
            value={value}
            onChange={(event) => setValue(event.target.value)}
            placeholder={type === "name" ? "Maria R. Garcia" : "1200 Congress Ave"}
            className="h-12 w-full rounded-md border border-white/10 bg-black px-3 font-mono text-sm text-white outline-none ring-alert/40 placeholder:text-zinc-600 focus:ring-2"
          />
        </label>

        <div className="grid gap-4 sm:grid-cols-2">
          <label className="block">
            <span className="mb-2 block text-sm font-medium text-zinc-200">County</span>
            <select
              value={county}
              onChange={(event) => setCounty(event.target.value as County)}
              className="h-12 w-full rounded-md border border-white/10 bg-black px-3 font-mono text-sm text-white outline-none ring-alert/40 focus:ring-2"
            >
              {counties.map((countyName) => (
                <option key={countyName} value={countyName}>
                  {countyName}
                </option>
              ))}
            </select>
          </label>

          <label className="block">
            <span className="mb-2 block text-sm font-medium text-zinc-200">Alert email</span>
            <input
              required
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="you@example.org"
              className="h-12 w-full rounded-md border border-white/10 bg-black px-3 font-mono text-sm text-white outline-none ring-alert/40 placeholder:text-zinc-600 focus:ring-2"
            />
          </label>
        </div>

        <button
          type="submit"
          disabled={loading || !value.trim() || !email.trim()}
          className="flex h-12 w-full items-center justify-center gap-2 rounded-md bg-alert px-4 text-sm font-semibold text-white transition hover:bg-red-500 disabled:cursor-not-allowed disabled:bg-zinc-700 disabled:text-zinc-400"
        >
          {loading ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" /> : null}
          Save watch
        </button>
      </form>
    </section>
  );
}

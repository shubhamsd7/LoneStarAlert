import AlertDashboard from '@/components/AlertDashboard';
import WatchForm from '@/components/WatchForm';

export default function Home() {
  return (
    <main className="min-h-screen bg-ink">
      <div className="border-b border-white/10 bg-black/30">
        <div className="mx-auto flex w-full max-w-7xl flex-col gap-3 px-4 py-4 lg:flex-row lg:items-center lg:justify-between lg:px-6">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[#FF4444]">TxAlert operations</p>
            <h1 className="mt-1 text-2xl font-semibold text-white">Texas civil court monitor</h1>
          </div>
          <div className="grid gap-2 text-xs text-zinc-300 sm:grid-cols-3">
            <Status label="Public records" value="Bounded checks" />
            <Status label="Agent cycle" value="Analyze, alert, recover" />
            <Status label="Next action" value="Answer + legal aid" />
          </div>
        </div>
      </div>

      <div className="mx-auto grid w-full max-w-7xl gap-6 px-4 py-6 lg:grid-cols-[420px_1fr] lg:px-6">
        <aside className="space-y-4 lg:sticky lg:top-6 lg:h-fit">
          <WatchForm />
          <section className="rounded-lg border border-white/10 bg-[#0F0F0F] p-4">
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-zinc-500">Workflow</p>
            <div className="mt-3 grid gap-3 text-sm text-zinc-300">
              {["Watch saved", "Court records checked", "Risk and pattern enriched", "Answer package prepared"].map(
                (item, index) => (
                  <div key={item} className="flex items-center gap-3">
                    <span className="flex h-6 w-6 items-center justify-center rounded bg-white/[0.06] font-mono text-xs text-zinc-400">
                      {index + 1}
                    </span>
                    <span>{item}</span>
                  </div>
                ),
              )}
            </div>
          </section>
        </aside>
        <AlertDashboard />
      </div>
    </main>
  );
}

function Status({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-white/10 bg-white/[0.04] px-3 py-2">
      <p className="font-semibold text-white">{label}</p>
      <p className="mt-1 text-zinc-500">{value}</p>
    </div>
  );
}

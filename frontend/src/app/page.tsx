import AlertDashboard from '@/components/AlertDashboard';
import WatchForm from '@/components/WatchForm';

export default function Home() {
  return (
    <main className="min-h-screen bg-ink">
      <div className="mx-auto grid w-full max-w-7xl gap-6 px-4 py-6 lg:grid-cols-[420px_1fr] lg:px-6">
        <aside className="lg:sticky lg:top-6 lg:h-fit">
          <WatchForm />
          <div className="mt-4 rounded-lg border border-white/10 bg-white/[0.03] p-4 text-sm leading-6 text-zinc-400">
            TxAlert monitors bounded public Texas court data and turns new case signals into plain-language next steps.
          </div>
        </aside>
        <AlertDashboard />
      </div>
    </main>
  );
}

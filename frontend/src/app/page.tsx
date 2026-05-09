import AlertDashboard from '@/components/AlertDashboard';
import WatchForm from '@/components/WatchForm';

export default function Home() {
  return (
    <main className="min-h-screen bg-ink">
      <div className="mx-auto grid w-full max-w-7xl gap-6 px-4 py-6 lg:grid-cols-[420px_1fr] lg:px-6">
        <aside className="lg:sticky lg:top-6 lg:h-fit">
          <WatchForm />
        </aside>
        <AlertDashboard />
      </div>
    </main>
  );
}

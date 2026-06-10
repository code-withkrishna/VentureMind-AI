export default function Loading() {
  return (
    <main className="flex min-h-screen items-center justify-center">
      <div className="flex flex-col items-center gap-4">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-gold-500 border-t-transparent" />
        <p className="text-sm text-muted-foreground">Loading VentureMind AI…</p>
      </div>
    </main>
  );
}

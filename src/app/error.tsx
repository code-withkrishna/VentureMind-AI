"use client";

import { useEffect } from "react";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Application error:", error);
  }, [error]);

  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-6 p-8 text-center">
      <div className="rounded-xl border border-red-500/20 bg-red-500/5 p-8 max-w-md">
        <h2 className="text-xl font-semibold text-red-400 mb-3">Something went wrong</h2>
        <p className="text-sm text-muted-foreground mb-6">
          An unexpected error occurred. Please try again.
        </p>
        <button
          onClick={reset}
          className="inline-flex items-center justify-center rounded-lg bg-gold-500 px-6 py-2.5 text-sm font-medium text-ink-950 transition-colors hover:bg-gold-400"
        >
          Try again
        </button>
      </div>
    </main>
  );
}

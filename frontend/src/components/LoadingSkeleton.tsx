"use client";

/** Reusable loading skeleton with shimmer animation. */
export default function LoadingSkeleton({
  lines = 5,
  title = "Analysing...",
}: {
  lines?: number;
  title?: string;
}) {
  return (
    <div className="animate-fade-in space-y-6 py-4">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="relative h-5 w-5">
          <div className="absolute inset-0 animate-spin rounded-full border-2 border-sentinel-500 border-t-transparent" />
        </div>
        <span className="text-sm font-medium text-sentinel-400">{title}</span>
      </div>

      {/* Skeleton blocks */}
      <div className="space-y-4">
        {/* Score skeleton */}
        <div className="glass-card p-6">
          <div className="shimmer mb-3 h-3 w-24 rounded-full bg-white/[0.04]" />
          <div className="shimmer mb-4 h-10 w-32 rounded-lg bg-white/[0.04]" />
          <div className="shimmer h-2 w-full rounded-full bg-white/[0.04]" />
        </div>

        {/* Detail skeletons */}
        <div className="glass-card space-y-3 p-6">
          {Array.from({ length: lines }).map((_, i) => (
            <div
              key={i}
              className="shimmer h-3 rounded-full bg-white/[0.04]"
              style={{ width: `${Math.max(40, 100 - i * 12)}%`, animationDelay: `${i * 0.15}s` }}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

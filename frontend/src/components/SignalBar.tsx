"use client";

interface SignalBarProps {
  label: string;
  score: number; // 0–1
  count: number;
  keywords: string[];
  color: string; // tailwind color class, e.g. 'red' | 'orange' | 'yellow'
}

const COLOR_MAP: Record<string, { bg: string; fill: string; badge: string }> = {
  red: {
    bg: "bg-red-500/10",
    fill: "bg-red-500",
    badge: "bg-red-500/15 text-red-400 border-red-500/20",
  },
  orange: {
    bg: "bg-orange-500/10",
    fill: "bg-orange-500",
    badge: "bg-orange-500/15 text-orange-400 border-orange-500/20",
  },
  yellow: {
    bg: "bg-yellow-500/10",
    fill: "bg-yellow-500",
    badge: "bg-yellow-500/15 text-yellow-400 border-yellow-500/20",
  },
  blue: {
    bg: "bg-blue-500/10",
    fill: "bg-blue-500",
    badge: "bg-blue-500/15 text-blue-400 border-blue-500/20",
  },
};

export default function SignalBar({ label, score, count, keywords, color }: SignalBarProps) {
  const c = COLOR_MAP[color] ?? COLOR_MAP.blue;

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-slate-300">{label}</span>
        <div className="flex items-center gap-2">
          <span className="text-xs tabular-nums text-slate-500">
            {Math.round(score * 100)}%
          </span>
          {count > 0 && (
            <span className={`rounded-full border px-2 py-0.5 text-[10px] font-semibold ${c.badge}`}>
              {count} found
            </span>
          )}
        </div>
      </div>

      {/* Bar */}
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-700/50">
        {score > 0 && (
          <div
            className={`h-full rounded-full ${c.fill} transition-all duration-700`}
            style={{ width: `${Math.max(Math.min(score * 100, 100), 2)}%` }}
          />
        )}
      </div>

      {/* Keywords */}
      {keywords.length > 0 && (
        <div className="flex flex-wrap gap-1.5 pt-1">
          {keywords.slice(0, 6).map((kw, i) => (
            <span
              key={i}
              className="rounded-md border border-white/[0.06] bg-white/[0.03] px-2 py-0.5 text-[11px] text-slate-500"
            >
              {kw}
            </span>
          ))}
          {keywords.length > 6 && (
            <span className="px-2 py-0.5 text-[11px] text-slate-600">
              +{keywords.length - 6} more
            </span>
          )}
        </div>
      )}
    </div>
  );
}

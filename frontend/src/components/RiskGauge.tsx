"use client";

import { useEffect, useState } from "react";

interface RiskGaugeProps {
  score: number; // 0–1
  riskLevel: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  label?: string;
  size?: "sm" | "md" | "lg";
}

const RISK_COLORS = {
  LOW: { bar: "bg-emerald-500", text: "text-emerald-400", glow: "shadow-emerald-500/20" },
  MEDIUM: { bar: "bg-yellow-500", text: "text-yellow-400", glow: "shadow-yellow-500/20" },
  HIGH: { bar: "bg-orange-500", text: "text-orange-400", glow: "shadow-orange-500/20" },
  CRITICAL: { bar: "bg-red-500", text: "text-red-400", glow: "shadow-red-500/20" },
};

const SIZE_CONFIG = {
  sm: { height: "h-1.5", textSize: "text-xl", labelSize: "text-xs" },
  md: { height: "h-2", textSize: "text-3xl", labelSize: "text-sm" },
  lg: { height: "h-3", textSize: "text-5xl", labelSize: "text-base" },
};

export default function RiskGauge({
  score,
  riskLevel,
  label = "Risk Score",
  size = "md",
}: RiskGaugeProps) {
  const [animatedScore, setAnimatedScore] = useState(0);
  const colors = RISK_COLORS[riskLevel];
  const sizeConf = SIZE_CONFIG[size];

  useEffect(() => {
    // Animate from 0 to target score
    const duration = 1200;
    const start = performance.now();
    const animate = (now: number) => {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      // Ease-out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      setAnimatedScore(score * eased);
      if (progress < 1) requestAnimationFrame(animate);
    };
    requestAnimationFrame(animate);
  }, [score]);

  const percentage = Math.round(animatedScore * 100);

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-end justify-between">
        <span className={`${sizeConf.labelSize} font-medium text-slate-400`}>
          {label}
        </span>
        <span className={`risk-badge risk-${riskLevel.toLowerCase()}`}>
          {riskLevel}
        </span>
      </div>

      {/* Score number */}
      <div className={`${sizeConf.textSize} font-bold tabular-nums ${colors.text}`}>
        {percentage}
        <span className="text-[0.5em] font-medium text-slate-600">%</span>
      </div>

      {/* Progress bar */}
      <div className={`progress-track ${sizeConf.height}`}>
        <div
          className={`${sizeConf.height} rounded-full ${colors.bar} shadow-lg ${colors.glow} transition-all duration-100`}
          style={{ width: `${animatedScore * 100}%` }}
        />
      </div>

      {/* Scale markers */}
      <div className="flex justify-between text-[10px] text-slate-700">
        <span>0</span>
        <span>25</span>
        <span>50</span>
        <span>75</span>
        <span>100</span>
      </div>
    </div>
  );
}

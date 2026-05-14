"use client";

import React, { useEffect, useState } from "react";
import { cn, riskGaugeColor, riskLabel } from "@/lib/utils";

interface RiskGaugeProps {
  score: number;
  size?: number;
  strokeWidth?: number;
  className?: string;
}

export const RiskGauge = React.memo(function RiskGauge({
  score,
  size = 140,
  strokeWidth = 10,
  className,
}: RiskGaugeProps) {
  const [animatedScore, setAnimatedScore] = useState(0);

  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const normalizedScore = Math.min(Math.max(score, 0), 10);
  const progress = normalizedScore / 10;
  const dashOffset = circumference * (1 - progress);
  const color = riskGaugeColor(normalizedScore);
  const label = riskLabel(normalizedScore);

  useEffect(() => {
    let frame: number;
    const start = performance.now();
    const duration = 1000;
    const from = 0;
    const to = normalizedScore;

    const animate = (now: number) => {
      const elapsed = now - start;
      const t = Math.min(elapsed / duration, 1);
      // Ease-out cubic
      const eased = 1 - Math.pow(1 - t, 3);
      setAnimatedScore(Math.round((from + (to - from) * eased) * 10) / 10);
      if (t < 1) frame = requestAnimationFrame(animate);
    };

    frame = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(frame);
  }, [normalizedScore]);

  return (
    <div className={cn("flex flex-col items-center gap-2", className)}>
      <div className="relative" style={{ width: size, height: size }}>
        <svg
          width={size}
          height={size}
          className="transform -rotate-90"
          aria-hidden="true"
        >
          {/* Background ring */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="hsl(214 32% 91%)"
            strokeWidth={strokeWidth}
          />
          {/* Progress ring */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke={color}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={dashOffset}
            className="transition-[stroke-dashoffset] duration-1000 ease-out"
          />
        </svg>

        {/* Center score */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span
            className="text-3xl font-bold tabular-nums"
            style={{ color }}
          >
            {animatedScore.toFixed(1)}
          </span>
          <span className="text-[11px] font-medium text-muted-foreground mt-0.5">
            out of 10
          </span>
        </div>
      </div>

      <div
        className={cn(
          "inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-semibold",
          score <= 3
            ? "bg-emerald-50 border-emerald-200 text-emerald-700"
            : score <= 6
              ? "bg-amber-50 border-amber-200 text-amber-700"
              : "bg-red-50 border-red-200 text-red-700"
        )}
      >
        <span
          className="h-1.5 w-1.5 rounded-full"
          style={{ backgroundColor: color }}
        />
        {label} Risk
      </div>
    </div>
  );
});

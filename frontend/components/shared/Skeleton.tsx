"use client";

import React from "react";
import { cn } from "@/lib/utils";

interface SkeletonProps {
  className?: string;
}

export const Skeleton = React.memo(function Skeleton({
  className,
}: SkeletonProps) {
  return (
    <div
      className={cn("shimmer rounded-md", className)}
      aria-hidden="true"
    />
  );
});

/* ── Pre-built skeleton variants ──────────────────────────────────────────── */

export const SkeletonCard = React.memo(function SkeletonCard() {
  return (
    <div className="rounded-xl border border-border bg-card p-6 space-y-4">
      <div className="flex items-center justify-between">
        <Skeleton className="h-4 w-24" />
        <Skeleton className="h-6 w-16 rounded-full" />
      </div>
      <Skeleton className="h-8 w-20" />
      <Skeleton className="h-3 w-32" />
    </div>
  );
});

export const SkeletonTableRow = React.memo(function SkeletonTableRow() {
  return (
    <div className="flex items-center gap-4 py-4 px-4 border-b border-border/50">
      <Skeleton className="h-4 w-40" />
      <Skeleton className="h-4 w-24" />
      <Skeleton className="h-4 w-20" />
      <Skeleton className="h-6 w-14 rounded-full" />
      <Skeleton className="h-8 w-16 rounded-md ml-auto" />
    </div>
  );
});

export const SkeletonGauge = React.memo(function SkeletonGauge() {
  return (
    <div className="flex flex-col items-center gap-3">
      <Skeleton className="h-32 w-32 rounded-full" />
      <Skeleton className="h-4 w-20" />
    </div>
  );
});

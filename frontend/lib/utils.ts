import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/* ── Risk helpers ──────────────────────────────────────────────────────────── */

export function riskColor(score: number): string {
  if (score <= 3) return "text-emerald-600";
  if (score <= 6) return "text-amber-500";
  return "text-red-500";
}

export function riskBg(score: number): string {
  if (score <= 3) return "bg-emerald-50 border-emerald-200 text-emerald-700";
  if (score <= 6) return "bg-amber-50 border-amber-200 text-amber-700";
  return "bg-red-50 border-red-200 text-red-700";
}

export function riskLabel(score: number): string {
  if (score <= 3) return "Low";
  if (score <= 6) return "Medium";
  return "High";
}

export function riskGaugeColor(score: number): string {
  if (score <= 3) return "#10B981";
  if (score <= 6) return "#F59E0B";
  return "#EF4444";
}

/* ── Formatting helpers ────────────────────────────────────────────────────── */

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function formatRelativeDate(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "Just now";
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `${days}d ago`;
  return formatDate(iso);
}

export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function getInitials(name: string): string {
  return name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);
}

export function clauseTypeLabel(type: string): string {
  const map: Record<string, string> = {
    termination: "Termination",
    payment: "Payment",
    liability: "Liability",
    confidentiality: "Confidentiality",
    ip_ownership: "IP Ownership",
    warranty: "Warranty",
    indemnification: "Indemnification",
    dispute_resolution: "Dispute Resolution",
    force_majeure: "Force Majeure",
    governing_law: "Governing Law",
    assignment: "Assignment",
    amendment: "Amendment",
    general: "General",
  };
  return map[type] ?? type;
}

/* ── Utilities ─────────────────────────────────────────────────────────────── */

export function debounce<T extends (...args: unknown[]) => void>(
  fn: T,
  ms: number
): (...args: Parameters<T>) => void {
  let timer: ReturnType<typeof setTimeout>;
  return (...args: Parameters<T>) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), ms);
  };
}

export function statusConfig(status: string) {
  switch (status) {
    case "complete":
      return {
        label: "Analyzed",
        className: "bg-emerald-50 text-emerald-700 border-emerald-200",
        dot: "bg-emerald-500",
      };
    case "analyzing":
      return {
        label: "Analyzing",
        className: "bg-blue-50 text-blue-700 border-blue-200",
        dot: "bg-blue-500 animate-pulse-soft",
      };
    case "pending":
      return {
        label: "Pending",
        className: "bg-slate-50 text-slate-600 border-slate-200",
        dot: "bg-slate-400",
      };
    case "error":
      return {
        label: "Failed",
        className: "bg-red-50 text-red-700 border-red-200",
        dot: "bg-red-500",
      };
    default:
      return {
        label: status,
        className: "bg-slate-50 text-slate-600 border-slate-200",
        dot: "bg-slate-400",
      };
  }
}

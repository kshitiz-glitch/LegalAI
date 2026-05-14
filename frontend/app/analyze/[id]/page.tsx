"use client";

import React, { useEffect, useState, useCallback, useMemo } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  Download,
  Clock,
  Users,
  Calendar,
  FileText,
  ChevronDown,
  Loader2,
  AlertTriangle,
  MessageSquare,
  Shield,
  Target,
  Handshake,
  Mail,
} from "lucide-react";
import { contractsApi } from "@/lib/api";
import { useAuthStore, useHasHydrated } from "@/lib/store";
import { RiskGauge } from "@/components/analysis/RiskGauge";
import { ClauseCard } from "@/components/analysis/ClauseCard";
import { Skeleton, SkeletonGauge } from "@/components/shared/Skeleton";
import {
  cn,
  formatDate,
  riskBg,
  riskLabel,
  clauseTypeLabel,
} from "@/lib/utils";
import { toast } from "sonner";
import type { Contract } from "@/types";

export default function AnalyzePage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const token = useAuthStore((s) => s.token);
  const hydrated = useHasHydrated();
  const [contract, setContract] = useState<Contract | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"clauses" | "redlines" | "strategy">("clauses");
  const [clauseFilter, setClauseFilter] = useState<string>("all");

  // Auth guard — wait for hydration
  useEffect(() => {
    if (hydrated && !token) router.replace("/login");
  }, [hydrated, token, router]);

  // Fetch contract (with polling while analyzing)
  const fetchContract = useCallback(async () => {
    if (!token || !id) return "error" as const;
    try {
      const data = await contractsApi.get(Number(id), token);
      setContract(data);
      return data.status;
    } catch {
      toast.error("Failed to load contract");
      router.push("/dashboard");
      return "error" as const;
    } finally {
      setLoading(false);
    }
  }, [token, id, router]);

  useEffect(() => {
    let interval: ReturnType<typeof setInterval>;
    let stopped = false;
    fetchContract().then((status) => {
      if (stopped) return;
      if (status === "analyzing" || status === "pending") {
        interval = setInterval(async () => {
          const newStatus = await fetchContract();
          if (!newStatus || newStatus === "complete" || newStatus === "error") {
            clearInterval(interval);
          }
        }, 4000);
      }
    });
    return () => { stopped = true; clearInterval(interval); };
  }, [fetchContract]);

  // Filter clauses
  const filteredClauses = useMemo(() => {
    if (!contract?.clauses) return [];
    const filtered = clauseFilter === "all"
      ? [...contract.clauses]
      : contract.clauses.filter((c) => c.clause_type === clauseFilter);
    return filtered.sort((a, b) => b.risk_score - a.risk_score);
  }, [contract?.clauses, clauseFilter]);

  // Clause type counts
  const clauseTypes = useMemo(() => {
    if (!contract?.clauses) return [];
    const counts: Record<string, number> = {};
    contract.clauses.forEach((c) => {
      counts[c.clause_type] = (counts[c.clause_type] || 0) + 1;
    });
    return Object.entries(counts)
      .sort((a, b) => b[1] - a[1])
      .map(([type, count]) => ({ type, count }));
  }, [contract?.clauses]);

  const isAnalyzing = contract?.status === "analyzing" || contract?.status === "pending";

  if (loading) return <AnalysisSkeleton />;
  if (!contract) return null;

  return (
    <div className="min-h-screen bg-background dot-bg">
      {/* Top bar */}
      <div className="sticky top-0 z-40 border-b border-border bg-white/90 backdrop-blur-md">
        <div className="mx-auto max-w-7xl flex items-center justify-between px-4 sm:px-6 h-14">
          <div className="flex items-center gap-3">
            <Link
              href="/dashboard"
              className="flex items-center gap-2 rounded-lg px-2.5 py-1.5 text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
            >
              <ArrowLeft className="h-4 w-4" />
              <span className="hidden sm:inline">Dashboard</span>
            </Link>
            <div className="h-5 w-px bg-border" />
            <h1 className="text-sm font-heading font-semibold text-foreground truncate max-w-[200px] sm:max-w-none">
              {contract.filename}
            </h1>
          </div>

          {contract.status === "complete" && (
            <button
              onClick={() => toast.info("Export feature coming soon")}
              className="inline-flex items-center gap-2 rounded-lg bg-primary px-3.5 py-2 text-xs font-semibold text-white transition-all hover:bg-primary/90 hover:shadow-button-hover active:scale-[0.98]"
            >
              <Download className="h-3.5 w-3.5" />
              Export
            </button>
          )}
        </div>

        {/* Analyzing progress */}
        {isAnalyzing && (
          <div className="h-1 w-full bg-muted overflow-hidden">
            <div className="h-full w-1/3 bg-primary rounded-full animate-[shimmer_1.5s_infinite_ease-in-out]" />
          </div>
        )}
      </div>

      {/* Analyzing state */}
      {isAnalyzing && (
        <div className="mx-auto max-w-7xl px-4 sm:px-6 py-20 text-center animate-fade-in">
          <div className="inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/10 mb-5">
            <Loader2 className="h-7 w-7 text-primary animate-spin" />
          </div>
          <h2 className="text-xl font-semibold text-foreground">
            Analyzing your contract...
          </h2>
          <p className="mt-2 text-sm text-muted-foreground max-w-md mx-auto">
            Our AI is reading every clause, assessing risks, and generating
            recommendations. This usually takes about 60 seconds.
          </p>
          <div className="mt-8 flex items-center justify-center gap-6 text-xs text-muted-foreground">
            <span className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-primary animate-pulse-soft" />
              Extracting clauses
            </span>
            <span className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-muted-foreground/30" />
              Risk assessment
            </span>
            <span className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-muted-foreground/30" />
              Generating suggestions
            </span>
          </div>
        </div>
      )}

      {/* Error state */}
      {contract.status === "error" && (
        <div className="mx-auto max-w-7xl px-4 sm:px-6 py-20 text-center animate-fade-in">
          <div className="inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-red-50 mb-5">
            <AlertTriangle className="h-7 w-7 text-red-500" />
          </div>
          <h2 className="text-xl font-semibold text-foreground">
            Analysis failed
          </h2>
          <p className="mt-2 text-sm text-muted-foreground">
            Something went wrong. Please try uploading the contract again.
          </p>
          <Link
            href="/dashboard"
            className="mt-6 inline-flex items-center gap-2 rounded-lg bg-primary px-5 py-2.5 text-sm font-medium text-white hover:bg-primary/90 transition-colors"
          >
            Back to Dashboard
          </Link>
        </div>
      )}

      {/* Complete analysis view */}
      {contract.status === "complete" && (
        <div className="mx-auto max-w-7xl px-4 sm:px-6 py-6 animate-fade-in">
          <div className="grid gap-6 lg:grid-cols-12">
            {/* ── Left Column (Summary & Content) ──────────────────────── */}
            <div className="lg:col-span-7 xl:col-span-8 space-y-6">
              {/* Summary Card */}
              {contract.summary && (
                <div className="rounded-xl border border-border bg-card p-6 shadow-card">
                  <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-3">
                    Summary
                  </h2>
                  <p className="text-sm text-foreground leading-relaxed">
                    {contract.summary}
                  </p>
                </div>
              )}

              {/* Meta Info Row */}
              <div className="grid gap-4 grid-cols-1 sm:grid-cols-3">
                {/* Parties */}
                {contract.parties && Object.keys(contract.parties).length > 0 && (
                  <div className="rounded-xl border border-border bg-card p-4 shadow-card">
                    <div className="flex items-center gap-2 mb-2.5">
                      <Users className="h-4 w-4 text-muted-foreground" />
                      <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                        Parties
                      </span>
                    </div>
                    <div className="space-y-1.5">
                      {Object.entries(contract.parties).map(([role, name]) => (
                        <div key={role}>
                          <span className="text-xs text-muted-foreground capitalize">
                            {role}:
                          </span>
                          <p className="text-sm font-medium text-foreground truncate">
                            {String(name)}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Key Dates */}
                {contract.key_dates && (
                  <div className="rounded-xl border border-border bg-card p-4 shadow-card">
                    <div className="flex items-center gap-2 mb-2.5">
                      <Calendar className="h-4 w-4 text-muted-foreground" />
                      <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                        Key Dates
                      </span>
                    </div>
                    <div className="space-y-1.5">
                      {contract.key_dates.effective_date && (
                        <div>
                          <span className="text-xs text-muted-foreground">
                            Effective:
                          </span>
                          <p className="text-sm font-medium text-foreground">
                            {contract.key_dates.effective_date}
                          </p>
                        </div>
                      )}
                      {contract.key_dates.expiry_date && (
                        <div>
                          <span className="text-xs text-muted-foreground">
                            Expiry:
                          </span>
                          <p className="text-sm font-medium text-foreground">
                            {contract.key_dates.expiry_date}
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Contract Type */}
                <div className="rounded-xl border border-border bg-card p-4 shadow-card">
                  <div className="flex items-center gap-2 mb-2.5">
                    <FileText className="h-4 w-4 text-muted-foreground" />
                    <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                      Details
                    </span>
                  </div>
                  <div className="space-y-1.5">
                    <div>
                      <span className="text-xs text-muted-foreground">Type:</span>
                      <p className="text-sm font-medium text-foreground">
                        {contract.contract_type ?? "Unknown"}
                      </p>
                    </div>
                    <div>
                      <span className="text-xs text-muted-foreground">
                        Uploaded:
                      </span>
                      <p className="text-sm font-medium text-foreground">
                        {formatDate(contract.created_at)}
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Tab Navigation — filled pills */}
              <div className="flex gap-1.5 p-1 rounded-xl bg-muted/60 w-fit">
                {[
                  { key: "clauses" as const, label: "Clauses", icon: Shield, count: contract.clauses?.length },
                  { key: "redlines" as const, label: "Redlines", icon: FileText, count: contract.redlines?.length },
                  { key: "strategy" as const, label: "Strategy", icon: Target },
                ].map(({ key, label, icon: Icon, count }) => (
                  <button
                    key={key}
                    onClick={() => setActiveTab(key)}
                    className={cn(
                      "flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg transition-all duration-150",
                      activeTab === key
                        ? "bg-card text-foreground shadow-card"
                        : "text-muted-foreground hover:text-foreground"
                    )}
                  >
                    <Icon className="h-4 w-4" />
                    {label}
                    {count !== undefined && (
                      <span className={cn("rounded-full px-2 py-0.5 text-xs tabular-nums", activeTab === key ? "bg-muted" : "bg-transparent")}>
                        {count}
                      </span>
                    )}
                  </button>
                ))}
              </div>

              {/* Tab Content */}
              {activeTab === "clauses" && (
                <div className="space-y-4">
                  {/* Clause type filters */}
                  <div className="flex gap-2 overflow-x-auto no-scrollbar pb-1">
                    <button
                      onClick={() => setClauseFilter("all")}
                      className={cn(
                        "shrink-0 rounded-full px-3 py-1 text-xs font-medium border transition-colors",
                        clauseFilter === "all"
                          ? "bg-primary text-white border-primary"
                          : "bg-white text-muted-foreground border-border hover:border-primary/30"
                      )}
                    >
                      All ({contract.clauses?.length ?? 0})
                    </button>
                    {clauseTypes.map(({ type, count }) => (
                      <button
                        key={type}
                        onClick={() => setClauseFilter(type)}
                        className={cn(
                          "shrink-0 rounded-full px-3 py-1 text-xs font-medium border transition-colors",
                          clauseFilter === type
                            ? "bg-primary text-white border-primary"
                            : "bg-white text-muted-foreground border-border hover:border-primary/30"
                        )}
                      >
                        {clauseTypeLabel(type)} ({count})
                      </button>
                    ))}
                  </div>

                  {/* Clause cards */}
                  <div className="space-y-3">
                    {filteredClauses.map((clause, i) => (
                      <ClauseCard key={i} clause={clause} index={i} />
                    ))}
                    {filteredClauses.length === 0 && (
                      <p className="text-center text-sm text-muted-foreground py-8">
                        No clauses match this filter.
                      </p>
                    )}
                  </div>
                </div>
              )}

              {activeTab === "redlines" && (
                <div className="space-y-4">
                  {contract.redlines && contract.redlines.length > 0 ? (
                    contract.redlines.map((redline, i) => (
                      <div
                        key={i}
                        className="rounded-xl border border-border bg-card p-5 shadow-card animate-slide-up"
                        style={{ animationDelay: `${i * 60}ms` }}
                      >
                        <div className="grid gap-4 sm:grid-cols-2">
                          <div>
                            <span className="text-xs font-semibold text-red-500 uppercase tracking-wider">
                              Original
                            </span>
                            <p className="mt-1.5 text-sm text-foreground leading-relaxed bg-red-50/50 rounded-lg p-3 border border-red-100">
                              {redline.original}
                            </p>
                          </div>
                          <div>
                            <span className="text-xs font-semibold text-emerald-600 uppercase tracking-wider">
                              Suggested
                            </span>
                            <p className="mt-1.5 text-sm text-foreground leading-relaxed bg-emerald-50/50 rounded-lg p-3 border border-emerald-100">
                              {redline.rewritten}
                            </p>
                          </div>
                        </div>
                        <div className="mt-3 pt-3 border-t border-border/50">
                          <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                            Rationale
                          </span>
                          <p className="mt-1 text-sm text-muted-foreground leading-relaxed">
                            {redline.rationale}
                          </p>
                        </div>
                        {redline.changes.length > 0 && (
                          <div className="flex flex-wrap gap-1.5 mt-3">
                            {redline.changes.map((c, j) => (
                              <span
                                key={j}
                                className="rounded-md bg-muted px-2 py-0.5 text-[11px] font-medium text-muted-foreground"
                              >
                                {c}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    ))
                  ) : (
                    <p className="text-center text-sm text-muted-foreground py-8">
                      No redline suggestions available.
                    </p>
                  )}
                </div>
              )}

              {activeTab === "strategy" && contract.negotiation_strategy && (
                <div className="space-y-4 animate-fade-in">
                  {/* Priority Issues */}
                  {contract.negotiation_strategy.priority_issues?.length > 0 && (
                    <div className="rounded-xl border border-border bg-card p-5 shadow-card">
                      <div className="flex items-center gap-2 mb-3">
                        <AlertTriangle className="h-4 w-4 text-amber-500" />
                        <h3 className="text-sm font-semibold text-foreground">Priority Issues</h3>
                      </div>
                      <ul className="space-y-2">
                        {contract.negotiation_strategy.priority_issues.map((item, i) => (
                          <li key={i} className="flex items-start gap-2 text-sm text-foreground">
                            <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-amber-500" />
                            {item}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Deal Breakers */}
                  {contract.negotiation_strategy.deal_breakers?.length > 0 && (
                    <div className="rounded-xl border border-red-200 bg-red-50/30 p-5">
                      <div className="flex items-center gap-2 mb-3">
                        <Shield className="h-4 w-4 text-red-500" />
                        <h3 className="text-sm font-semibold text-red-700">Deal Breakers</h3>
                      </div>
                      <ul className="space-y-2">
                        {contract.negotiation_strategy.deal_breakers.map((item, i) => (
                          <li key={i} className="flex items-start gap-2 text-sm text-red-700">
                            <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-red-500" />
                            {item}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Negotiable Points */}
                  {contract.negotiation_strategy.negotiable_points?.length > 0 && (
                    <div className="rounded-xl border border-border bg-card p-5 shadow-card">
                      <div className="flex items-center gap-2 mb-3">
                        <Handshake className="h-4 w-4 text-emerald-500" />
                        <h3 className="text-sm font-semibold text-foreground">Negotiable Points</h3>
                      </div>
                      <ul className="space-y-2">
                        {contract.negotiation_strategy.negotiable_points.map((item, i) => (
                          <li key={i} className="flex items-start gap-2 text-sm text-foreground">
                            <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-500" />
                            {item}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Email Opener */}
                  {contract.negotiation_strategy.email_opener && (
                    <div className="rounded-xl border border-border bg-card p-5 shadow-card">
                      <div className="flex items-center gap-2 mb-3">
                        <Mail className="h-4 w-4 text-primary" />
                        <h3 className="text-sm font-semibold text-foreground">Email Opener</h3>
                      </div>
                      <div className="rounded-lg bg-muted/50 p-4 text-sm text-foreground leading-relaxed whitespace-pre-line font-mono text-xs">
                        {contract.negotiation_strategy.email_opener}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* ── Right Column (Risk Gauge + Quick Stats) ───────────── */}
            <div className="lg:col-span-5 xl:col-span-4 space-y-6">
              {/* Risk Score */}
              <div className="rounded-xl border border-primary/20 bg-primary/[0.04] p-6 shadow-card">
                <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-5 text-center">
                  Overall Risk Score
                </h2>
                <RiskGauge
                  score={contract.overall_risk_score ?? 0}
                  size={160}
                  className="mx-auto"
                />
              </div>

              {/* Risk Breakdown */}
              {contract.clauses && contract.clauses.length > 0 && (
                <div className="rounded-xl border border-border bg-card p-5 shadow-card">
                  <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-4">
                    Risk Breakdown
                  </h3>
                  <div className="space-y-3">
                    {(() => {
                      const low = contract.clauses.filter(
                        (c) => c.risk_score <= 3
                      ).length;
                      const med = contract.clauses.filter(
                        (c) => c.risk_score > 3 && c.risk_score <= 6
                      ).length;
                      const high = contract.clauses.filter(
                        (c) => c.risk_score > 6
                      ).length;
                      const total = contract.clauses.length;

                      return [
                        {
                          label: "Low Risk",
                          count: low,
                          pct: (low / total) * 100,
                          color: "bg-emerald-500",
                          bg: "bg-emerald-100",
                        },
                        {
                          label: "Medium Risk",
                          count: med,
                          pct: (med / total) * 100,
                          color: "bg-amber-500",
                          bg: "bg-amber-100",
                        },
                        {
                          label: "High Risk",
                          count: high,
                          pct: (high / total) * 100,
                          color: "bg-red-500",
                          bg: "bg-red-100",
                        },
                      ].map(({ label, count, pct, color, bg }) => (
                        <div key={label}>
                          <div className="flex items-center justify-between text-xs mb-1.5">
                            <span className="font-medium text-foreground">
                              {label}
                            </span>
                            <span className="text-muted-foreground tabular-nums">
                              {count} clauses
                            </span>
                          </div>
                          <div className={`h-2 w-full rounded-full ${bg}`}>
                            <div
                              className={`h-full rounded-full ${color} transition-all duration-700 ease-out`}
                              style={{ width: `${pct}%` }}
                            />
                          </div>
                        </div>
                      ));
                    })()}
                  </div>
                </div>
              )}

              {/* Quick Stats */}
              <div className="rounded-xl border border-border bg-card p-5 shadow-card">
                <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-3">
                  Quick Stats
                </h3>
                <div className="space-y-2.5">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Total Clauses</span>
                    <span className="font-semibold text-foreground tabular-nums">
                      {contract.clauses?.length ?? 0}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Redline Suggestions</span>
                    <span className="font-semibold text-foreground tabular-nums">
                      {contract.redlines?.length ?? 0}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Contract Type</span>
                    <span className="font-medium text-foreground">
                      {contract.contract_type ?? "—"}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

/* ── Loading skeleton ──────────────────────────────────────────────────── */
function AnalysisSkeleton() {
  return (
    <div className="min-h-screen bg-background dot-bg">
      <div className="border-b border-border bg-white">
        <div className="mx-auto max-w-7xl flex items-center gap-3 px-4 sm:px-6 h-14">
          <Skeleton className="h-4 w-20" />
          <Skeleton className="h-4 w-40" />
        </div>
      </div>
      <div className="mx-auto max-w-7xl px-4 sm:px-6 py-6">
        <div className="grid gap-6 lg:grid-cols-12">
          <div className="lg:col-span-8 space-y-4">
            <Skeleton className="h-32 w-full rounded-xl" />
            <div className="grid gap-4 grid-cols-3">
              <Skeleton className="h-24 rounded-xl" />
              <Skeleton className="h-24 rounded-xl" />
              <Skeleton className="h-24 rounded-xl" />
            </div>
          </div>
          <div className="lg:col-span-4">
            <SkeletonGauge />
          </div>
        </div>
      </div>
    </div>
  );
}

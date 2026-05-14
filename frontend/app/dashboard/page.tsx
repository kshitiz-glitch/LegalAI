"use client";

import React, { useEffect, useState, useCallback, useMemo } from "react";
import { useRouter } from "next/navigation";
import {
  FileText,
  AlertTriangle,
  TrendingUp,
  Calendar,
  Search,
  Upload,
} from "lucide-react";
import { contractsApi } from "@/lib/api";
import { useAuthStore } from "@/lib/store";
import { FileUpload } from "@/components/upload/FileUpload";
import { ContractTable } from "@/components/shared/ContractTable";
import { SkeletonCard, SkeletonTableRow } from "@/components/shared/Skeleton";
import { cn, formatDate } from "@/lib/utils";
import type { ContractListItem } from "@/types";
import { toast } from "sonner";
import Link from "next/link";

export default function DashboardPage() {
  const router = useRouter();
  const token = useAuthStore((s) => s.token);
  const cachedContracts = useAuthStore((s) => s.contracts);
  const setContracts = useAuthStore((s) => s.setContracts);
  const isStale = useAuthStore((s) => s.isContractsStale);
  const [contracts, setLocalContracts] = useState<ContractListItem[]>(cachedContracts);
  const [loading, setLoading] = useState(cachedContracts.length === 0);

  const fetchContracts = useCallback(async () => {
    if (!token) return;
    try {
      const data = await contractsApi.list(token);
      setLocalContracts(data);
      setContracts(data);
    } catch {
      toast.error("Failed to load contracts");
    } finally {
      setLoading(false);
    }
  }, [token, setContracts]);

  useEffect(() => {
    if (cachedContracts.length > 0 && !isStale()) {
      setLocalContracts(cachedContracts);
      setLoading(false);
    } else {
      fetchContracts();
    }
  }, [fetchContracts, cachedContracts, isStale]);

  const handleUpload = useCallback(
    async (file: File) => {
      if (!token) return;
      const contract = await contractsApi.upload(file, token);
      toast.success("Contract uploaded successfully");
      router.push(`/analyze/${contract.id}`);
    },
    [token, router]
  );

  const handleDelete = useCallback(
    async (id: number) => {
      if (!token) return;
      try {
        await contractsApi.delete(id, token);
        const updated = contracts.filter((c) => c.id !== id);
        setLocalContracts(updated);
        setContracts(updated);
        toast.success("Contract deleted");
      } catch {
        toast.error("Failed to delete contract");
      }
    },
    [token, contracts, setContracts]
  );

  const stats = useMemo(() => {
    const total = contracts.length;
    const highRisk = contracts.filter(
      (c) => c.overall_risk_score !== null && c.overall_risk_score > 6
    ).length;
    const avgScore =
      contracts.filter((c) => c.overall_risk_score !== null).length > 0
        ? contracts
            .filter((c) => c.overall_risk_score !== null)
            .reduce((sum, c) => sum + (c.overall_risk_score ?? 0), 0) /
          contracts.filter((c) => c.overall_risk_score !== null).length
        : 0;
    const now = new Date();
    const thisMonth = contracts.filter((c) => {
      const d = new Date(c.created_at);
      return d.getMonth() === now.getMonth() && d.getFullYear() === now.getFullYear();
    }).length;

    return [
      {
        label: "Total Contracts",
        value: total,
        icon: FileText,
        tint: "bg-primary/[0.06]",
        iconColor: "text-primary",
      },
      {
        label: "High Risk",
        value: highRisk,
        icon: AlertTriangle,
        tint: "bg-red-500/[0.06]",
        iconColor: "text-red-500",
      },
      {
        label: "Avg Risk Score",
        value: avgScore.toFixed(1),
        icon: TrendingUp,
        tint: "bg-amber-500/[0.06]",
        iconColor: "text-amber-600",
      },
      {
        label: "This Month",
        value: thisMonth,
        icon: Calendar,
        tint: "bg-emerald-500/[0.06]",
        iconColor: "text-emerald-600",
      },
    ];
  }, [contracts]);

  const greeting = useMemo(() => {
    const h = new Date().getHours();
    if (h < 12) return "Good morning";
    if (h < 17) return "Good afternoon";
    return "Good evening";
  }, []);

  const userName = useAuthStore((s) => s.user?.full_name?.split(" ")[0] ?? "there");

  const today = new Date().toLocaleDateString("en-US", {
    weekday: "long",
    month: "long",
    day: "numeric",
  });

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header — Clean greeting + actions */}
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-heading font-bold text-foreground">
            {greeting}, {userName}
          </h1>
          <p className="text-sm text-muted-foreground mt-1">{today}</p>
        </div>
        <div className="flex items-center gap-2">
          <Link
            href="/search"
            className="inline-flex items-center gap-2 rounded-lg border border-border bg-white px-4 py-2 text-sm font-medium text-foreground transition-all hover:shadow-card-hover hover:border-primary/30 active:scale-[0.98]"
          >
            <Search className="h-4 w-4 text-muted-foreground" />
            Search Clauses
          </Link>
        </div>
      </div>

      {/* Stats Grid — Tinted backgrounds */}
      <div className="grid gap-4 grid-cols-2 lg:grid-cols-4">
        {loading
          ? Array.from({ length: 4 }).map((_, i) => <SkeletonCard key={i} />)
          : stats.map(({ label, value, icon: Icon, tint, iconColor }, i) => (
              <div
                key={label}
                className={cn(
                  "rounded-xl border border-border/60 p-5 shadow-card animate-slide-up transition-all hover:shadow-card-hover",
                  tint
                )}
                style={{ animationDelay: `${i * 60}ms` }}
              >
                <div className="flex items-center justify-between mb-3">
                  <span className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">
                    {label}
                  </span>
                  <Icon className={cn("h-4 w-4", iconColor)} />
                </div>
                <p className="text-2xl font-heading font-bold text-foreground tabular-nums">
                  {value}
                </p>
              </div>
            ))}
      </div>

      {/* Upload + Recent contracts grid */}
      <div className="grid gap-6 lg:grid-cols-5">
        {/* Upload Section */}
        <div className="lg:col-span-2">
          <div className="rounded-xl border border-border bg-card p-6 shadow-card h-full">
            <h2 className="text-base font-heading font-semibold text-foreground mb-4">
              Upload Contract
            </h2>
            <FileUpload onUpload={handleUpload} />
            <div className="mt-4 rounded-lg bg-muted/60 p-3">
              <p className="text-xs text-muted-foreground leading-relaxed">
                <span className="font-medium text-foreground">How it works:</span>{" "}
                Upload a PDF contract and our AI will analyze every clause,
                assign risk scores, and generate redline suggestions. Analysis
                takes about 60 seconds.
              </p>
            </div>
          </div>
        </div>

        {/* Recent Contracts */}
        <div className="lg:col-span-3">
          <div className="rounded-xl border border-border bg-card shadow-card">
            <div className="flex items-center justify-between p-5 pb-0">
              <h2 className="text-base font-heading font-semibold text-foreground">
                Recent Contracts
              </h2>
              {contracts.length > 5 && (
                <span className="text-xs text-muted-foreground">
                  Showing latest 5 of {contracts.length}
                </span>
              )}
            </div>
            <div className="p-5 pt-4">
              {loading ? (
                <div className="space-y-1">
                  {Array.from({ length: 4 }).map((_, i) => (
                    <SkeletonTableRow key={i} />
                  ))}
                </div>
              ) : (
                <ContractTable
                  contracts={contracts.slice(0, 10)}
                  onDelete={handleDelete}
                />
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

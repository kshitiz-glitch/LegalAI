"use client";

import React, { useState, useMemo, useCallback } from "react";
import Link from "next/link";
import {
  ArrowUpDown,
  Eye,
  Trash2,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { cn, formatDate, formatRelativeDate, statusConfig } from "@/lib/utils";
import type { ContractListItem } from "@/types";

interface ContractTableProps {
  contracts: ContractListItem[];
  onDelete?: (id: number) => void;
  pageSize?: number;
}

type SortKey = "filename" | "created_at" | "overall_risk_score" | "status";
type SortDir = "asc" | "desc";

export const ContractTable = React.memo(function ContractTable({
  contracts,
  onDelete,
  pageSize = 10,
}: ContractTableProps) {
  const [sortKey, setSortKey] = useState<SortKey>("created_at");
  const [sortDir, setSortDir] = useState<SortDir>("desc");
  const [page, setPage] = useState(0);

  const handleSort = useCallback(
    (key: SortKey) => {
      if (sortKey === key) {
        setSortDir((d) => (d === "asc" ? "desc" : "asc"));
      } else {
        setSortKey(key);
        setSortDir("desc");
      }
      setPage(0);
    },
    [sortKey]
  );

  const sorted = useMemo(() => {
    const copy = [...contracts];
    copy.sort((a, b) => {
      let cmp = 0;
      switch (sortKey) {
        case "filename":
          cmp = a.filename.localeCompare(b.filename);
          break;
        case "created_at":
          cmp =
            new Date(a.created_at).getTime() -
            new Date(b.created_at).getTime();
          break;
        case "overall_risk_score":
          cmp = (a.overall_risk_score ?? 0) - (b.overall_risk_score ?? 0);
          break;
        case "status":
          cmp = a.status.localeCompare(b.status);
          break;
      }
      return sortDir === "asc" ? cmp : -cmp;
    });
    return copy;
  }, [contracts, sortKey, sortDir]);

  const totalPages = Math.ceil(sorted.length / pageSize);
  const paginated = useMemo(
    () => sorted.slice(page * pageSize, (page + 1) * pageSize),
    [sorted, page, pageSize]
  );

  const SortHeader = useCallback(
    ({
      label,
      column,
      className,
    }: {
      label: string;
      column: SortKey;
      className?: string;
    }) => (
      <button
        onClick={() => handleSort(column)}
        className={cn(
          "group flex items-center gap-1 text-xs font-semibold uppercase tracking-wider text-muted-foreground hover:text-foreground transition-colors",
          className
        )}
      >
        {label}
        <ArrowUpDown
          className={cn(
            "h-3 w-3 transition-opacity",
            sortKey === column ? "opacity-100" : "opacity-0 group-hover:opacity-50"
          )}
        />
      </button>
    ),
    [handleSort, sortKey]
  );

  if (contracts.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <div className="h-12 w-12 rounded-xl bg-muted flex items-center justify-center mb-3">
          <Eye className="h-5 w-5 text-muted-foreground" />
        </div>
        <p className="text-sm font-medium text-foreground">No contracts yet</p>
        <p className="text-xs text-muted-foreground mt-1">
          Upload a contract to get started
        </p>
      </div>
    );
  }

  return (
    <div>
      {/* Desktop Table */}
      <div className="hidden md:block overflow-hidden rounded-xl border border-border">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border bg-muted/30">
              <th className="px-4 py-3 text-left">
                <SortHeader label="Contract" column="filename" />
              </th>
              <th className="px-4 py-3 text-left">
                <SortHeader label="Status" column="status" />
              </th>
              <th className="px-4 py-3 text-left">
                <SortHeader label="Risk" column="overall_risk_score" />
              </th>
              <th className="px-4 py-3 text-left">
                <SortHeader label="Date" column="created_at" />
              </th>
              <th className="px-4 py-3 text-right">
                <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Actions
                </span>
              </th>
            </tr>
          </thead>
          <tbody>
            {paginated.map((contract) => {
              const status = statusConfig(contract.status);
              return (
                <tr
                  key={contract.id}
                  className="border-b border-border/50 last:border-0 transition-colors hover:bg-primary/[0.03] group"
                >
                  <td className="px-4 py-3">
                    <span className="font-medium text-foreground truncate block max-w-[240px]">
                      {contract.filename}
                    </span>
                    {contract.contract_type && (
                      <span className="text-xs text-muted-foreground">
                        {contract.contract_type}
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={cn(
                        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium",
                        status.className
                      )}
                    >
                      <span
                        className={cn("h-1.5 w-1.5 rounded-full", status.dot)}
                      />
                      {status.label}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    {contract.overall_risk_score !== null ? (
                      <div className="flex items-center gap-2">
                        <div className="h-1.5 w-16 rounded-full bg-muted overflow-hidden">
                          <div
                            className="h-full rounded-full transition-all"
                            style={{
                              width: `${(contract.overall_risk_score / 10) * 100}%`,
                              backgroundColor:
                                contract.overall_risk_score > 6
                                  ? '#EF4444'
                                  : contract.overall_risk_score > 3
                                  ? '#F59E0B'
                                  : '#10B981',
                            }}
                          />
                        </div>
                        <span className="font-semibold tabular-nums text-xs">
                          {contract.overall_risk_score.toFixed(1)}
                        </span>
                      </div>
                    ) : (
                      <span className="text-muted-foreground">—</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-muted-foreground">
                    <span title={formatDate(contract.created_at)}>
                      {formatRelativeDate(contract.created_at)}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center justify-end gap-1">
                      <Link
                        href={`/analyze/${contract.id}`}
                        className="inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium text-primary bg-primary/5 hover:bg-primary/10 transition-colors"
                      >
                        <Eye className="h-3 w-3" />
                        View
                      </Link>
                      {onDelete && (
                        <button
                          onClick={() => onDelete(contract.id)}
                          className="inline-flex items-center rounded-lg p-1.5 text-muted-foreground hover:text-red-500 hover:bg-red-50 transition-colors"
                          title="Delete"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Mobile Cards */}
      <div className="md:hidden space-y-3">
        {paginated.map((contract) => {
          const status = statusConfig(contract.status);
          return (
            <Link
              key={contract.id}
              href={`/analyze/${contract.id}`}
              className="block rounded-xl border border-border bg-card p-4 hover-lift"
            >
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <p className="font-medium text-foreground text-sm truncate">
                    {contract.filename}
                  </p>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    {formatRelativeDate(contract.created_at)}
                  </p>
                </div>
                <span
                  className={cn(
                    "shrink-0 inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-xs font-medium",
                    status.className
                  )}
                >
                  <span
                    className={cn("h-1.5 w-1.5 rounded-full", status.dot)}
                  />
                  {status.label}
                </span>
              </div>
              {contract.overall_risk_score !== null && (
                <div className="mt-2 text-sm font-semibold tabular-nums">
                  Risk: {contract.overall_risk_score.toFixed(1)}/10
                </div>
              )}
            </Link>
          );
        })}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between px-1 pt-4">
          <p className="text-xs text-muted-foreground">
            {page * pageSize + 1}–{Math.min((page + 1) * pageSize, sorted.length)}{" "}
            of {sorted.length}
          </p>
          <div className="flex items-center gap-1">
            <button
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              disabled={page === 0}
              className="inline-flex items-center justify-center h-8 w-8 rounded-lg border border-border text-sm transition-colors hover:bg-muted disabled:opacity-40 disabled:pointer-events-none"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
            <span className="px-2 text-xs text-muted-foreground tabular-nums">
              {page + 1} / {totalPages}
            </span>
            <button
              onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
              disabled={page >= totalPages - 1}
              className="inline-flex items-center justify-center h-8 w-8 rounded-lg border border-border text-sm transition-colors hover:bg-muted disabled:opacity-40 disabled:pointer-events-none"
            >
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
});

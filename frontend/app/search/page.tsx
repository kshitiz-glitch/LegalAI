"use client";

import React, { useState, useCallback, useEffect, useMemo, useRef } from "react";
import { useRouter } from "next/navigation";
import {
  Search as SearchIcon,
  X,
  FileText,
  Loader2,
  ArrowLeft,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import Link from "next/link";
import { searchApi } from "@/lib/api";
import { useAuthStore, useHasHydrated } from "@/lib/store";
import { Navigation } from "@/components/shared/Navigation";
import { cn, clauseTypeLabel, riskBg } from "@/lib/utils";
import { toast } from "sonner";
import type { SearchResult } from "@/types";

const CLAUSE_TYPES = [
  "all",
  "termination",
  "payment",
  "liability",
  "confidentiality",
  "ip_ownership",
  "warranty",
  "indemnification",
  "dispute_resolution",
  "force_majeure",
  "governing_law",
  "assignment",
  "amendment",
] as const;

const CLAUSE_TYPE_STYLE: Record<string, { dot: string; badge: string }> = {
  termination:        { dot: "bg-red-500",     badge: "bg-red-50 text-red-700" },
  payment:            { dot: "bg-emerald-500", badge: "bg-emerald-50 text-emerald-700" },
  liability:          { dot: "bg-amber-500",   badge: "bg-amber-50 text-amber-700" },
  confidentiality:    { dot: "bg-purple-500",  badge: "bg-purple-50 text-purple-700" },
  ip_ownership:       { dot: "bg-indigo-500",  badge: "bg-indigo-50 text-indigo-700" },
  warranty:           { dot: "bg-cyan-500",    badge: "bg-cyan-50 text-cyan-700" },
  indemnification:    { dot: "bg-rose-500",    badge: "bg-rose-50 text-rose-700" },
  dispute_resolution: { dot: "bg-amber-500",   badge: "bg-amber-50 text-amber-700" },
  force_majeure:      { dot: "bg-red-500",     badge: "bg-red-50 text-red-700" },
  governing_law:      { dot: "bg-blue-500",    badge: "bg-blue-50 text-blue-700" },
  assignment:         { dot: "bg-indigo-500",   badge: "bg-indigo-50 text-indigo-700" },
  amendment:          { dot: "bg-purple-500",  badge: "bg-purple-50 text-purple-700" },
  general:            { dot: "bg-slate-400",   badge: "bg-slate-50 text-slate-600" },
};

export default function SearchPage() {
  const router = useRouter();
  const token = useAuthStore((s) => s.token);
  const hydrated = useHasHydrated();

  /* --- existing state --- */
  const [query, setQuery] = useState("");
  const [activeFilter, setActiveFilter] = useState("all");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [limit, setLimit] = useState(10);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  // Auth guard — wait for hydration
  useEffect(() => {
    if (hydrated && !token) router.replace("/login");
  }, [hydrated, token, router]);

  // Semantic search (when query is present)
  const doSearch = useCallback(
    async (q: string, filter: string, lim: number) => {
      if (!token || !q.trim()) return;
      setLoading(true);
      try {
        const data = await searchApi.clauses(
          q.trim(),
          token,
          filter === "all" ? undefined : filter,
          lim
        );
        setResults(data);
        setSearched(true);
      } catch {
        toast.error("Search failed. Please try again.");
      } finally {
        setLoading(false);
      }
    },
    [token]
  );

  // Browse mode (when no query — just filter by type)
  const doBrowse = useCallback(
    async (filter: string, lim: number) => {
      if (!token) return;
      setLoading(true);
      try {
        const data = await searchApi.browse(
          token,
          filter === "all" ? undefined : filter,
          lim
        );
        setResults(data);
        setSearched(true);
      } catch {
        toast.error("Failed to load clauses.");
      } finally {
        setLoading(false);
      }
    },
    [token]
  );

  // Load clauses on mount (browse mode)
  useEffect(() => {
    if (token && !query.trim()) {
      doBrowse(activeFilter, limit);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  // Debounced search on query change, or browse when query is cleared
  useEffect(() => {
    if (!query.trim()) {
      // Switch to browse mode
      doBrowse(activeFilter, limit);
      return;
    }

    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      doSearch(query, activeFilter, limit);
    }, 400);

    return () => clearTimeout(debounceRef.current);
  }, [query, activeFilter, doSearch, doBrowse, limit]);

  const handleLoadMore = useCallback(() => {
    const newLimit = limit + 10;
    setLimit(newLimit);
    if (query.trim()) {
      doSearch(query, activeFilter, newLimit);
    } else {
      doBrowse(activeFilter, newLimit);
    }
  }, [limit, query, activeFilter, doSearch, doBrowse]);

  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

  return (
    <div className="min-h-screen bg-background dot-bg">
      <Navigation />

      <div className="mx-auto max-w-3xl px-4 py-10 sm:px-6">
        {/* Title — left-aligned, not centered */}
        <div className="mb-6 animate-fade-in">
          <h1 className="text-2xl font-heading font-bold text-foreground">
            Search Clauses
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            200K+ clauses from real contracts
          </p>
        </div>

        {/* Search bar — big, prominent */}
        <div className="relative mb-5 animate-slide-up">
          <div className="relative">
            <SearchIcon className="absolute left-5 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground/70" />
            <input
              type="text"
              value={query}
              onChange={(e) => {
                setQuery(e.target.value);
                setLimit(10);
                setExpandedIndex(null);
              }}
              placeholder='Try "indemnification clause" or "liability cap"...'
              className="w-full rounded-xl border border-border bg-white py-4 pl-14 pr-12 text-base text-foreground shadow-inner-soft placeholder:text-muted-foreground/40 transition-all focus:border-primary focus:ring-2 focus:ring-primary/20 focus:shadow-glow focus:outline-none"
              autoFocus
            />
            {query && (
              <button
                onClick={() => {
                  setQuery("");
                  setResults([]);
                  setSearched(false);
                  setLimit(10);
                  setExpandedIndex(null);
                }}
                className="absolute right-4 top-1/2 -translate-y-1/2 rounded-md p-1.5 text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
              >
                <X className="h-4 w-4" />
              </button>
            )}
          </div>
          {loading && (
            <div className="absolute right-14 top-1/2 -translate-y-1/2">
              <Loader2 className="h-4 w-4 text-primary animate-spin" />
            </div>
          )}
        </div>

        {/* Filter pills with scroll arrows */}
        <div className="relative mb-6 animate-slide-up stagger-1">
          <button
            onClick={() => {
              const el = document.getElementById('filter-scroll');
              if (el) el.scrollBy({ left: -200, behavior: 'smooth' });
            }}
            className="absolute left-0 top-1/2 -translate-y-1/2 z-10 flex h-7 w-7 items-center justify-center rounded-full bg-card border border-border shadow-sm hover:shadow-md transition-all -ml-1"
            aria-label="Scroll filters left"
          >
            <ChevronLeft className="h-3.5 w-3.5 text-muted-foreground" />
          </button>

          <div
            id="filter-scroll"
            className="flex gap-1.5 overflow-x-auto no-scrollbar px-8 pb-2"
          >
            {CLAUSE_TYPES.map((type) => (
              <button
                key={type}
                onClick={() => {
                  setActiveFilter(type);
                  setLimit(10);
                  setExpandedIndex(null);
                }}
                className={cn(
                  "shrink-0 rounded-lg px-3.5 py-1.5 text-xs font-medium transition-all duration-150",
                  activeFilter === type
                    ? "bg-foreground text-background shadow-sm"
                    : "bg-card text-muted-foreground border border-border hover:text-foreground hover:border-foreground/20"
                )}
              >
                {type === "all" ? "All Types" : clauseTypeLabel(type)}
              </button>
            ))}
          </div>

          <button
            onClick={() => {
              const el = document.getElementById('filter-scroll');
              if (el) el.scrollBy({ left: 200, behavior: 'smooth' });
            }}
            className="absolute right-0 top-1/2 -translate-y-1/2 z-10 flex h-7 w-7 items-center justify-center rounded-full bg-card border border-border shadow-sm hover:shadow-md transition-all -mr-1"
            aria-label="Scroll filters right"
          >
            <ChevronRight className="h-3.5 w-3.5 text-muted-foreground" />
          </button>
        </div>

        {/* Results */}
        <div className="space-y-3">
          {results.map((result, i) => {
            const isExpanded = expandedIndex === i;
            const isLong = result.text.length > 400;
            const style = CLAUSE_TYPE_STYLE[result.clause_type] ?? CLAUSE_TYPE_STYLE.general;

            return (
              <div
                key={i}
                onClick={() => isLong && setExpandedIndex(isExpanded ? null : i)}
                className={cn(
                  "rounded-xl border border-border/60 bg-card p-5 shadow-card transition-all animate-fade-in hover:shadow-card-hover",
                  isLong && "cursor-pointer"
                )}
                style={{ animationDelay: `${i * 30}ms` }}
              >
                <div className="flex items-center gap-2.5 mb-3">
                  <span className={cn("h-2 w-2 rounded-full shrink-0", style.dot)} />
                  <span className={cn("inline-flex items-center rounded-md px-2 py-0.5 text-[11px] font-semibold", style.badge)}>
                    {clauseTypeLabel(result.clause_type)}
                  </span>
                  <span className="text-[11px] text-muted-foreground">
                    {result.contract_type}
                  </span>
                  {query.trim() && (
                    <span className="text-[11px] text-muted-foreground tabular-nums ml-auto font-medium bg-muted rounded-md px-1.5 py-0.5">
                      {(result.score * 100).toFixed(0)}%
                    </span>
                  )}
                </div>
                <p className="text-sm text-foreground/80 leading-relaxed">
                  {isExpanded || !isLong
                    ? result.text
                    : result.text.slice(0, 400) + "..."}
                </p>
                {isLong && (
                  <button
                    className="mt-2.5 text-xs font-medium text-primary hover:text-primary/80 transition-colors"
                    onClick={(e) => {
                      e.stopPropagation();
                      setExpandedIndex(isExpanded ? null : i);
                    }}
                  >
                    {isExpanded ? "Show less" : "Read full clause"}
                  </button>
                )}
              </div>
            );
          })}

          {/* Load more */}
          {results.length >= limit && results.length > 0 && (
            <div className="text-center pt-6">
              <button
                onClick={handleLoadMore}
                disabled={loading}
                className="inline-flex items-center gap-2 rounded-lg border border-border bg-card px-5 py-2.5 text-sm font-medium text-foreground transition-all hover:shadow-card-hover hover:border-primary/30 active:scale-[0.98] disabled:opacity-50"
              >
                {loading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  "Load More Results"
                )}
              </button>
            </div>
          )}

          {/* Empty state */}
          {searched && results.length === 0 && !loading && (
            <div className="text-center py-16 animate-fade-in">
              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-muted mb-4">
                <SearchIcon className="h-6 w-6 text-muted-foreground" />
              </div>
              <p className="text-sm font-medium text-foreground">
                No results found
              </p>
              <p className="text-xs text-muted-foreground mt-1">
                Try different keywords or remove filters
              </p>
            </div>
          )}

          {/* Loading state */}
          {!searched && loading && (
            <div className="text-center py-16 animate-fade-in">
              <Loader2 className="h-8 w-8 text-primary animate-spin mx-auto mb-4" />
              <p className="text-sm font-medium text-foreground">
                Loading clauses...
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

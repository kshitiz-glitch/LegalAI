"use client";

import React, { useState, useCallback } from "react";
import {
  ChevronDown,
  AlertTriangle,
  CheckCircle2,
  Info,
} from "lucide-react";
import {
  cn,
  riskBg,
  riskLabel,
  riskColor,
  clauseTypeLabel,
} from "@/lib/utils";
import type { ClauseAnalysis } from "@/types";

interface ClauseCardProps {
  clause: ClauseAnalysis;
  index: number;
}

export const ClauseCard = React.memo(function ClauseCard({
  clause,
  index,
}: ClauseCardProps) {
  const [expanded, setExpanded] = useState(false);

  const toggle = useCallback(() => setExpanded((p) => !p), []);

  const riskIcon =
    clause.risk_score <= 3 ? (
      <CheckCircle2 className="h-3.5 w-3.5" />
    ) : clause.risk_score <= 6 ? (
      <Info className="h-3.5 w-3.5" />
    ) : (
      <AlertTriangle className="h-3.5 w-3.5" />
    );

  return (
    <div
      className={cn(
        "group rounded-xl border bg-card transition-all duration-200 card-accent",
        clause.risk_score <= 3 ? "card-accent-emerald" :
        clause.risk_score <= 6 ? "card-accent-amber" : "card-accent-red",
        expanded ? "shadow-card-hover" : "shadow-card hover:shadow-card-hover",
        "animate-fade-in"
      )}
      style={{ animationDelay: `${index * 50}ms` }}
    >
      {/* Header — always visible */}
      <button
        onClick={toggle}
        className="flex w-full items-start gap-3 p-4 text-left"
        aria-expanded={expanded}
      >
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 mb-1.5">
            <span className="inline-flex items-center rounded-md bg-muted px-2 py-0.5 text-[11px] font-medium text-muted-foreground">
              {clauseTypeLabel(clause.clause_type)}
            </span>
            <span
              className={cn(
                "inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[11px] font-semibold",
                riskBg(clause.risk_score)
              )}
            >
              {riskIcon}
              {riskLabel(clause.risk_score)} · {clause.risk_score}/10
            </span>
          </div>

          <p className={cn("text-sm text-foreground leading-relaxed", !expanded && "line-clamp-2")}>
            {clause.text}
          </p>
        </div>

        <ChevronDown
          className={cn(
            "h-4 w-4 shrink-0 text-muted-foreground transition-transform duration-200 mt-1",
            expanded && "rotate-180"
          )}
        />
      </button>

      {/* Expanded Content */}
      <div
        className={cn(
          "grid transition-[grid-template-rows] duration-300 ease-out",
          expanded ? "grid-rows-[1fr]" : "grid-rows-[0fr]"
        )}
      >
        <div className="overflow-hidden">
          <div className="border-t border-border/50 px-4 pb-4 pt-3 space-y-4">
            {/* Explanation */}
            <div>
              <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1.5">
                Plain English
              </h4>
              <p className="text-sm text-foreground leading-relaxed">
                {clause.explanation}
              </p>
            </div>

            {/* Issues */}
            {clause.issues && clause.issues.length > 0 && (
              <div>
                <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1.5">
                  Issues Found
                </h4>
                <ul className="space-y-1">
                  {clause.issues.map((issue, i) => (
                    <li
                      key={i}
                      className="flex items-start gap-2 text-sm text-foreground"
                    >
                      <span className={cn("mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full", 
                        clause.risk_score <= 3 ? "bg-emerald-500" : 
                        clause.risk_score <= 6 ? "bg-amber-500" : "bg-red-500"
                      )} />
                      {issue}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Similar Clauses */}
            {clause.similar_clauses && clause.similar_clauses.length > 0 && (
              <div>
                <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
                  Similar Market Clauses
                </h4>
                <div className="space-y-2.5">
                  {clause.similar_clauses.slice(0, 3).map((similar, i) => {
                    const pct = similar.score * 100;
                    const simLabel = pct >= 85 ? "Very Similar" : pct >= 70 ? "Similar" : "Related";
                    const simColor = pct >= 85 ? "text-emerald-600" : pct >= 70 ? "text-primary" : "text-muted-foreground";

                    return (
                      <div
                        key={i}
                        className="rounded-lg border border-border/50 bg-muted/30 p-3.5 text-xs leading-relaxed"
                      >
                        <div className="flex items-center gap-2 mb-2">
                          <span className="font-semibold text-foreground">
                            {clauseTypeLabel(similar.clause_type)}
                          </span>
                          <span className={cn("text-[10px] font-medium px-1.5 py-0.5 rounded-md bg-muted", simColor)}>
                            {simLabel}
                          </span>
                        </div>
                        <p className="text-muted-foreground">{similar.text}</p>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
});

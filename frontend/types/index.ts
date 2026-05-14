export interface User {
  id: number;
  email: string;
  full_name: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user?: User;
}

export interface SimilarClause {
  text: string;
  score: number;
  clause_type: string;
  contract_type: string;
}

export interface ClauseAnalysis {
  text: string;
  clause_type: string;
  risk_score: number;
  risk_level: "Low" | "Medium" | "High" | "Critical";
  issues: string[];
  explanation: string;
  similar_clauses: SimilarClause[];
}

export interface Redline {
  original: string;
  rewritten: string;
  changes: string[];
  rationale: string;
}

export interface NegotiationStrategy {
  priority_issues: string[];
  negotiable_points: string[];
  deal_breakers: string[];
  compromise_positions: Record<string, string>;
  talking_points: string[];
  email_opener: string;
}

export interface Contract {
  id: number;
  filename: string;
  contract_type: string | null;
  status: "pending" | "analyzing" | "complete" | "error";
  overall_risk_score: number | null;
  summary: string | null;
  parties: Record<string, string> | null;
  key_dates: { effective_date: string | null; expiry_date: string | null } | null;
  clauses: ClauseAnalysis[] | null;
  redlines: Redline[] | null;
  negotiation_strategy: NegotiationStrategy | null;
  created_at: string;
}

export interface ContractListItem {
  id: number;
  filename: string;
  contract_type: string | null;
  status: "pending" | "analyzing" | "complete" | "error";
  overall_risk_score: number | null;
  created_at: string;
}

export interface SearchResult {
  text: string;
  clause_type: string;
  contract_type: string;
  score: number;
}

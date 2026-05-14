import type {
  User,
  TokenResponse,
  Contract,
  ContractListItem,
  SearchResult,
} from "@/types";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function request<T>(
  path: string,
  options: RequestInit = {},
  token?: string
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (options.body instanceof FormData) delete headers["Content-Type"];

  const res = await fetch(`${BASE}${path}`, { ...options, headers });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? "Request failed");
  }
  return res.json() as Promise<T>;
}

// Auth
export const authApi = {
  register: (email: string, password: string, full_name: string) =>
    request<TokenResponse>("/api/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, full_name }),
    }),

  login: (email: string, password: string) =>
    request<TokenResponse>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  me: (token: string) =>
    request<User>("/api/auth/me", {}, token),
};

// Contracts
export const contractsApi = {
  upload: (file: File, token: string) => {
    const form = new FormData();
    form.append("file", file);
    return request<Contract>("/api/contracts/upload", {
      method: "POST",
      body: form,
    }, token);
  },

  list: (token: string) =>
    request<ContractListItem[]>("/api/contracts/", {}, token),

  get: (id: number, token: string) =>
    request<Contract>(`/api/contracts/${id}`, {}, token),

  delete: (id: number, token: string) =>
    request<{ detail: string }>(`/api/contracts/${id}`, { method: "DELETE" }, token),
};

// Search
export const searchApi = {
  clauses: (query: string, token: string, clause_type?: string, limit = 10) =>
    request<SearchResult[]>("/api/search/clauses", {
      method: "POST",
      body: JSON.stringify({ query, clause_type, limit }),
    }, token),

  browse: (token: string, clause_type?: string, limit = 10) => {
    const params = new URLSearchParams({ limit: String(limit) });
    if (clause_type && clause_type !== "all") params.set("clause_type", clause_type);
    return request<SearchResult[]>(`/api/search/browse?${params}`, {}, token);
  },
};

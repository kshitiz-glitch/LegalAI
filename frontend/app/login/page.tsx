"use client";

import React, { useState, useCallback, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Scale, ArrowRight, Loader2, Eye, EyeOff, Shield, FileText, TrendingUp } from "lucide-react";
import { authApi } from "@/lib/api";
import { useAuthStore } from "@/lib/store";

export default function LoginPage() {
  const router = useRouter();
  const { setAuth } = useAuthStore();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Prefetch dashboard so it loads instantly after login
  useEffect(() => { router.prefetch("/dashboard"); }, [router]);

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      setLoading(true);
      setError("");
      try {
        const { access_token, user } = await authApi.login(email, password);
        if (!user) throw new Error("Login failed — no user data");
        setAuth(access_token, user);
        router.replace("/dashboard");
      } catch (err) {
        setError(err instanceof Error ? err.message : "Login failed");
      } finally {
        setLoading(false);
      }
    },
    [email, password, setAuth, router]
  );

  return (
    <div className="flex min-h-screen">
      {/* ── Left Panel — Brand ──────────────────────────────────── */}
      <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden bg-[hsl(220,25%,12%)]">
        {/* Mesh gradient overlay */}
        <div className="absolute inset-0 mesh-gradient opacity-60" />
        <div
          className="absolute inset-0 opacity-[0.03]"
          style={{
            backgroundImage: "radial-gradient(circle at 1px 1px, white 1px, transparent 0)",
            backgroundSize: "32px 32px",
          }}
        />

        <div className="relative flex flex-col justify-between p-12 xl:p-16 w-full">
          {/* Logo */}
          <Link href="/" className="inline-flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary text-white">
              <Scale className="h-4.5 w-4.5" />
            </div>
            <span className="text-xl font-heading font-bold tracking-tight text-white">
              Legal<span className="text-primary">AI</span>
            </span>
          </Link>

          {/* Tagline */}
          <div className="space-y-6">
            <h1 className="text-4xl xl:text-5xl font-heading font-bold text-white leading-[1.1]">
              Contract intelligence,<br />
              <span className="text-primary">not guesswork.</span>
            </h1>
            <p className="text-base text-white/50 max-w-md leading-relaxed">
              AI-powered contract analysis that identifies risks, suggests redlines,
              and gives you negotiation leverage — in seconds, not hours.
            </p>
          </div>

          {/* Stats strip */}
          <div className="flex gap-8">
            {[
              { icon: FileText, stat: "200K+", label: "Clauses indexed" },
              { icon: Shield, stat: "98%", label: "Risk accuracy" },
              { icon: TrendingUp, stat: "60s", label: "Analysis time" },
            ].map(({ icon: Icon, stat, label }) => (
              <div key={label} className="flex items-center gap-3">
                <div className="flex h-8 w-8 items-center justify-center rounded-md bg-white/[0.06]">
                  <Icon className="h-3.5 w-3.5 text-primary" />
                </div>
                <div>
                  <p className="text-sm font-bold text-white tabular-nums">{stat}</p>
                  <p className="text-[11px] text-white/40">{label}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── Right Panel — Form ──────────────────────────────────── */}
      <div className="flex w-full lg:w-1/2 flex-col items-center justify-center px-6 py-12 bg-background">
        {/* Mobile logo */}
        <div className="lg:hidden mb-10">
          <Link href="/" className="inline-flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary text-white">
              <Scale className="h-4.5 w-4.5" />
            </div>
            <span className="text-xl font-heading font-bold tracking-tight text-foreground">
              Legal<span className="text-primary">AI</span>
            </span>
          </Link>
        </div>

        <div className="w-full max-w-sm animate-fade-in">
          <div className="mb-8">
            <h2 className="text-2xl font-heading font-bold text-foreground">
              Welcome back
            </h2>
            <p className="mt-2 text-sm text-muted-foreground">
              Sign in to continue to your dashboard
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            {error && (
              <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700 animate-scale-in">
                {error}
              </div>
            )}

            <div>
              <label
                htmlFor="email"
                className="block text-sm font-medium text-foreground mb-1.5"
              >
                Email
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoComplete="email"
                className="w-full rounded-lg border border-border bg-white px-3.5 py-2.5 text-sm text-foreground shadow-inner-soft placeholder:text-muted-foreground/50 transition-colors focus:border-primary focus:ring-2 focus:ring-primary/20 focus:outline-none"
                placeholder="you@company.com"
              />
            </div>

            <div>
              <label
                htmlFor="password"
                className="block text-sm font-medium text-foreground mb-1.5"
              >
                Password
              </label>
              <div className="relative">
                <input
                  id="password"
                  type={showPw ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  autoComplete="current-password"
                  className="w-full rounded-lg border border-border bg-white px-3.5 py-2.5 pr-10 text-sm text-foreground shadow-inner-soft placeholder:text-muted-foreground/50 transition-colors focus:border-primary focus:ring-2 focus:ring-primary/20 focus:outline-none"
                  placeholder="••••••••"
                />
                <button
                  type="button"
                  onClick={() => setShowPw(!showPw)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                  tabIndex={-1}
                >
                  {showPw ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-lg bg-primary py-2.5 text-sm font-semibold text-white transition-all hover:bg-primary/90 hover:shadow-button-hover active:scale-[0.98] disabled:opacity-60 disabled:pointer-events-none flex items-center justify-center gap-2"
            >
              {loading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <>
                  Sign in
                  <ArrowRight className="h-4 w-4" />
                </>
              )}
            </button>
          </form>

          <p className="mt-8 text-center text-sm text-muted-foreground">
            Don&apos;t have an account?{" "}
            <Link
              href="/register"
              className="font-medium text-primary hover:text-primary/80 transition-colors"
            >
              Create one
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}

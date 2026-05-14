import Link from "next/link";
import {
  Shield,
  Zap,
  Search,
  ArrowRight,
  Upload,
  BarChart3,
  FileCheck,
  Scale,
  Check,
  Star,
} from "lucide-react";

/* ── Pure Server Component — 0 bytes of client JS ────────────────────────── */

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-background">
      {/* ── Navigation ─────────────────────────────────────────────────── */}
      <header className="sticky top-0 z-50 border-b border-border/50 bg-background/80 backdrop-blur-lg">
        <nav className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
          <Link href="/" className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-white">
              <Scale className="h-4 w-4" />
            </div>
            <span className="text-lg font-heading font-bold tracking-tight text-foreground">
              Legal<span className="text-primary">AI</span>
            </span>
          </Link>
          <div className="flex items-center gap-3">
            <Link
              href="/login"
              className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
            >
              Sign in
            </Link>
            <Link
              href="/register"
              className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white transition-all hover:bg-primary/90 hover:shadow-button-hover active:scale-[0.98]"
            >
              Get Started
            </Link>
          </div>
        </nav>
      </header>

      {/* ── Hero Section ───────────────────────────────────────────────── */}
      <section className="relative overflow-hidden">
        {/* Grid background */}
        <div className="absolute inset-0 grid-bg radial-fade" aria-hidden="true" />
        {/* Gradient orb */}
        <div
          className="absolute top-[-120px] left-1/2 -translate-x-1/2 h-[500px] w-[700px] rounded-full opacity-15 blur-3xl"
          style={{
            background:
              "radial-gradient(circle, hsl(172 66% 40%) 0%, hsl(38 92% 50%) 50%, transparent 80%)",
          }}
          aria-hidden="true"
        />

        <div className="relative mx-auto max-w-4xl px-4 pt-24 pb-20 sm:pt-32 sm:pb-28">
          <div className="max-w-2xl animate-fade-in">
            <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-border bg-card px-4 py-1.5 text-sm text-muted-foreground shadow-sm">
              <Star className="h-3.5 w-3.5 text-amber-400 fill-amber-400" />
              <span>AI-powered contract analysis</span>
            </div>

          <h1 className="text-4xl font-heading font-bold tracking-tight text-foreground sm:text-5xl lg:text-6xl animate-slide-up">
            Understand any contract
            <br />
            <span className="gradient-text">in seconds, not hours</span>
          </h1>

          <p className="mt-6 max-w-xl text-lg text-muted-foreground leading-relaxed animate-slide-up stagger-2">
            Upload your contracts and get instant AI analysis. Identify risks,
            review clauses, and generate redline suggestions — all powered by
            advanced language models.
          </p>

          <div className="mt-10 flex flex-col sm:flex-row items-start gap-4 animate-slide-up stagger-3">
            <Link
              href="/register"
              className="inline-flex items-center gap-2 rounded-xl bg-primary px-6 py-3.5 text-sm font-semibold text-white shadow-lg shadow-primary/20 transition-all hover:shadow-xl hover:shadow-primary/25 hover:bg-primary/90 active:scale-[0.98]"
            >
              <Upload className="h-4 w-4" />
              Upload Contract
              <ArrowRight className="h-4 w-4" />
            </Link>
            <Link
              href="/login"
              className="inline-flex items-center gap-2 rounded-xl border border-border bg-card px-6 py-3.5 text-sm font-semibold text-foreground shadow-sm transition-all hover:shadow-md hover:border-border/80 active:scale-[0.98]"
            >
              Sign in to Dashboard
            </Link>
          </div>
          </div>
        </div>
      </section>

      {/* ── Features Grid ──────────────────────────────────────────────── */}
      <section className="mx-auto max-w-6xl px-4 pb-24 sm:px-6">
        <div className="text-center mb-14">
          <h2 className="text-2xl font-heading font-bold text-foreground sm:text-3xl">
            Everything you need to review contracts
          </h2>
          <p className="mt-3 text-muted-foreground max-w-xl mx-auto">
            Built for legal professionals, startups, and anyone who signs contracts.
          </p>
        </div>

        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map(({ icon: Icon, title, description, color }, i) => (
            <div
              key={title}
              className="group rounded-2xl border border-border bg-card p-6 transition-all hover-lift"
            >
              <div
                className={`flex h-11 w-11 items-center justify-center rounded-xl ${color} mb-4`}
              >
                <Icon className="h-5 w-5" />
              </div>
              <h3 className="text-base font-heading font-semibold text-foreground mb-1.5">
                {title}
              </h3>
              <p className="text-sm text-muted-foreground leading-relaxed">
                {description}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* ── How It Works ───────────────────────────────────────────────── */}
      <section className="border-y border-border/50 bg-muted/30">
        <div className="mx-auto max-w-5xl px-4 py-24 sm:px-6">
          <div className="text-center mb-14">
            <h2 className="text-2xl font-bold text-foreground sm:text-3xl">
              Three steps to safer contracts
            </h2>
          </div>

          <div className="grid gap-8 sm:grid-cols-3">
            {STEPS.map(({ icon: Icon, step, title, description }, i) => (
              <div key={step} className="relative text-center">
                <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-white border border-border shadow-card">
                  <Icon className="h-6 w-6 text-primary" />
                </div>
                <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-primary text-xs font-bold text-white mb-2">
                  {step}
                </span>
                <h3 className="text-base font-semibold text-foreground mb-1">
                  {title}
                </h3>
                <p className="text-sm text-muted-foreground">{description}</p>

                {/* Connector line (desktop only) */}
                {i < 2 && (
                  <div
                    className="hidden sm:block absolute top-7 left-[calc(50%+40px)] w-[calc(100%-80px)] border-t-2 border-dashed border-border"
                    aria-hidden="true"
                  />
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Pricing ────────────────────────────────────────────────────── */}
      <section className="mx-auto max-w-5xl px-4 py-24 sm:px-6">
        <div className="text-center mb-14">
          <h2 className="text-2xl font-bold text-foreground sm:text-3xl">
            Simple, transparent pricing
          </h2>
          <p className="mt-3 text-muted-foreground">
            Start free. Upgrade when you need more.
          </p>
        </div>

        <div className="grid gap-6 sm:grid-cols-3">
          {PLANS.map(({ name, price, period, features, highlight, cta }) => (
            <div
              key={name}
              className={`relative rounded-2xl border p-6 ${
                highlight
                  ? "border-primary shadow-glow bg-white"
                  : "border-border bg-card"
              }`}
            >
              {highlight && (
                <span className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-primary px-3 py-0.5 text-xs font-semibold text-white">
                  Most Popular
                </span>
              )}
              <h3 className="text-lg font-semibold text-foreground">{name}</h3>
              <div className="mt-3 mb-6">
                <span className="text-3xl font-bold text-foreground">
                  {price}
                </span>
                {period && (
                  <span className="text-sm text-muted-foreground ml-1">
                    /{period}
                  </span>
                )}
              </div>
              <ul className="space-y-2.5 mb-6">
                {features.map((f) => (
                  <li
                    key={f}
                    className="flex items-start gap-2.5 text-sm text-muted-foreground"
                  >
                    <Check className="h-4 w-4 shrink-0 text-primary mt-0.5" />
                    {f}
                  </li>
                ))}
              </ul>
              <Link
                href="/register"
                className={`block w-full rounded-lg py-2.5 text-center text-sm font-semibold transition-all active:scale-[0.98] ${
                  highlight
                    ? "bg-primary text-white hover:bg-primary/90 hover:shadow-button-hover"
                    : "bg-muted text-foreground hover:bg-muted/80"
                }`}
              >
                {cta}
              </Link>
            </div>
          ))}
        </div>
      </section>

      {/* ── Footer ─────────────────────────────────────────────────────── */}
      <footer className="border-t border-border/50 bg-muted/20">
        <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <div className="flex h-6 w-6 items-center justify-center rounded-md bg-primary text-white">
                <Scale className="h-3 w-3" />
              </div>
              <span className="text-sm font-medium text-muted-foreground">
                LegalAI
              </span>
            </div>
            <p className="text-xs text-muted-foreground">
              © {new Date().getFullYear()} LegalAI. Not legal advice.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}

/* ── Static data (no runtime cost) ──────────────────────────────────────── */

const FEATURES = [
  {
    icon: Shield,
    title: "Risk Assessment",
    description:
      "AI analyzes every clause and assigns a risk score. Get instant visibility into potential issues before you sign.",
    color: "bg-red-50 text-red-600",
  },
  {
    icon: Zap,
    title: "Instant Analysis",
    description:
      "Upload a PDF and get results in under 60 seconds. Our AI reads, classifies, and evaluates clauses automatically.",
    color: "bg-amber-50 text-amber-600",
  },
  {
    icon: Search,
    title: "Clause Search",
    description:
      "Search across 200K+ legal clauses from real contracts. Find precedent and compare language instantly.",
    color: "bg-blue-50 text-blue-600",
  },
  {
    icon: FileCheck,
    title: "Redline Suggestions",
    description:
      "Get AI-generated alternative language for risky clauses, with clear rationale for each suggested change.",
    color: "bg-emerald-50 text-emerald-600",
  },
  {
    icon: BarChart3,
    title: "Negotiation Strategy",
    description:
      "AI generates priority issues, deal-breakers, compromise positions, and even email openers for negotiations.",
    color: "bg-purple-50 text-purple-600",
  },
  {
    icon: Scale,
    title: "Legal Intelligence",
    description:
      "Powered by Llama 3.3 70B and trained on real legal datasets. Smart enough to catch what you might miss.",
    color: "bg-indigo-50 text-indigo-600",
  },
] as const;

const STEPS = [
  {
    icon: Upload,
    step: "1",
    title: "Upload Contract",
    description: "Drop a PDF and our AI starts analyzing immediately.",
  },
  {
    icon: BarChart3,
    step: "2",
    title: "AI Analyzes",
    description: "Every clause is classified, scored, and explained in plain English.",
  },
  {
    icon: FileCheck,
    step: "3",
    title: "Review & Act",
    description: "Get redline suggestions, negotiation strategies, and export your report.",
  },
] as const;

const PLANS = [
  {
    name: "Free",
    price: "$0",
    period: null,
    highlight: false,
    cta: "Get Started",
    features: [
      "3 contract analyses/month",
      "Basic risk scoring",
      "Clause search (100 queries)",
      "PDF upload up to 5MB",
    ],
  },
  {
    name: "Pro",
    price: "$29",
    period: "month",
    highlight: true,
    cta: "Start Free Trial",
    features: [
      "Unlimited analyses",
      "Advanced risk assessment",
      "Redline suggestions",
      "Negotiation strategies",
      "Priority support",
    ],
  },
  {
    name: "Team",
    price: "$79",
    period: "month",
    highlight: false,
    cta: "Contact Sales",
    features: [
      "Everything in Pro",
      "5 team members",
      "Shared contract library",
      "API access",
      "Custom integrations",
    ],
  },
] as const;

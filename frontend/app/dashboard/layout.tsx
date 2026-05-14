"use client";

import React, { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Navigation } from "@/components/shared/Navigation";
import { useAuthStore, useHasHydrated } from "@/lib/store";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const hydrated = useHasHydrated();
  const token = useAuthStore((s) => s.token);

  useEffect(() => {
    if (hydrated && !token) {
      router.replace("/login");
    }
  }, [hydrated, token, router]);

  if (!hydrated) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
      </div>
    );
  }

  if (!token) return null;

  return (
    <div className="min-h-screen bg-muted/20 dot-bg">
      <Navigation />
      <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        {children}
      </main>
    </div>
  );
}

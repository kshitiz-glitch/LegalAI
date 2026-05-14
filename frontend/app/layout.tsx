import type { Metadata } from "next";
import { DM_Sans, Inter } from "next/font/google";
import { Toaster } from "sonner";
import "./globals.css";

const dmSans = DM_Sans({
  subsets: ["latin"],
  variable: "--font-heading",
  display: "swap",
  weight: ["500", "600", "700"],
});

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: "LegalAI — AI-Powered Contract Analysis",
  description:
    "Upload contracts and get instant AI analysis. Identify risks, review clauses, and generate redline suggestions in seconds.",
  keywords: ["contract analysis", "AI legal", "risk assessment", "clause review"],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${dmSans.variable} ${inter.variable}`}>
      <body className="min-h-screen bg-background antialiased">
        {children}
        <Toaster
          position="bottom-right"
          toastOptions={{
            className: "font-sans",
            style: {
              background: "hsl(40 33% 98%)",
              border: "1px solid hsl(36 16% 88%)",
              color: "hsl(220 25% 12%)",
            },
          }}
        />
      </body>
    </html>
  );
}

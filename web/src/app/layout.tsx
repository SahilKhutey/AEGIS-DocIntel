import type { Metadata } from "next";
import { Suspense } from "react";
import "./globals.css";
import { AppShell } from "@/components/app-shell";

export const metadata: Metadata = {
  title: "AEGIS-DocIntel — Document Intelligence Workbench",
  description: "Enterprise Document Intelligence, Evidence Explorer & Governance Review Workbench",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full flex flex-col bg-gray-50 text-gray-900">
        <Suspense fallback={<div className="min-h-screen bg-gray-50 p-4 flex items-center justify-center text-sm text-gray-500">Loading AEGIS Workbench...</div>}>
          <AppShell>{children}</AppShell>
        </Suspense>
      </body>
    </html>
  );
}

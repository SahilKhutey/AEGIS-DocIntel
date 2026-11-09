import type { Metadata } from "next";
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
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}

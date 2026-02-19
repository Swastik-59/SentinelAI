import type { Metadata } from "next";
import "./globals.css";
import { Sidebar } from "@/components/Sidebar";

export const metadata: Metadata = {
  title: "SentinelAI — AI Fraud Detection for Banking",
  description:
    "Enterprise-grade AI-generated fraud detection platform for banking communications, documents, and images.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-[#0a0e1a] antialiased flex">
        <Sidebar />
        <main className="flex-1 ml-16">{children}</main>
      </body>
    </html>
  );
}

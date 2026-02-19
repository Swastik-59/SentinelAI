"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import {
  getCases,
  updateCaseStatus,
  type Case,
  type CaseStatus,
  type RiskLevel,
} from "@/lib/api";

/* ── Status column config ──────────────────────────────────────────── */
const COLUMNS: { status: CaseStatus; label: string; color: string; bg: string }[] = [
  { status: "OPEN", label: "Open", color: "text-blue-400", bg: "bg-blue-500/10 border-blue-500/20" },
  { status: "UNDER_REVIEW", label: "Under Review", color: "text-yellow-400", bg: "bg-yellow-500/10 border-yellow-500/20" },
  { status: "ESCALATED", label: "Escalated", color: "text-red-400", bg: "bg-red-500/10 border-red-500/20" },
  { status: "RESOLVED", label: "Resolved", color: "text-emerald-400", bg: "bg-emerald-500/10 border-emerald-500/20" },
  { status: "FALSE_POSITIVE", label: "False Positive", color: "text-slate-400", bg: "bg-slate-500/10 border-slate-500/20" },
];

const RISK_COLORS: Record<RiskLevel, string> = {
  LOW: "bg-emerald-500/20 text-emerald-300 border-emerald-500/30",
  MEDIUM: "bg-yellow-500/20 text-yellow-300 border-yellow-500/30",
  HIGH: "bg-orange-500/20 text-orange-300 border-orange-500/30",
  CRITICAL: "bg-red-500/20 text-red-300 border-red-500/30",
};

/* ── Case Card ─────────────────────────────────────────────────────── */
function CaseCard({ c, onMove }: { c: Case; onMove: (id: string, to: CaseStatus) => void }) {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <div className="glass-card p-4 group hover:border-white/10 transition-all">
      <div className="flex items-start justify-between mb-2">
        <Link
          href={`/cases/${c.id}`}
          className="text-sm font-mono text-sentinel-400 hover:text-sentinel-300 transition"
        >
          {c.id.slice(0, 8)}…
        </Link>
        <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${RISK_COLORS[c.risk_level]}`}>
          {c.risk_level}
        </span>
      </div>

      <div className="space-y-1.5 mb-3">
        <div className="flex justify-between text-xs">
          <span className="text-slate-500">Risk Score</span>
          <span className="text-slate-300 font-medium">{(c.risk_score * 100).toFixed(0)}%</span>
        </div>
        <div className="flex justify-between text-xs">
          <span className="text-slate-500">AI Prob</span>
          <span className="text-slate-300">{(c.ai_probability * 100).toFixed(0)}%</span>
        </div>
        <div className="flex justify-between text-xs">
          <span className="text-slate-500">Fraud Prob</span>
          <span className="text-slate-300">{(c.fraud_probability * 100).toFixed(0)}%</span>
        </div>
      </div>

      {c.escalation_reason && (
        <p className="text-[11px] text-orange-300/80 bg-orange-500/10 rounded px-2 py-1 mb-2 line-clamp-2">
          {c.escalation_reason}
        </p>
      )}

      <div className="flex items-center justify-between text-[11px] text-slate-500">
        <span>{new Date(c.created_at).toLocaleDateString()}</span>
        <div className="relative">
          <button
            onClick={() => setMenuOpen(!menuOpen)}
            className="text-slate-500 hover:text-white transition px-1"
          >
            ⋯
          </button>
          {menuOpen && (
            <div className="absolute right-0 bottom-6 z-20 glass-card border border-white/10 rounded-lg py-1 min-w-[140px] shadow-2xl">
              {COLUMNS.filter((col) => col.status !== c.status).map((col) => (
                <button
                  key={col.status}
                  onClick={() => { onMove(c.id, col.status); setMenuOpen(false); }}
                  className={`block w-full text-left px-3 py-1.5 text-xs hover:bg-white/5 ${col.color}`}
                >
                  → {col.label}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

/* ── Main Page ─────────────────────────────────────────────────────── */
export default function CasesPage() {
  const [cases, setCases] = useState<Case[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<"kanban" | "table">("kanban");

  const fetchCases = useCallback(async () => {
    try {
      const data = await getCases({ limit: 200 });
      setCases(data.cases);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load cases");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchCases(); }, [fetchCases]);

  const handleMove = async (caseId: string, newStatus: CaseStatus) => {
    try {
      await updateCaseStatus(caseId, newStatus);
      setCases((prev) =>
        prev.map((c) => (c.id === caseId ? { ...c, status: newStatus } : c)),
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update");
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0a0e1a] flex items-center justify-center">
        <div className="animate-spin h-8 w-8 border-2 border-sentinel-500 border-t-transparent rounded-full" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0a0e1a] p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white">Investigation Cases</h1>
          <p className="text-sm text-slate-400 mt-1">
            {cases.length} cases • {cases.filter((c) => c.status === "ESCALATED").length} escalated
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex rounded-lg overflow-hidden border border-white/10">
            <button
              onClick={() => setViewMode("kanban")}
              className={`px-3 py-1.5 text-xs font-medium transition ${
                viewMode === "kanban" ? "bg-sentinel-600 text-white" : "text-slate-400 hover:text-white"
              }`}
            >
              Kanban
            </button>
            <button
              onClick={() => setViewMode("table")}
              className={`px-3 py-1.5 text-xs font-medium transition ${
                viewMode === "table" ? "bg-sentinel-600 text-white" : "text-slate-400 hover:text-white"
              }`}
            >
              Table
            </button>
          </div>
          <Link href="/dashboard" className="text-sm text-sentinel-400 hover:text-sentinel-300 transition">
            ← Dashboard
          </Link>
        </div>
      </div>

      {error && (
        <div className="mb-6 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-300 text-sm">
          {error}
        </div>
      )}

      {viewMode === "kanban" ? (
        /* ── Kanban View ──────────────────────────────────────────── */
        <div className="grid grid-cols-5 gap-4">
          {COLUMNS.map((col) => {
            const colCases = cases.filter((c) => c.status === col.status);
            return (
              <div key={col.status} className="space-y-3">
                <div className={`flex items-center gap-2 px-3 py-2 rounded-lg border ${col.bg}`}>
                  <span className={`text-sm font-semibold ${col.color}`}>{col.label}</span>
                  <span className="text-xs text-slate-500 ml-auto">{colCases.length}</span>
                </div>
                <div className="space-y-2">
                  {colCases.map((c) => (
                    <CaseCard key={c.id} c={c} onMove={handleMove} />
                  ))}
                  {colCases.length === 0 && (
                    <div className="text-center py-8 text-xs text-slate-600">No cases</div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        /* ── Table View ───────────────────────────────────────────── */
        <div className="glass-card overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-white/5 text-left text-xs text-slate-500">
                <th className="p-3">Case ID</th>
                <th className="p-3">Risk Level</th>
                <th className="p-3">Risk Score</th>
                <th className="p-3">Status</th>
                <th className="p-3">Assigned</th>
                <th className="p-3">Created</th>
              </tr>
            </thead>
            <tbody>
              {cases.map((c) => (
                <tr key={c.id} className="border-b border-white/5 hover:bg-white/[0.02] transition">
                  <td className="p-3">
                    <Link href={`/cases/${c.id}`} className="text-sentinel-400 hover:text-sentinel-300 font-mono text-xs">
                      {c.id.slice(0, 12)}…
                    </Link>
                  </td>
                  <td className="p-3">
                    <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${RISK_COLORS[c.risk_level]}`}>
                      {c.risk_level}
                    </span>
                  </td>
                  <td className="p-3 text-slate-300">{(c.risk_score * 100).toFixed(0)}%</td>
                  <td className="p-3">
                    <span className={COLUMNS.find((col) => col.status === c.status)?.color}>
                      {COLUMNS.find((col) => col.status === c.status)?.label || c.status}
                    </span>
                  </td>
                  <td className="p-3 text-slate-400">{c.assigned_to || "—"}</td>
                  <td className="p-3 text-slate-500 text-xs">{new Date(c.created_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {cases.length === 0 && (
            <div className="text-center py-12 text-slate-500">No cases yet. Analyze content to auto-generate cases.</div>
          )}
        </div>
      )}
    </div>
  );
}

"use client";

import { useState, useEffect, useCallback } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  getCase,
  updateCaseStatus,
  addCaseNote,
  getCaseExportUrl,
  type Case,
  type CaseStatus,
} from "@/lib/api";

const STATUS_OPTIONS: { value: CaseStatus; label: string; color: string }[] = [
  { value: "OPEN", label: "Open", color: "bg-blue-500" },
  { value: "UNDER_REVIEW", label: "Under Review", color: "bg-yellow-500" },
  { value: "ESCALATED", label: "Escalated", color: "bg-red-500" },
  { value: "RESOLVED", label: "Resolved", color: "bg-emerald-500" },
  { value: "FALSE_POSITIVE", label: "False Positive", color: "bg-slate-500" },
];

const RISK_STYLES: Record<string, string> = {
  LOW: "bg-emerald-500/20 text-emerald-300 border-emerald-500/30",
  MEDIUM: "bg-yellow-500/20 text-yellow-300 border-yellow-500/30",
  HIGH: "bg-orange-500/20 text-orange-300 border-orange-500/30",
  CRITICAL: "bg-red-500/20 text-red-300 border-red-500/30",
};

export default function CaseDetailPage() {
  const params = useParams();
  const caseId = params.id as string;

  const [caseData, setCaseData] = useState<Case | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [noteText, setNoteText] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [assignTo, setAssignTo] = useState("");

  const fetchCase = useCallback(async () => {
    try {
      const data = await getCase(caseId);
      setCaseData(data);
      setAssignTo(data.assigned_to || "");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load case");
    } finally {
      setLoading(false);
    }
  }, [caseId]);

  useEffect(() => { fetchCase(); }, [fetchCase]);

  const handleStatusChange = async (newStatus: CaseStatus) => {
    if (!caseData) return;
    try {
      const updated = await updateCaseStatus(caseData.id, newStatus, assignTo || undefined);
      setCaseData(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update status");
    }
  };

  const handleAddNote = async () => {
    if (!caseData || !noteText.trim()) return;
    setSubmitting(true);
    try {
      await addCaseNote(caseData.id, noteText.trim());
      setNoteText("");
      await fetchCase();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add note");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0a0e1a] flex items-center justify-center">
        <div className="animate-spin h-8 w-8 border-2 border-sentinel-500 border-t-transparent rounded-full" />
      </div>
    );
  }

  if (error || !caseData) {
    return (
      <div className="min-h-screen bg-[#0a0e1a] flex items-center justify-center">
        <div className="glass-card p-6 max-w-md text-center">
          <p className="text-red-400 mb-4">{error || "Case not found"}</p>
          <Link href="/cases" className="text-sentinel-400 hover:text-sentinel-300 text-sm">
            ← Back to Cases
          </Link>
        </div>
      </div>
    );
  }

  const c = caseData;

  return (
    <div className="min-h-screen bg-[#0a0e1a] p-6 max-w-6xl mx-auto">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm text-slate-500 mb-6">
        <Link href="/cases" className="hover:text-sentinel-400 transition">Cases</Link>
        <span>/</span>
        <span className="text-slate-300 font-mono">{c.id.slice(0, 12)}</span>
      </div>

      {/* Header */}
      <div className="flex items-start justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-3">
            Case Investigation
            <span className={`text-xs font-semibold px-2.5 py-1 rounded-full border ${RISK_STYLES[c.risk_level] || ""}`}>
              {c.risk_level}
            </span>
          </h1>
          <p className="text-sm text-slate-500 font-mono mt-1">{c.id}</p>
        </div>
        <a
          href={getCaseExportUrl(c.id)}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-2 px-4 py-2 bg-sentinel-600 hover:bg-sentinel-500 text-white text-sm rounded-lg transition"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          Export PDF
        </a>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Left Column — Details */}
        <div className="col-span-2 space-y-6">
          {/* Score Cards */}
          <div className="grid grid-cols-3 gap-4">
            {[
              { label: "Risk Score", value: c.risk_score, color: "sentinel" },
              { label: "AI Probability", value: c.ai_probability, color: "indigo" },
              { label: "Fraud Probability", value: c.fraud_probability, color: "rose" },
            ].map((metric) => (
              <div key={metric.label} className="glass-card p-4">
                <p className="text-xs text-slate-500 mb-1">{metric.label}</p>
                <p className="text-2xl font-bold text-white">
                  {(metric.value * 100).toFixed(1)}
                  <span className="text-sm text-slate-500">%</span>
                </p>
                <div className="mt-2 h-1.5 rounded-full bg-slate-800">
                  <div
                    className={`h-full rounded-full transition-all ${
                      metric.color === "sentinel" ? "bg-sentinel-500" :
                      metric.color === "indigo" ? "bg-indigo-500" : "bg-rose-500"
                    }`}
                    style={{ width: `${metric.value * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </div>

          {/* Escalation Reason */}
          {c.escalation_reason && (
            <div className="glass-card p-4 border-l-4 border-l-orange-500">
              <h3 className="text-sm font-semibold text-orange-300 mb-1">Escalation Reason</h3>
              <p className="text-sm text-slate-300">{c.escalation_reason}</p>
            </div>
          )}

          {/* Result Details */}
          {c.result && (() => {
            const res = c.result as Record<string, unknown>;
            return (
              <div className="glass-card p-5">
                <h3 className="text-sm font-semibold text-white mb-3">Analysis Result</h3>
                {res.explanation ? (
                  <p className="text-sm text-slate-300 mb-4 leading-relaxed">
                    {String(res.explanation)}
                  </p>
                ) : null}
                {Array.isArray(res.details) ? (
                  <ul className="space-y-1.5">
                    {(res.details as string[]).map((d: string, i: number) => (
                      <li key={i} className="text-xs text-slate-400 flex items-start gap-2">
                        <span className="text-sentinel-500 mt-0.5">•</span>
                        {d}
                      </li>
                    ))}
                  </ul>
                ) : null}
              </div>
            );
          })()}

          {/* Investigation Timeline */}
          <div className="glass-card p-5">
            <h3 className="text-sm font-semibold text-white mb-4">Investigation Timeline</h3>
            {c.notes && c.notes.length > 0 ? (
              <div className="space-y-3">
                {c.notes.map((note) => (
                  <div key={note.id} className="flex gap-3 group">
                    <div className="flex flex-col items-center">
                      <div className="w-2 h-2 rounded-full bg-sentinel-500 mt-1.5" />
                      <div className="w-px flex-1 bg-white/5 group-last:hidden" />
                    </div>
                    <div className="pb-4">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-xs font-medium text-slate-300">{note.author}</span>
                        <span className="text-[10px] text-slate-600">
                          {new Date(note.timestamp).toLocaleString()}
                        </span>
                      </div>
                      <p className="text-sm text-slate-400">{note.note}</p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-600">No investigation notes yet.</p>
            )}

            {/* Add Note */}
            <div className="mt-4 pt-4 border-t border-white/5">
              <textarea
                value={noteText}
                onChange={(e) => setNoteText(e.target.value)}
                placeholder="Add investigation note..."
                className="w-full bg-white/[0.03] border border-white/10 rounded-lg px-3 py-2 text-sm text-slate-300 placeholder-slate-600 focus:outline-none focus:border-sentinel-500/50 resize-none"
                rows={3}
              />
              <button
                onClick={handleAddNote}
                disabled={submitting || !noteText.trim()}
                className="mt-2 px-4 py-1.5 bg-sentinel-600 hover:bg-sentinel-500 disabled:opacity-40 text-white text-sm rounded-lg transition"
              >
                {submitting ? "Adding…" : "Add Note"}
              </button>
            </div>
          </div>
        </div>

        {/* Right Column — Actions */}
        <div className="space-y-4">
          {/* Status */}
          <div className="glass-card p-4">
            <h3 className="text-xs text-slate-500 mb-3 font-semibold uppercase tracking-wider">Status</h3>
            <div className="space-y-1.5">
              {STATUS_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => handleStatusChange(opt.value)}
                  className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition ${
                    c.status === opt.value
                      ? "bg-white/10 text-white font-medium"
                      : "text-slate-400 hover:bg-white/5 hover:text-white"
                  }`}
                >
                  <div className={`w-2 h-2 rounded-full ${opt.color}`} />
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          {/* Assign */}
          <div className="glass-card p-4">
            <h3 className="text-xs text-slate-500 mb-3 font-semibold uppercase tracking-wider">Assigned To</h3>
            <input
              value={assignTo}
              onChange={(e) => setAssignTo(e.target.value)}
              placeholder="Enter username…"
              className="w-full bg-white/[0.03] border border-white/10 rounded-lg px-3 py-2 text-sm text-slate-300 placeholder-slate-600 focus:outline-none focus:border-sentinel-500/50"
            />
            <button
              onClick={() => handleStatusChange(c.status as CaseStatus)}
              className="mt-2 w-full px-3 py-1.5 bg-white/5 hover:bg-white/10 text-slate-300 text-xs rounded-lg transition"
            >
              Update Assignment
            </button>
          </div>

          {/* Meta */}
          <div className="glass-card p-4 space-y-3">
            <h3 className="text-xs text-slate-500 font-semibold uppercase tracking-wider">Details</h3>
            {[
              { label: "Created", value: new Date(c.created_at).toLocaleString() },
              { label: "Updated", value: new Date(c.updated_at).toLocaleString() },
              { label: "Content Hash", value: c.content_hash?.slice(0, 16) + "…" || "—" },
              { label: "Client", value: c.client_id?.slice(0, 8) || "—" },
            ].map((row) => (
              <div key={row.label} className="flex justify-between text-xs">
                <span className="text-slate-500">{row.label}</span>
                <span className="text-slate-300 font-mono">{row.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

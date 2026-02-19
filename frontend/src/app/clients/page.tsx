"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import {
  getClients,
  createClient,
  getClientRiskSummary,
  type Client,
  type ClientRiskSummary,
} from "@/lib/api";

const RISK_COLORS: Record<string, string> = {
  LOW: "bg-emerald-500",
  MEDIUM: "bg-yellow-500",
  HIGH: "bg-orange-500",
  CRITICAL: "bg-red-500",
};

/* ── Create Client Modal ───────────────────────────────────────────── */
function CreateClientModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [name, setName] = useState("");
  const [industry, setIndustry] = useState("");
  const [email, setEmail] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const handleCreate = async () => {
    if (!name.trim()) return;
    setSubmitting(true);
    try {
      await createClient(name.trim(), industry || undefined, email || undefined);
      onCreated();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create client");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="glass-card p-6 w-full max-w-md border border-white/10">
        <h2 className="text-lg font-semibold text-white mb-4">Register Client</h2>
        {error && <p className="text-red-400 text-xs mb-3">{error}</p>}
        <div className="space-y-3">
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Client name *"
            className="w-full bg-white/[0.03] border border-white/10 rounded-lg px-3 py-2 text-sm text-slate-300 placeholder-slate-600 focus:outline-none focus:border-sentinel-500/50"
          />
          <input
            value={industry}
            onChange={(e) => setIndustry(e.target.value)}
            placeholder="Industry (optional)"
            className="w-full bg-white/[0.03] border border-white/10 rounded-lg px-3 py-2 text-sm text-slate-300 placeholder-slate-600 focus:outline-none focus:border-sentinel-500/50"
          />
          <input
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Contact email (optional)"
            className="w-full bg-white/[0.03] border border-white/10 rounded-lg px-3 py-2 text-sm text-slate-300 placeholder-slate-600 focus:outline-none focus:border-sentinel-500/50"
          />
        </div>
        <div className="mt-4 flex justify-end gap-2">
          <button onClick={onClose} className="px-4 py-2 text-sm text-slate-400 hover:text-white transition">Cancel</button>
          <button
            onClick={handleCreate}
            disabled={submitting || !name.trim()}
            className="px-4 py-2 bg-sentinel-600 hover:bg-sentinel-500 disabled:opacity-40 text-white text-sm rounded-lg transition"
          >
            {submitting ? "Creating…" : "Create"}
          </button>
        </div>
      </div>
    </div>
  );
}

/* ── Risk Summary Panel ────────────────────────────────────────────── */
function RiskSummaryPanel({ summary, onClose }: { summary: ClientRiskSummary; onClose: () => void }) {
  const c = summary.client;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="glass-card p-6 w-full max-w-lg border border-white/10 max-h-[80vh] overflow-y-auto">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h2 className="text-lg font-semibold text-white">{c.name}</h2>
            <p className="text-xs text-slate-500">{c.industry || "No industry"} • {c.contact_email || "No email"}</p>
          </div>
          <button onClick={onClose} className="text-slate-500 hover:text-white text-lg">✕</button>
        </div>

        <div className="grid grid-cols-3 gap-3 mb-4">
          <div className="bg-white/[0.03] rounded-lg p-3 text-center">
            <p className="text-xl font-bold text-white">{c.total_cases}</p>
            <p className="text-xs text-slate-500">Total Cases</p>
          </div>
          <div className="bg-white/[0.03] rounded-lg p-3 text-center">
            <p className="text-xl font-bold text-red-400">{c.open_cases}</p>
            <p className="text-xs text-slate-500">Open Cases</p>
          </div>
          <div className="bg-white/[0.03] rounded-lg p-3 text-center">
            <p className="text-xl font-bold text-sentinel-400">{(c.avg_risk_score * 100).toFixed(0)}%</p>
            <p className="text-xs text-slate-500">Avg Risk</p>
          </div>
        </div>

        {/* Risk Distribution */}
        {Object.keys(summary.risk_distribution).length > 0 && (
          <div className="mb-4">
            <h3 className="text-xs text-slate-500 font-semibold uppercase tracking-wider mb-2">Risk Distribution</h3>
            <div className="flex gap-2">
              {Object.entries(summary.risk_distribution).map(([level, count]) => (
                <div key={level} className="flex items-center gap-1.5 text-xs">
                  <div className={`w-2.5 h-2.5 rounded ${RISK_COLORS[level] || "bg-slate-500"}`} />
                  <span className="text-slate-400">{level}: {count}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Recent Cases */}
        {summary.recent_cases.length > 0 && (
          <div>
            <h3 className="text-xs text-slate-500 font-semibold uppercase tracking-wider mb-2">Recent Cases</h3>
            <div className="space-y-2">
              {summary.recent_cases.map((rc) => (
                <Link
                  key={rc.id}
                  href={`/cases/${rc.id}`}
                  className="block bg-white/[0.03] rounded-lg p-3 hover:bg-white/[0.05] transition"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-sentinel-400 font-mono">{rc.id.slice(0, 12)}</span>
                    <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                      rc.risk_level === "CRITICAL" ? "bg-red-500/20 text-red-300" :
                      rc.risk_level === "HIGH" ? "bg-orange-500/20 text-orange-300" :
                      rc.risk_level === "MEDIUM" ? "bg-yellow-500/20 text-yellow-300" :
                      "bg-emerald-500/20 text-emerald-300"
                    }`}>
                      {rc.risk_level}
                    </span>
                  </div>
                  <div className="flex items-center gap-3 mt-1 text-[11px] text-slate-500">
                    <span>Risk: {(rc.risk_score * 100).toFixed(0)}%</span>
                    <span>Status: {rc.status}</span>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

/* ── Main Page ─────────────────────────────────────────────────────── */
export default function ClientsPage() {
  const [clients, setClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [selectedSummary, setSelectedSummary] = useState<ClientRiskSummary | null>(null);

  const fetchClients = useCallback(async () => {
    try {
      const data = await getClients({ limit: 200 });
      setClients(data.clients);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load clients");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchClients(); }, [fetchClients]);

  const handleViewRisk = async (clientId: string) => {
    try {
      const summary = await getClientRiskSummary(clientId);
      setSelectedSummary(summary);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load summary");
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
    <div className="min-h-screen bg-[#0a0e1a] p-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white">Corporate Clients</h1>
          <p className="text-sm text-slate-400 mt-1">{clients.length} registered clients</p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowCreate(true)}
            className="px-4 py-2 bg-sentinel-600 hover:bg-sentinel-500 text-white text-sm rounded-lg transition"
          >
            + Register Client
          </button>
          <Link href="/dashboard" className="text-sm text-sentinel-400 hover:text-sentinel-300 transition">← Dashboard</Link>
        </div>
      </div>

      {error && (
        <div className="mb-6 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-300 text-sm">
          {error}
        </div>
      )}

      {/* Client Grid */}
      <div className="grid grid-cols-3 gap-4">
        {clients.map((c) => (
          <div key={c.id} className="glass-card p-5 hover:border-white/10 transition">
            <div className="flex items-start justify-between mb-3">
              <div>
                <h3 className="text-sm font-semibold text-white">{c.name}</h3>
                <p className="text-xs text-slate-500 mt-0.5">{c.industry || "—"}</p>
              </div>
              <button
                onClick={() => handleViewRisk(c.id)}
                className="text-xs text-sentinel-400 hover:text-sentinel-300 transition"
              >
                Risk Profile →
              </button>
            </div>

            <div className="grid grid-cols-3 gap-2 mb-3">
              <div className="text-center">
                <p className="text-lg font-bold text-white">{c.total_cases}</p>
                <p className="text-[10px] text-slate-500">Cases</p>
              </div>
              <div className="text-center">
                <p className="text-lg font-bold text-red-400">{c.open_cases}</p>
                <p className="text-[10px] text-slate-500">Open</p>
              </div>
              <div className="text-center">
                <p className="text-lg font-bold text-sentinel-400">{(c.avg_risk_score * 100).toFixed(0)}%</p>
                <p className="text-[10px] text-slate-500">Avg Risk</p>
              </div>
            </div>

            <div className="flex items-center justify-between text-[11px] text-slate-600">
              <span>{c.contact_email || "No email"}</span>
              <span>{new Date(c.created_at).toLocaleDateString()}</span>
            </div>
          </div>
        ))}
        {clients.length === 0 && (
          <div className="col-span-3 text-center py-12 text-slate-500">
            No clients registered. Click &quot;Register Client&quot; to add one.
          </div>
        )}
      </div>

      {/* Modals */}
      {showCreate && <CreateClientModal onClose={() => setShowCreate(false)} onCreated={fetchClients} />}
      {selectedSummary && <RiskSummaryPanel summary={selectedSummary} onClose={() => setSelectedSummary(null)} />}
    </div>
  );
}

"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, LineChart, Line, Area, AreaChart,
} from "recharts";
import { getAnalyticsOverview, type AnalyticsOverview } from "@/lib/api";

const RISK_COLORS: Record<string, string> = {
  LOW: "#10b981",
  MEDIUM: "#eab308",
  HIGH: "#f97316",
  CRITICAL: "#ef4444",
};

const STATUS_COLORS: Record<string, string> = {
  OPEN: "#3b82f6",
  UNDER_REVIEW: "#eab308",
  ESCALATED: "#ef4444",
  RESOLVED: "#10b981",
  FALSE_POSITIVE: "#64748b",
};

const TYPE_COLORS = ["#4c6ef5", "#7c3aed", "#06b6d4"];

/* ── Stat Card ─────────────────────────────────────────────────────── */
function StatCard({ label, value, sub, accent }: { label: string; value: string; sub?: string; accent?: string }) {
  return (
    <div className="glass-card p-5">
      <p className="text-xs text-slate-500 font-medium uppercase tracking-wider mb-1">{label}</p>
      <p className={`text-2xl font-bold ${accent || "text-white"}`}>{value}</p>
      {sub && <p className="text-xs text-slate-500 mt-1">{sub}</p>}
    </div>
  );
}

/* ── Custom Tooltip ────────────────────────────────────────────────── */
function ChartTooltip({ active, payload, label }: { active?: boolean; payload?: { value: number; name?: string }[]; label?: string }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="glass-card px-3 py-2 text-xs border border-white/10">
      <p className="text-slate-400 mb-1">{label}</p>
      {payload.map((p, i) => (
        <p key={i} className="text-white font-medium">{p.name || "Count"}: {p.value}</p>
      ))}
    </div>
  );
}

export default function AnalyticsPage() {
  const [data, setData] = useState<AnalyticsOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [days, setDays] = useState(30);

  useEffect(() => {
    setLoading(true);
    getAnalyticsOverview(days)
      .then(setData)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed"))
      .finally(() => setLoading(false));
  }, [days]);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0a0e1a] flex items-center justify-center">
        <div className="animate-spin h-8 w-8 border-2 border-sentinel-500 border-t-transparent rounded-full" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="min-h-screen bg-[#0a0e1a] flex items-center justify-center">
        <div className="glass-card p-6 text-center">
          <p className="text-red-400 mb-4">{error || "No data"}</p>
          <Link href="/dashboard" className="text-sentinel-400 text-sm">← Dashboard</Link>
        </div>
      </div>
    );
  }

  const riskPieData = Object.entries(data.risk_breakdown).map(([name, value]) => ({
    name, value, color: RISK_COLORS[name] || "#64748b",
  }));

  const statusPieData = Object.entries(data.case_status).map(([name, value]) => ({
    name, value, color: STATUS_COLORS[name] || "#64748b",
  }));

  const typePieData = Object.entries(data.type_breakdown).map(([name, value]) => ({
    name, value,
  }));

  return (
    <div className="min-h-screen bg-[#0a0e1a] p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white">Fraud Analytics</h1>
          <p className="text-sm text-slate-400 mt-1">Trend analysis over {days} days</p>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
            className="bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-sm text-slate-300 focus:outline-none focus:border-sentinel-500/50"
          >
            <option value={7}>7 days</option>
            <option value={30}>30 days</option>
            <option value={90}>90 days</option>
            <option value={365}>1 year</option>
          </select>
          <Link href="/dashboard" className="text-sm text-sentinel-400 hover:text-sentinel-300 transition">← Dashboard</Link>
        </div>
      </div>

      {/* Top Stats */}
      <div className="grid grid-cols-5 gap-4 mb-8">
        <StatCard label="Total Cases" value={String(data.total_cases)} />
        <StatCard label="Escalated" value={String(data.total_escalated)} accent="text-red-400" />
        <StatCard label="AI-Generated Fraud" value={`${data.ai_fraud_percentage}%`} accent="text-indigo-400" />
        <StatCard label="Avg Resolution" value={data.avg_resolution_hours ? `${data.avg_resolution_hours}h` : "—"} />
        <StatCard
          label="Top Keyword"
          value={data.top_fraud_keywords[0]?.keyword || "—"}
          sub={data.top_fraud_keywords[0] ? `${data.top_fraud_keywords[0].count} occurrences` : undefined}
        />
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-2 gap-6 mb-6">
        {/* Fraud Trend */}
        <div className="glass-card p-5">
          <h3 className="text-sm font-semibold text-white mb-4">Daily Fraud Detections</h3>
          <ResponsiveContainer width="100%" height={240}>
            <AreaChart data={data.fraud_per_day}>
              <defs>
                <linearGradient id="fraudGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#ef4444" stopOpacity={0.3} />
                  <stop offset="100%" stopColor="#ef4444" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="date" tick={{ fontSize: 10, fill: "#64748b" }} />
              <YAxis tick={{ fontSize: 10, fill: "#64748b" }} allowDecimals={false} />
              <Tooltip content={<ChartTooltip />} />
              <Area type="monotone" dataKey="count" stroke="#ef4444" fill="url(#fraudGrad)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Risk Breakdown */}
        <div className="glass-card p-5">
          <h3 className="text-sm font-semibold text-white mb-4">Risk Level Distribution</h3>
          <div className="flex items-center gap-6">
            <ResponsiveContainer width="50%" height={200}>
              <PieChart>
                <Pie
                  data={riskPieData}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  innerRadius={40}
                  paddingAngle={2}
                >
                  {riskPieData.map((entry, i) => (
                    <Cell key={i} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
            <div className="space-y-2">
              {riskPieData.map((entry) => (
                <div key={entry.name} className="flex items-center gap-2 text-xs">
                  <div className="w-3 h-3 rounded" style={{ backgroundColor: entry.color }} />
                  <span className="text-slate-400">{entry.name}</span>
                  <span className="text-white font-medium ml-auto">{entry.value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-cols-3 gap-6 mb-6">
        {/* Case Status */}
        <div className="glass-card p-5">
          <h3 className="text-sm font-semibold text-white mb-4">Case Status</h3>
          <ResponsiveContainer width="100%" height={180}>
            <PieChart>
              <Pie data={statusPieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={70} innerRadius={30}>
                {statusPieData.map((entry, i) => (
                  <Cell key={i} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
          <div className="flex flex-wrap gap-2 mt-2">
            {statusPieData.map((s) => (
              <span key={s.name} className="text-[10px] px-2 py-0.5 rounded-full border border-white/10 text-slate-400">
                <span className="inline-block w-2 h-2 rounded-full mr-1" style={{ backgroundColor: s.color }} />
                {s.name.replace("_", " ")} ({s.value})
              </span>
            ))}
          </div>
        </div>

        {/* Analysis Type Breakdown */}
        <div className="glass-card p-5">
          <h3 className="text-sm font-semibold text-white mb-4">Analysis Types</h3>
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={typePieData}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="name" tick={{ fontSize: 10, fill: "#64748b" }} />
              <YAxis tick={{ fontSize: 10, fill: "#64748b" }} allowDecimals={false} />
              <Tooltip content={<ChartTooltip />} />
              <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                {typePieData.map((_, i) => (
                  <Cell key={i} fill={TYPE_COLORS[i % TYPE_COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Top Keywords */}
        <div className="glass-card p-5">
          <h3 className="text-sm font-semibold text-white mb-4">Top Fraud Keywords</h3>
          {data.top_fraud_keywords.length > 0 ? (
            <div className="space-y-2">
              {data.top_fraud_keywords.map((kw, i) => (
                <div key={kw.keyword} className="flex items-center gap-2">
                  <span className="text-xs text-slate-500 w-4">{i + 1}</span>
                  <span className="text-xs text-slate-300 flex-1 truncate">{kw.keyword}</span>
                  <div className="flex-1 h-1.5 rounded-full bg-slate-800 max-w-[80px]">
                    <div
                      className="h-full rounded-full bg-sentinel-500"
                      style={{
                        width: `${(kw.count / (data.top_fraud_keywords[0]?.count || 1)) * 100}%`,
                      }}
                    />
                  </div>
                  <span className="text-xs text-slate-500 w-6 text-right">{kw.count}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-slate-600 text-center py-8">No keyword data yet</p>
          )}
        </div>
      </div>
    </div>
  );
}

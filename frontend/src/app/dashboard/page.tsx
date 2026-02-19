"use client";

import { useState, useCallback, useEffect } from "react";
import Link from "next/link";
import {
  analyzeText,
  analyzeImage,
  analyzeDocument,
  getAuditLogs,
  healthCheck,
  type TextAnalysisResult,
  type ImageAnalysisResult,
  type DocumentAnalysisResult,
  type AuditLogEntry,
  type HealthStatus,
} from "@/lib/api";
import RiskGauge from "@/components/RiskGauge";
import FileUpload from "@/components/FileUpload";
import JsonViewer from "@/components/JsonViewer";
import LoadingSkeleton from "@/components/LoadingSkeleton";
import SignalBar from "@/components/SignalBar";

/* ── Icon helpers ──────────────────────────────────────────────────────── */
const ShieldIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
  </svg>
);
const TextIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
    <polyline points="14 2 14 8 20 8" /><line x1="16" y1="13" x2="8" y2="13" />
    <line x1="16" y1="17" x2="8" y2="17" /><polyline points="10 9 9 9 8 9" />
  </svg>
);
const DocIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M4 4v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8.342a2 2 0 0 0-.602-1.43l-4.44-4.342A2 2 0 0 0 13.56 2H6a2 2 0 0 0-2 2z" />
    <path d="M9 13h6" /><path d="M9 17h3" /><path d="M14 2v4a2 2 0 0 0 2 2h4" />
  </svg>
);
const ImageIconSvg = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
    <circle cx="8.5" cy="8.5" r="1.5" /><polyline points="21 15 16 10 5 21" />
  </svg>
);
const SendIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="22" y1="2" x2="11" y2="13" /><polygon points="22 2 15 22 11 13 2 9 22 2" />
  </svg>
);
const AlertIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
    <line x1="12" y1="9" x2="12" y2="13" /><line x1="12" y1="17" x2="12.01" y2="17" />
  </svg>
);
const LogIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
    <path d="M14 2v6h6" /><path d="M16 13H8" /><path d="M16 17H8" /><path d="M10 9H8" />
  </svg>
);

/* ── Risk badge color ──────────────────────────────────────────────────── */
function riskBadge(level: string) {
  const map: Record<string, string> = {
    LOW: "risk-badge risk-low",
    MEDIUM: "risk-badge risk-medium",
    HIGH: "risk-badge risk-high",
    CRITICAL: "risk-badge risk-critical",
  };
  return map[level] || "risk-badge risk-low";
}

function riskHeatColor(score: number): string {
  if (score >= 0.8) return "text-red-400";
  if (score >= 0.6) return "text-orange-400";
  if (score >= 0.3) return "text-yellow-400";
  return "text-emerald-400";
}

/* ── Tab definitions ───────────────────────────────────────────────────── */
type TabId = "text" | "document" | "image";
type ViewId = "analyze" | "audit";
const TABS: { id: TabId; label: string; icon: React.ReactNode }[] = [
  { id: "text", label: "Text", icon: <TextIcon /> },
  { id: "document", label: "Document", icon: <DocIcon /> },
  { id: "image", label: "Image", icon: <ImageIconSvg /> },
];

type AnyResult = TextAnalysisResult | ImageAnalysisResult | DocumentAnalysisResult;

/* ── Dashboard Page ────────────────────────────────────────────────────── */
export default function DashboardPage() {
  const [view, setView] = useState<ViewId>("analyze");
  const [activeTab, setActiveTab] = useState<TabId>("text");
  const [textInput, setTextInput] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AnyResult | null>(null);
  const [resultTab, setResultTab] = useState<TabId>("text");

  // Audit log state
  const [auditLogs, setAuditLogs] = useState<AuditLogEntry[]>([]);
  const [auditLoading, setAuditLoading] = useState(false);
  const [auditFilter, setAuditFilter] = useState<string>("");
  const [flaggedOnly, setFlaggedOnly] = useState(false);

  // Health status
  const [health, setHealth] = useState<HealthStatus | null>(null);

  // Check health on mount
  useEffect(() => {
    healthCheck().then(setHealth).catch(() => setHealth(null));
  }, []);

  // Load audit logs when switching to audit view
  useEffect(() => {
    if (view === "audit") {
      loadAuditLogs();
    }
  }, [view, auditFilter, flaggedOnly]);

  const loadAuditLogs = async () => {
    setAuditLoading(true);
    try {
      const res = await getAuditLogs({
        limit: 50,
        flagged_only: flaggedOnly,
        input_type: auditFilter || undefined,
      });
      setAuditLogs(res.logs);
    } catch {
      setAuditLogs([]);
    } finally {
      setAuditLoading(false);
    }
  };

  // ── Submit handler ────────────────────────────────────────────
  const handleSubmit = useCallback(async () => {
    setError(null);
    setResult(null);
    setLoading(true);
    setResultTab(activeTab);

    try {
      if (activeTab === "text") {
        if (textInput.trim().length < 10) throw new Error("Please enter at least 10 characters of text.");
        const res = await analyzeText(textInput);
        setResult(res);
      } else if (activeTab === "document") {
        if (!selectedFile) throw new Error("Please select a PDF file.");
        const res = await analyzeDocument(selectedFile);
        setResult(res);
      } else if (activeTab === "image") {
        if (!selectedFile) throw new Error("Please select an image file.");
        const res = await analyzeImage(selectedFile);
        setResult(res);
      }
    } catch (err: any) {
      setError(err.message || "Analysis failed. Make sure the backend is running.");
    } finally {
      setLoading(false);
    }
  }, [activeTab, textInput, selectedFile]);

  const switchTab = (tab: TabId) => {
    setActiveTab(tab);
    setSelectedFile(null);
    setError(null);
  };

  // ── Result type guards ────────────────────────────────────────
  const isTextResult = (r: AnyResult): r is TextAnalysisResult =>
    "stylometric_features" in r && "risk_score" in r && !("extracted_text_preview" in r);
  const isDocResult = (r: AnyResult): r is DocumentAnalysisResult =>
    "extracted_text_preview" in r;
  const isImageResult = (r: AnyResult): r is ImageAnalysisResult =>
    "deepfake_probability" in r;

  return (
    <div className="min-h-screen bg-[#0a0e1a]">
      {/* ── Top bar ────────────────────────────────────────────── */}
      <header className="sticky top-0 z-50 border-b border-white/[0.04] bg-[#0a0e1a]/80 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-3">
          <Link href="/" className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-sentinel-600 shadow-md shadow-sentinel-600/20">
              <ShieldIcon />
            </div>
            <span className="text-base font-bold tracking-tight text-white">
              Sentinel<span className="text-sentinel-400">AI</span>
            </span>
          </Link>
          <div className="flex items-center gap-4">
            {/* View toggle */}
            <div className="flex gap-1 rounded-lg bg-white/[0.03] p-1">
              <button
                onClick={() => setView("analyze")}
                className={`rounded-md px-3 py-1.5 text-xs font-medium transition-all ${
                  view === "analyze" ? "bg-sentinel-600/20 text-sentinel-300" : "text-slate-500 hover:text-slate-300"
                }`}
              >
                Analyze
              </button>
              <button
                onClick={() => setView("audit")}
                className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-all ${
                  view === "audit" ? "bg-sentinel-600/20 text-sentinel-300" : "text-slate-500 hover:text-slate-300"
                }`}
              >
                <LogIcon /> Audit Log
              </button>
            </div>
            {/* Status indicators */}
            <div className="hidden items-center gap-2 sm:flex">
              {health && (
                <>
                  <div className={`h-2 w-2 rounded-full ${health.models.ai_detector ? "bg-emerald-500" : "bg-yellow-500"} shadow-lg`} />
                  <span className="text-[10px] text-slate-600">
                    ML {health.models.ai_detector ? "Active" : "Fallback"}
                  </span>
                  <div className={`h-2 w-2 rounded-full ${health.ollama ? "bg-emerald-500" : "bg-slate-600"} shadow-lg`} />
                  <span className="text-[10px] text-slate-600">
                    LLM {health.ollama ? "Connected" : "Offline"}
                  </span>
                </>
              )}
              {!health && (
                <>
                  <div className="h-2 w-2 rounded-full bg-red-500 shadow-lg" />
                  <span className="text-[10px] text-slate-600">Backend Offline</span>
                </>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* ── Audit Log View ─────────────────────────────────────── */}
      {view === "audit" && (
        <main className="mx-auto max-w-7xl px-6 py-8">
          <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <h2 className="text-lg font-semibold text-white">Audit Log</h2>
            <div className="flex gap-2">
              <select
                value={auditFilter}
                onChange={(e) => setAuditFilter(e.target.value)}
                className="rounded-lg border border-white/[0.06] bg-white/[0.03] px-3 py-1.5 text-xs text-slate-300"
              >
                <option value="">All Types</option>
                <option value="text">Text</option>
                <option value="image">Image</option>
                <option value="document">Document</option>
              </select>
              <button
                onClick={() => setFlaggedOnly(!flaggedOnly)}
                className={`rounded-lg border px-3 py-1.5 text-xs font-medium transition-all ${
                  flaggedOnly
                    ? "border-red-500/30 bg-red-500/10 text-red-400"
                    : "border-white/[0.06] bg-white/[0.03] text-slate-400"
                }`}
              >
                {flaggedOnly ? "Flagged Only" : "Show All"}
              </button>
              <button
                onClick={loadAuditLogs}
                className="rounded-lg border border-white/[0.06] bg-white/[0.03] px-3 py-1.5 text-xs text-slate-400 hover:text-white transition-all"
              >
                Refresh
              </button>
            </div>
          </div>

          {auditLoading ? (
            <LoadingSkeleton title="Loading audit logs..." lines={8} />
          ) : auditLogs.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-20 text-center">
              <LogIcon />
              <p className="mt-4 text-sm text-slate-500">No audit log entries found.</p>
            </div>
          ) : (
            <div className="space-y-2">
              {/* Table header */}
              <div className="grid grid-cols-[60px_100px_80px_100px_100px_80px_1fr] gap-3 px-4 py-2 text-[10px] uppercase tracking-wider text-slate-600">
                <span>ID</span>
                <span>Timestamp</span>
                <span>Type</span>
                <span>AI Prob</span>
                <span>Fraud Score</span>
                <span>Risk</span>
                <span>Flagged</span>
              </div>
              {auditLogs.map((log) => (
                <div
                  key={log.id}
                  className={`glass-card grid grid-cols-[60px_100px_80px_100px_100px_80px_1fr] items-center gap-3 px-4 py-3 text-xs ${
                    log.flagged ? "border-red-500/10" : ""
                  }`}
                >
                  <span className="text-slate-500">#{log.id}</span>
                  <span className="text-slate-500 truncate" title={log.timestamp}>
                    {new Date(log.timestamp).toLocaleString("en-US", {
                      month: "short", day: "numeric", hour: "2-digit", minute: "2-digit",
                    })}
                  </span>
                  <span className="rounded-full bg-white/[0.04] px-2 py-0.5 text-center text-slate-400">
                    {log.input_type}
                  </span>
                  <span className={riskHeatColor(log.ai_probability)}>
                    {(log.ai_probability * 100).toFixed(1)}%
                  </span>
                  <span className={riskHeatColor(log.fraud_risk_score)}>
                    {(log.fraud_risk_score * 100).toFixed(1)}%
                  </span>
                  <span className={riskBadge(log.risk_level)}>{log.risk_level}</span>
                  <span>
                    {log.flagged && (
                      <span className="text-red-400 flex items-center gap-1">
                        <AlertIcon /> Flagged
                      </span>
                    )}
                  </span>
                </div>
              ))}
            </div>
          )}
        </main>
      )}

      {/* ── Analysis View ──────────────────────────────────────── */}
      {view === "analyze" && (
        <main className="mx-auto max-w-7xl px-6 py-8">
          <div className="grid gap-8 lg:grid-cols-[420px_1fr]">
            {/* ── Left Panel: Input ──────────────────────────────── */}
            <div className="space-y-6">
              {/* Tab selector */}
              <div className="glass-card p-1.5">
                <div className="flex gap-1">
                  {TABS.map((tab) => (
                    <button
                      key={tab.id}
                      onClick={() => switchTab(tab.id)}
                      className={`flex flex-1 items-center justify-center gap-2 rounded-lg py-2.5 text-sm font-medium transition-all duration-200 ${
                        activeTab === tab.id
                          ? "bg-sentinel-600/20 text-sentinel-300 shadow-sm"
                          : "text-slate-500 hover:bg-white/[0.03] hover:text-slate-300"
                      }`}
                    >
                      {tab.icon}
                      {tab.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Input area */}
              <div className="glass-card p-5">
                <h2 className="mb-4 flex items-center gap-2 text-sm font-semibold text-slate-300">
                  {activeTab === "text" && (<><TextIcon /> Paste Text to Analyse</>)}
                  {activeTab === "document" && (<><DocIcon /> Upload PDF Document</>)}
                  {activeTab === "image" && (<><ImageIconSvg /> Upload Image</>)}
                </h2>

                {activeTab === "text" && (
                  <textarea
                    value={textInput}
                    onChange={(e) => setTextInput(e.target.value)}
                    placeholder="Paste suspicious text here — email content, chat messages, letters, etc."
                    className="input-dark custom-scrollbar min-h-[240px] resize-y font-mono text-xs leading-relaxed"
                    disabled={loading}
                  />
                )}

                {activeTab === "document" && (
                  <FileUpload
                    accept=".pdf,application/pdf"
                    label="Drop a PDF here, or click to browse"
                    hint="Max 20 MB — text will be extracted automatically"
                    icon={<DocIcon />}
                    onFileSelected={setSelectedFile}
                    disabled={loading}
                  />
                )}

                {activeTab === "image" && (
                  <FileUpload
                    accept="image/jpeg,image/png,image/webp,image/bmp,image/tiff"
                    label="Drop an image here, or click to browse"
                    hint="JPEG, PNG, WebP, BMP, TIFF — Max 10 MB"
                    icon={<ImageIconSvg />}
                    onFileSelected={setSelectedFile}
                    disabled={loading}
                  />
                )}

                {activeTab === "text" && (
                  <div className="mt-2 text-right text-[11px] text-slate-700">
                    {textInput.length.toLocaleString()} characters
                  </div>
                )}
              </div>

              {/* Submit button */}
              <button onClick={handleSubmit} disabled={loading} className="btn-primary w-full py-3">
                {loading ? (
                  <>
                    <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                    Analysing...
                  </>
                ) : (
                  <><SendIcon /> Run Analysis</>
                )}
              </button>

              {/* Error */}
              {error && (
                <div className="animate-slide-down flex items-start gap-3 rounded-xl border border-red-500/20 bg-red-500/10 p-4">
                  <div className="mt-0.5 text-red-400"><AlertIcon /></div>
                  <p className="text-sm text-red-300">{error}</p>
                </div>
              )}

              {/* Quick tip */}
              <div className="rounded-xl border border-white/[0.04] bg-white/[0.01] p-4">
                <p className="text-xs leading-relaxed text-slate-600">
                  <strong className="text-slate-500">Tip:</strong> For best results, paste
                  the complete email or message content. The engine analyses sentence structure,
                  vocabulary patterns, and fraud-intent signals across the full text.
                </p>
              </div>
            </div>

            {/* ── Right Panel: Results ───────────────────────────── */}
            <div className="space-y-6">
              {loading && <LoadingSkeleton title="Running detection pipeline..." />}

              {!loading && !result && !error && (
                <div className="flex flex-col items-center justify-center py-24 text-center">
                  <div className="mb-6 flex h-20 w-20 items-center justify-center rounded-2xl bg-white/[0.02] text-slate-700">
                    <ShieldIcon />
                  </div>
                  <h3 className="text-lg font-semibold text-slate-500">Ready to Analyse</h3>
                  <p className="mx-auto mt-2 max-w-sm text-sm text-slate-700">
                    Paste text, upload a document, or submit an image on the left to run the AI fraud detection pipeline.
                  </p>
                </div>
              )}

              {/* ── Text Results ─────────────────────────────────── */}
              {result && isTextResult(result) && (
                <div className="animate-slide-up space-y-6">
                  {/* Triple gauge row */}
                  <div className="grid gap-4 sm:grid-cols-3">
                    <div className="glass-card p-5">
                      <RiskGauge score={result.ai_probability} riskLevel={result.risk_level} label="AI Probability" size="sm" />
                    </div>
                    <div className="glass-card p-5">
                      <RiskGauge score={result.fraud_probability} riskLevel={result.risk_level} label="Fraud Probability" size="sm" />
                    </div>
                    <div className="glass-card p-5">
                      <RiskGauge score={result.risk_score} riskLevel={result.risk_level} label="Risk Score" size="sm" />
                    </div>
                  </div>

                  {/* LLM Explanation */}
                  <div className="glass-card p-6">
                    <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-slate-300">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
                      AI Explanation
                    </h3>
                    <p className="text-sm leading-relaxed text-slate-400 whitespace-pre-wrap">{result.explanation}</p>
                    {result.details.length > 0 && (
                      <ul className="mt-4 space-y-2">
                        {result.details.map((d, i) => (
                          <li key={i} className="flex items-start gap-2 text-xs leading-relaxed text-slate-500">
                            <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-sentinel-500/60" />
                            {d}
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>

                  {/* Fraud Signals */}
                  <div className="glass-card space-y-5 p-6">
                    <h3 className="text-sm font-semibold text-slate-300">Fraud Intent Signals</h3>
                    <SignalBar label="Urgency Language" score={result.fraud_signals.urgency.score} count={result.fraud_signals.urgency.count} keywords={result.fraud_signals.urgency.keywords} color="red" />
                    <SignalBar label="Financial Redirection" score={result.fraud_signals.financial_redirection.score} count={result.fraud_signals.financial_redirection.count} keywords={result.fraud_signals.financial_redirection.keywords} color="orange" />
                    <SignalBar label="Impersonation" score={result.fraud_signals.impersonation.score} count={result.fraud_signals.impersonation.count} keywords={result.fraud_signals.impersonation.keywords} color="yellow" />
                  </div>

                  {/* Highlighted Phrases */}
                  {result.highlighted_phrases.length > 0 && (
                    <div className="glass-card p-6">
                      <h3 className="mb-3 text-sm font-semibold text-slate-300">Suspicious Phrases</h3>
                      <div className="flex flex-wrap gap-2">
                        {result.highlighted_phrases.map((phrase, i) => (
                          <span key={i} className="rounded-lg border border-red-500/20 bg-red-500/10 px-3 py-1.5 text-xs font-medium text-red-400">
                            &ldquo;{phrase}&rdquo;
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Stylometric Features */}
                  <div className="glass-card p-6">
                    <h3 className="mb-4 text-sm font-semibold text-slate-300">Stylometric Profile</h3>
                    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
                      {Object.entries(result.stylometric_features).map(([key, value]) => (
                        <div key={key} className="rounded-lg border border-white/[0.04] bg-white/[0.02] p-3">
                          <div className="text-[10px] uppercase tracking-wider text-slate-600">{key.replace(/_/g, " ")}</div>
                          <div className="mt-1 text-lg font-semibold tabular-nums text-slate-300">
                            {typeof value === "number" ? value.toFixed(3) : value}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  <JsonViewer data={result} />
                </div>
              )}

              {/* ── Document Results ─────────────────────────────── */}
              {result && isDocResult(result) && (
                <div className="animate-slide-up space-y-6">
                  <div className="grid gap-4 sm:grid-cols-3">
                    <div className="glass-card p-6">
                      <RiskGauge score={result.ai_probability} riskLevel={result.risk_level} label="AI Probability" size="sm" />
                    </div>
                    <div className="glass-card p-6">
                      <RiskGauge score={result.fraud_probability ?? result.fraud_risk_score} riskLevel={result.risk_level} label="Fraud Probability" size="sm" />
                    </div>
                    <div className="glass-card p-6">
                      <RiskGauge score={result.risk_score ?? result.fraud_risk_score} riskLevel={result.risk_level} label="Risk Score" size="sm" />
                    </div>
                  </div>

                  <div className="glass-card p-6">
                    <h3 className="mb-3 text-sm font-semibold text-slate-300">Explanation</h3>
                    <p className="text-sm leading-relaxed text-slate-400">{result.explanation}</p>
                    {result.details.length > 0 && (
                      <ul className="mt-4 space-y-2">
                        {result.details.map((d, i) => (
                          <li key={i} className="flex items-start gap-2 text-xs leading-relaxed text-slate-500">
                            <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-sentinel-500/60" />
                            {d}
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>

                  <div className="glass-card space-y-5 p-6">
                    <h3 className="text-sm font-semibold text-slate-300">Fraud Intent Signals</h3>
                    <SignalBar label="Urgency Language" score={result.fraud_signals.urgency.score} count={result.fraud_signals.urgency.count} keywords={result.fraud_signals.urgency.keywords} color="red" />
                    <SignalBar label="Financial Redirection" score={result.fraud_signals.financial_redirection.score} count={result.fraud_signals.financial_redirection.count} keywords={result.fraud_signals.financial_redirection.keywords} color="orange" />
                    <SignalBar label="Impersonation" score={result.fraud_signals.impersonation.score} count={result.fraud_signals.impersonation.count} keywords={result.fraud_signals.impersonation.keywords} color="yellow" />
                  </div>

                  {result.extracted_text_preview && (
                    <div className="glass-card p-6">
                      <h3 className="mb-3 text-sm font-semibold text-slate-300">
                        Extracted Text Preview
                        <span className="ml-2 text-xs font-normal text-slate-600">{result.page_count} page{result.page_count !== 1 ? "s" : ""}</span>
                      </h3>
                      <p className="custom-scrollbar max-h-40 overflow-y-auto rounded-lg bg-black/20 p-4 font-mono text-xs leading-relaxed text-slate-500">
                        {result.extracted_text_preview}
                      </p>
                    </div>
                  )}

                  <div className="glass-card p-6">
                    <h3 className="mb-4 text-sm font-semibold text-slate-300">Stylometric Profile</h3>
                    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
                      {Object.entries(result.stylometric_features).map(([key, value]) => (
                        <div key={key} className="rounded-lg border border-white/[0.04] bg-white/[0.02] p-3">
                          <div className="text-[10px] uppercase tracking-wider text-slate-600">{key.replace(/_/g, " ")}</div>
                          <div className="mt-1 text-lg font-semibold tabular-nums text-slate-300">
                            {typeof value === "number" ? value.toFixed(3) : value}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  <JsonViewer data={result} />
                </div>
              )}

              {/* ── Image Results ────────────────────────────────── */}
              {result && isImageResult(result) && (
                <div className="animate-slide-up space-y-6">
                  <div className="grid gap-4 sm:grid-cols-2">
                    <div className="glass-card p-6">
                      <RiskGauge score={result.deepfake_probability} riskLevel={result.risk_level} label="Deepfake Probability" />
                    </div>
                    <div className="glass-card p-6">
                      <RiskGauge score={result.fraud_risk_score} riskLevel={result.risk_level} label="Fraud Risk Score" />
                    </div>
                  </div>

                  <div className="glass-card p-6">
                    <h3 className="mb-3 text-sm font-semibold text-slate-300">Explanation</h3>
                    <p className="text-sm leading-relaxed text-slate-400">{result.explanation}</p>
                    {result.details.length > 0 && (
                      <ul className="mt-4 space-y-2">
                        {result.details.map((d, i) => (
                          <li key={i} className="flex items-start gap-2 text-xs leading-relaxed text-slate-500">
                            <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-sentinel-500/60" />
                            {d}
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>

                  <div className="glass-card p-6">
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-slate-500">Analysis Method</span>
                      <span className="rounded-full border border-white/[0.06] bg-white/[0.03] px-3 py-1 text-xs font-medium text-slate-400">
                        {result.analysis_method}
                      </span>
                    </div>
                  </div>

                  <JsonViewer data={result} />
                </div>
              )}
            </div>
          </div>
        </main>
      )}
    </div>
  );
}

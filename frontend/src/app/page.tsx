"use client";

import Link from "next/link";
import { useState, useEffect } from "react";

/* ── Animated background grid ──────────────────────────────────────── */
function GridBackground() {
  return (
    <div className="pointer-events-none fixed inset-0 z-0 overflow-hidden">
      {/* Radial gradient overlay */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,rgba(76,110,245,0.08)_0%,transparent_60%)]" />
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_bottom_right,rgba(99,102,241,0.05)_0%,transparent_50%)]" />
      {/* Grid lines */}
      <div
        className="absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage: `
            linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)
          `,
          backgroundSize: "60px 60px",
        }}
      />
      {/* Floating orbs */}
      <div className="absolute -top-40 -left-40 h-80 w-80 rounded-full bg-sentinel-600/10 blur-[120px] animate-pulse-slow" />
      <div className="absolute top-1/3 -right-20 h-96 w-96 rounded-full bg-indigo-600/8 blur-[150px] animate-pulse-slow" />
      <div className="absolute -bottom-20 left-1/3 h-72 w-72 rounded-full bg-sentinel-700/10 blur-[100px] animate-pulse-slow" />
    </div>
  );
}

/* ── Feature card ──────────────────────────────────────────────────── */
function FeatureCard({
  icon,
  title,
  description,
  delay,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
  delay: number;
}) {
  const [visible, setVisible] = useState(false);
  useEffect(() => {
    const t = setTimeout(() => setVisible(true), delay);
    return () => clearTimeout(t);
  }, [delay]);

  return (
    <div
      className={`glass-card glow-hover p-6 transition-all duration-700 ${
        visible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-6"
      }`}
    >
      <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-lg bg-sentinel-600/15 text-sentinel-400">
        {icon}
      </div>
      <h3 className="mb-2 text-lg font-semibold text-white">{title}</h3>
      <p className="text-sm leading-relaxed text-slate-400">{description}</p>
    </div>
  );
}

/* ── Stat counter ──────────────────────────────────────────────────── */
function StatCounter({
  value,
  label,
  suffix = "",
}: {
  value: string;
  label: string;
  suffix?: string;
}) {
  return (
    <div className="text-center">
      <div className="text-3xl font-bold text-white">
        {value}
        <span className="text-sentinel-400">{suffix}</span>
      </div>
      <div className="mt-1 text-sm text-slate-500">{label}</div>
    </div>
  );
}

/* ── Icons (inline SVGs to avoid dependency issues) ────────────────── */
const ShieldIcon = () => (
  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
  </svg>
);

const ScanIcon = () => (
  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M3 7V5a2 2 0 0 1 2-2h2" /><path d="M17 3h2a2 2 0 0 1 2 2v2" />
    <path d="M21 17v2a2 2 0 0 1-2 2h-2" /><path d="M7 21H5a2 2 0 0 1-2-2v-2" />
    <line x1="7" y1="12" x2="17" y2="12" />
  </svg>
);

const BrainIcon = () => (
  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96.44 2.5 2.5 0 0 1-2.96-3.08 3 3 0 0 1-.34-5.58 2.5 2.5 0 0 1 1.32-4.24 2.5 2.5 0 0 1 1.98-3A2.5 2.5 0 0 1 9.5 2Z" />
    <path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96.44 2.5 2.5 0 0 0 2.96-3.08 3 3 0 0 0 .34-5.58 2.5 2.5 0 0 0-1.32-4.24 2.5 2.5 0 0 0-1.98-3A2.5 2.5 0 0 0 14.5 2Z" />
  </svg>
);

const FileTextIcon = () => (
  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
    <polyline points="14 2 14 8 20 8" />
    <line x1="16" y1="13" x2="8" y2="13" />
    <line x1="16" y1="17" x2="8" y2="17" />
    <polyline points="10 9 9 9 8 9" />
  </svg>
);

const ImageIcon = () => (
  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
    <circle cx="8.5" cy="8.5" r="1.5" /><polyline points="21 15 16 10 5 21" />
  </svg>
);

const ChartIcon = () => (
  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="18" y1="20" x2="18" y2="10" /><line x1="12" y1="20" x2="12" y2="4" />
    <line x1="6" y1="20" x2="6" y2="14" />
  </svg>
);

const ArrowRight = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="5" y1="12" x2="19" y2="12" /><polyline points="12 5 19 12 12 19" />
  </svg>
);

/* ── Main Landing Page ─────────────────────────────────────────────── */
export default function LandingPage() {
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  return (
    <div className="relative min-h-screen overflow-hidden">
      <GridBackground />

      {/* ── Nav ─────────────────────────────────────────────────────── */}
      <nav className="relative z-10 mx-auto flex max-w-7xl items-center justify-between px-6 py-5">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-sentinel-600 shadow-lg shadow-sentinel-600/25">
            <ShieldIcon />
          </div>
          <span className="text-lg font-bold tracking-tight text-white">
            Sentinel<span className="text-sentinel-400">AI</span>
          </span>
        </div>
        <div className="hidden items-center gap-8 md:flex">
          <a href="#features" className="text-sm text-slate-400 transition hover:text-white">
            Features
          </a>
          <a href="#how-it-works" className="text-sm text-slate-400 transition hover:text-white">
            How It Works
          </a>
          <Link href="/dashboard" className="btn-primary text-sm">
            Open Dashboard
          </Link>
        </div>
        <Link href="/dashboard" className="btn-primary text-sm md:hidden">
          Dashboard
        </Link>
      </nav>

      {/* ── Hero ────────────────────────────────────────────────────── */}
      <section className="relative z-10 mx-auto max-w-7xl px-6 pb-20 pt-16 md:pt-24 lg:pt-32">
        <div className="mx-auto max-w-3xl text-center">
          {/* Badge */}
          <div
            className={`mb-6 inline-flex items-center gap-2 rounded-full border border-sentinel-500/20 bg-sentinel-500/10 px-4 py-1.5 text-xs font-medium text-sentinel-300 transition-all duration-700 ${
              mounted ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"
            }`}
          >
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-sentinel-400 opacity-75" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-sentinel-400" />
            </span>
            AI-Powered Fraud Detection Engine
          </div>

          {/* Headline */}
          <h1
            className={`text-4xl font-extrabold leading-tight tracking-tight text-white sm:text-5xl lg:text-6xl transition-all duration-700 delay-100 ${
              mounted ? "opacity-100 translate-y-0" : "opacity-0 translate-y-6"
            }`}
          >
            Detect AI-Generated{" "}
            <span className="gradient-text">Fraud in Banking</span>{" "}
            Before It Strikes
          </h1>

          {/* Sub */}
          <p
            className={`mx-auto mt-6 max-w-2xl text-lg leading-relaxed text-slate-400 transition-all duration-700 delay-200 ${
              mounted ? "opacity-100 translate-y-0" : "opacity-0 translate-y-6"
            }`}
          >
            SentinelAI combines stylometric analysis, GPT-2 perplexity scoring,
            and deep learning to identify AI-generated phishing emails, deepfake
            documents, and manipulated images — with full explainability.
          </p>

          {/* CTA */}
          <div
            className={`mt-10 flex flex-col items-center gap-4 sm:flex-row sm:justify-center transition-all duration-700 delay-300 ${
              mounted ? "opacity-100 translate-y-0" : "opacity-0 translate-y-6"
            }`}
          >
            <Link
              href="/dashboard"
              className="btn-primary px-8 py-3 text-base"
            >
              Launch Dashboard
              <ArrowRight />
            </Link>
            <a href="#features" className="btn-ghost text-base">
              Explore Features
            </a>
          </div>
        </div>

        {/* Stats row */}
        <div
          className={`mx-auto mt-20 grid max-w-2xl grid-cols-3 gap-8 transition-all duration-700 delay-500 ${
            mounted ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"
          }`}
        >
          <StatCounter value="97.3" suffix="%" label="Detection Accuracy" />
          <StatCounter value="<2" suffix="s" label="Analysis Speed" />
          <StatCounter value="4" suffix="" label="Risk Levels" />
        </div>
      </section>

      {/* ── Features ────────────────────────────────────────────────── */}
      <section id="features" className="relative z-10 mx-auto max-w-7xl px-6 py-24">
        <div className="mb-14 text-center">
          <h2 className="text-3xl font-bold text-white sm:text-4xl">
            Multi-Layer Detection Engine
          </h2>
          <p className="mx-auto mt-4 max-w-xl text-slate-400">
            A comprehensive pipeline that analyses text, images, and documents
            through multiple AI detection layers.
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          <FeatureCard
            icon={<ScanIcon />}
            title="Text Analysis"
            description="Stylometric profiling, sentence variance analysis, and GPT-2 perplexity scoring detect AI-written communications with high precision."
            delay={100}
          />
          <FeatureCard
            icon={<ImageIcon />}
            title="Deepfake Detection"
            description="CNN-based image analysis identifies AI-generated or manipulated images, including GAN artefacts and synthetic face detection."
            delay={200}
          />
          <FeatureCard
            icon={<FileTextIcon />}
            title="Document Scanning"
            description="PDF text extraction combined with full text analysis pipeline for detecting fraudulent documents and forged communications."
            delay={300}
          />
          <FeatureCard
            icon={<BrainIcon />}
            title="Explainable AI"
            description="Every detection comes with a detailed explanation — which features triggered, why the risk level was assigned, and actionable recommendations."
            delay={400}
          />
          <FeatureCard
            icon={<ChartIcon />}
            title="Risk Scoring"
            description="Four-tier risk classification (LOW → CRITICAL) combining AI probability with fraud-intent signals like urgency, redirection, and impersonation."
            delay={500}
          />
          <FeatureCard
            icon={<ShieldIcon />}
            title="Audit Trail"
            description="Every analysis is logged with full results. Filter by risk level, type, or date — ensuring compliance and investigative traceability."
            delay={600}
          />
        </div>
      </section>

      {/* ── How It Works ────────────────────────────────────────────── */}
      <section id="how-it-works" className="relative z-10 mx-auto max-w-7xl px-6 py-24">
        <div className="mb-14 text-center">
          <h2 className="text-3xl font-bold text-white sm:text-4xl">
            How It Works
          </h2>
          <p className="mx-auto mt-4 max-w-xl text-slate-400">
            From input to explainable result in milliseconds.
          </p>
        </div>

        <div className="mx-auto grid max-w-4xl gap-0 md:grid-cols-4">
          {[
            { step: "01", title: "Input", desc: "Paste text, upload an image, or submit a PDF document." },
            { step: "02", title: "Analyse", desc: "Multi-layer AI pipeline extracts features and runs classification." },
            { step: "03", title: "Score", desc: "Fraud risk engine combines AI detection with intent-based signals." },
            { step: "04", title: "Explain", desc: "Get a detailed, human-readable report with highlighted risks." },
          ].map((item, i) => (
            <div key={i} className="relative flex flex-col items-center px-4 py-8 text-center">
              {/* Connector line */}
              {i < 3 && (
                <div className="absolute right-0 top-1/2 hidden h-px w-full -translate-y-1/2 bg-gradient-to-r from-transparent via-sentinel-500/30 to-transparent md:block" />
              )}
              <div className="relative z-10 mb-4 flex h-12 w-12 items-center justify-center rounded-full border border-sentinel-500/30 bg-sentinel-600/15 text-sm font-bold text-sentinel-400">
                {item.step}
              </div>
              <h3 className="mb-2 text-base font-semibold text-white">{item.title}</h3>
              <p className="text-sm text-slate-500">{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── CTA Bar ─────────────────────────────────────────────────── */}
      <section className="relative z-10 mx-auto max-w-7xl px-6 pb-32">
        <div className="glass-card flex flex-col items-center gap-6 px-8 py-12 text-center md:flex-row md:justify-between md:text-left">
          <div>
            <h3 className="text-2xl font-bold text-white">
              Ready to protect your institution?
            </h3>
            <p className="mt-2 text-slate-400">
              Start analysing communications for AI-generated fraud right now.
            </p>
          </div>
          <Link href="/dashboard" className="btn-primary shrink-0 px-8 py-3 text-base">
            Open Dashboard
            <ArrowRight />
          </Link>
        </div>
      </section>

      {/* ── Footer ──────────────────────────────────────────────────── */}
      <footer className="relative z-10 border-t border-white/[0.04] py-8">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6">
          <div className="flex items-center gap-2 text-sm text-slate-600">
            <ShieldIcon />
            <span>SentinelAI</span>
          </div>
          <p className="text-xs text-slate-700">
            Hackathon Prototype &middot; 2026
          </p>
        </div>
      </footer>
    </div>
  );
}

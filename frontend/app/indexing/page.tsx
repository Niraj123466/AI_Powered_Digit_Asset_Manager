"use client";

import React, { useState, useEffect } from "react";
import {
  Database,
  Play,
  RotateCcw,
  RefreshCw,
  AlertCircle,
  CheckCircle2,
  Clock,
  Cpu,
  Layers,
  HardDrive,
  Activity,
  FileCheck,
  FileX,
  Copy,
  Sliders,
  Sparkles,
} from "lucide-react";
import { api, IndexStatus } from "@/lib/api";

export default function IndexingPage() {
  const [status, setStatus] = useState<IndexStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  const fetchStatus = async () => {
    try {
      const data = await api.getIndexStatus();
      setStatus(data);
    } catch (e) {
      console.error("Failed to fetch index status:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    let timer: NodeJS.Timeout;
    const scheduleNext = (delay: number) => {
      timer = setTimeout(async () => {
        if (typeof document !== "undefined" && document.hidden) {
          scheduleNext(10000);
          return;
        }
        try {
          const data = await api.getIndexStatus();
          setStatus(data);
          scheduleNext(data?.running ? 2500 : 10000);
        } catch {
          scheduleNext(15000);
        }
      }, delay);
    };
    scheduleNext(3000);
    return () => clearTimeout(timer);
  }, []);

  const handleStartIndexing = async () => {
    setActionLoading(true);
    setActionMessage(null);
    try {
      const res = await api.startIndexing();
      setActionMessage(res.message || "Indexing pipeline started");
      await fetchStatus();
    } catch (e) {
      setActionMessage("Failed to start indexing pipeline");
    } finally {
      setActionLoading(false);
    }
  };

  const handleRetryFailed = async () => {
    setActionLoading(true);
    setActionMessage(null);
    try {
      const res = await api.retryFailed();
      setActionMessage(res.message || "Retrying failed jobs");
      await fetchStatus();
    } catch (e) {
      setActionMessage("Failed to trigger retries");
    } finally {
      setActionLoading(false);
    }
  };

  const isRunning = status?.running;
  const stats = status?.stats;
  const totalNew = stats?.total_new || 0;
  const processed = stats?.total_processed || 0;
  const progressPercent = totalNew > 0 ? Math.min(100, Math.round((processed / totalNew) * 100)) : 0;

  return (
    <div className="space-y-8">
      {/* Page Title & Status */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-white/10 pb-5">
        <div>
          <h1 className="text-xl md:text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
            <Database className="h-5 w-5 text-primary" />
            <span>Ingestion & Indexing Pipeline</span>
          </h1>
          <p className="text-xs text-muted-foreground mt-1">
            Real-time file scanning, SHA-256 deduplication, multimodal AI processing, and Qdrant vector sync
          </p>
        </div>

        {/* Global Action Triggers */}
        <div className="flex items-center gap-2">
          <button
            onClick={handleRetryFailed}
            disabled={actionLoading || isRunning}
            className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg bg-obsidian-900 hover:bg-obsidian-850 text-white text-xs font-medium border border-white/10 transition-colors disabled:opacity-40"
          >
            <RotateCcw className="h-3.5 w-3.5 text-amber-400" />
            <span>Retry Failed</span>
          </button>

          <button
            onClick={fetchStatus}
            className="p-2 rounded-lg bg-obsidian-900 border border-white/10 text-muted-foreground hover:text-white transition-colors"
            title="Refresh status"
          >
            <RefreshCw className="h-4 w-4" />
          </button>

          <button
            onClick={handleStartIndexing}
            disabled={actionLoading || isRunning}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-primary hover:bg-primary/90 text-white text-xs font-medium transition-colors shadow-glow-primary disabled:opacity-50 disabled:pointer-events-none"
          >
            <Play className={`h-3.5 w-3.5 ${actionLoading || isRunning ? "animate-spin" : "fill-current"}`} />
            <span>{isRunning ? "Pipeline Active..." : "Run Ingestion"}</span>
          </button>
        </div>
      </div>

      {actionMessage && (
        <div className="p-3 rounded-lg bg-primary/10 border border-primary/30 text-xs font-mono text-primary flex items-center gap-2">
          <Sparkles className="h-4 w-4" />
          <span>{actionMessage}</span>
        </div>
      )}

      {/* Main Pipeline Progress Card */}
      <div className="rounded-2xl bg-obsidian-900 border border-white/10 p-6 space-y-6 top-bevel">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div
              className={`h-12 w-12 rounded-xl flex items-center justify-center border ${
                isRunning
                  ? "bg-cyan/15 border-cyan/40 text-cyan animate-pulse"
                  : "bg-emerald-500/10 border-emerald-500/30 text-emerald-400"
              }`}
            >
              {isRunning ? <Cpu className="h-6 w-6 animate-spin" /> : <CheckCircle2 className="h-6 w-6" />}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-semibold text-white">
                  {isRunning ? "Ingestion Engine In Progress" : "Pipeline Idle & Synced"}
                </h3>
                <span
                  className={`text-[10px] font-mono px-2 py-0.5 rounded uppercase font-semibold ${
                    isRunning
                      ? "bg-cyan/20 text-cyan border border-cyan/40"
                      : "bg-emerald-500/20 text-emerald-400 border border-emerald-500/40"
                  }`}
                >
                  {isRunning ? "Running" : "Idle"}
                </span>
              </div>
              <p className="text-xs text-muted-foreground font-mono mt-1">
                {stats?.current_file ? (
                  <>
                    Processing: <span className="text-white">{stats.current_file}</span>
                    {stats?.current_stage && ` [${stats.current_stage}]`}
                  </>
                ) : (
                  "All discovered media files in MEDIA_ROOT have been processed"
                )}
              </p>
            </div>
          </div>

          <div className="text-right">
            <span className="text-3xl font-bold font-mono text-white">{progressPercent}%</span>
            <p className="text-xs font-mono text-muted-foreground">
              {processed} of {totalNew} items processed
            </p>
          </div>
        </div>

        {/* Progress Track */}
        <div className="space-y-2">
          <div className="h-3 w-full bg-obsidian-950 rounded-full overflow-hidden border border-white/10 p-0.5">
            <div
              className={`h-full rounded-full transition-all duration-500 ${
                isRunning
                  ? "bg-gradient-to-r from-primary to-cyan animate-pulse"
                  : "bg-emerald-500"
              }`}
              style={{ width: `${Math.max(3, progressPercent)}%` }}
            />
          </div>

          {/* Pipeline Stage Indicators */}
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 pt-2 text-[11px] font-mono">
            <div className="p-2 rounded bg-obsidian-950 border border-white/5 text-center">
              <span className="text-muted-foreground block text-[10px]">1. SCAN</span>
              <span className="text-white font-medium">SHA-256 Hash</span>
            </div>
            <div className="p-2 rounded bg-obsidian-950 border border-white/5 text-center">
              <span className="text-muted-foreground block text-[10px]">2. DEDUPLICATE</span>
              <span className="text-white font-medium">Exact Match</span>
            </div>
            <div className="p-2 rounded bg-obsidian-950 border border-white/5 text-center">
              <span className="text-muted-foreground block text-[10px]">3. EXTRACT</span>
              <span className="text-white font-medium">EXIF & Frames</span>
            </div>
            <div className="p-2 rounded bg-obsidian-950 border border-white/5 text-center">
              <span className="text-muted-foreground block text-[10px]">4. AI UNDERSTAND</span>
              <span className="text-white font-medium">CLIP + LLaVA</span>
            </div>
            <div className="p-2 rounded bg-obsidian-950 border border-white/5 text-center">
              <span className="text-muted-foreground block text-[10px]">5. SYNC</span>
              <span className="text-white font-medium">Qdrant Vectors</span>
            </div>
          </div>
        </div>
      </div>

      {/* Metrics Breakdown Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        <div className="p-4 rounded-xl bg-obsidian-900 border border-white/10 top-bevel">
          <span className="text-[10px] font-mono uppercase text-muted-foreground block">
            Discovered
          </span>
          <span className="text-2xl font-bold font-mono text-white mt-1 block">
            {stats?.total_discovered ?? 0}
          </span>
          <span className="text-[10px] font-mono text-muted-foreground">Files on disk</span>
        </div>

        <div className="p-4 rounded-xl bg-obsidian-900 border border-white/10 top-bevel">
          <span className="text-[10px] font-mono uppercase text-muted-foreground block">
            New Items
          </span>
          <span className="text-2xl font-bold font-mono text-cyan mt-1 block">
            {stats?.total_new ?? 0}
          </span>
          <span className="text-[10px] font-mono text-muted-foreground">Unique content</span>
        </div>

        <div className="p-4 rounded-xl bg-obsidian-900 border border-white/10 top-bevel">
          <span className="text-[10px] font-mono uppercase text-muted-foreground block">
            Processed
          </span>
          <span className="text-2xl font-bold font-mono text-emerald-400 mt-1 block">
            {stats?.total_processed ?? 0}
          </span>
          <span className="text-[10px] font-mono text-muted-foreground">Indexed in DB</span>
        </div>

        <div className="p-4 rounded-xl bg-obsidian-900 border border-white/10 top-bevel">
          <span className="text-[10px] font-mono uppercase text-muted-foreground block">
            Duplicates
          </span>
          <span className="text-2xl font-bold font-mono text-purple-400 mt-1 block">
            {stats?.total_duplicates ?? 0}
          </span>
          <span className="text-[10px] font-mono text-muted-foreground">Reused embeddings</span>
        </div>

        <div className="p-4 rounded-xl bg-obsidian-900 border border-white/10 top-bevel">
          <span className="text-[10px] font-mono uppercase text-muted-foreground block">
            Failed
          </span>
          <span className="text-2xl font-bold font-mono text-red-400 mt-1 block">
            {stats?.total_failed ?? 0}
          </span>
          <span className="text-[10px] font-mono text-muted-foreground">Needs review</span>
        </div>

        <div className="p-4 rounded-xl bg-obsidian-900 border border-white/10 top-bevel">
          <span className="text-[10px] font-mono uppercase text-muted-foreground block">
            Skipped
          </span>
          <span className="text-2xl font-bold font-mono text-white/60 mt-1 block">
            {stats?.total_skipped ?? 0}
          </span>
          <span className="text-[10px] font-mono text-muted-foreground">Unchanged files</span>
        </div>
      </div>

      {/* Engine Parameters & Pipeline Settings */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Worker Configuration */}
        <div className="rounded-xl bg-obsidian-900 border border-white/10 p-5 space-y-3 top-bevel">
          <h3 className="text-xs font-mono uppercase tracking-wider text-muted-foreground flex items-center gap-2 border-b border-white/5 pb-2">
            <Sliders className="h-4 w-4 text-primary" />
            <span>Worker & Pipeline Tuning</span>
          </h3>

          <div className="space-y-2.5 text-xs font-mono">
            <div className="flex justify-between items-center text-muted-foreground">
              <span>Parallel Ingestion Workers:</span>
              <span className="text-white px-2 py-0.5 rounded bg-white/5">2 Workers</span>
            </div>
            <div className="flex justify-between items-center text-muted-foreground">
              <span>Video Frame Sampling Interval:</span>
              <span className="text-white px-2 py-0.5 rounded bg-white/5">5 Seconds</span>
            </div>
            <div className="flex justify-between items-center text-muted-foreground">
              <span>Video Maximum Sampled Frames:</span>
              <span className="text-white px-2 py-0.5 rounded bg-white/5">64 Frames Cap</span>
            </div>
            <div className="flex justify-between items-center text-muted-foreground">
              <span>OCR Text Extraction:</span>
              <span className="text-emerald-400 px-2 py-0.5 rounded bg-emerald-500/10">Enabled (300 DPI)</span>
            </div>
            <div className="flex justify-between items-center text-muted-foreground">
              <span>Audio Transcription:</span>
              <span className="text-white/60 px-2 py-0.5 rounded bg-white/5">Disabled (faster-whisper)</span>
            </div>
          </div>
        </div>

        {/* AI Model Architecture */}
        <div className="rounded-xl bg-obsidian-900 border border-white/10 p-5 space-y-3 top-bevel">
          <h3 className="text-xs font-mono uppercase tracking-wider text-muted-foreground flex items-center gap-2 border-b border-white/5 pb-2">
            <Cpu className="h-4 w-4 text-cyan" />
            <span>AI Model Architecture</span>
          </h3>

          <div className="space-y-2.5 text-xs font-mono">
            <div className="flex justify-between items-center text-muted-foreground">
              <span>Multimodal Embedding Model:</span>
              <span className="text-white px-2 py-0.5 rounded bg-white/5">clip-ViT-B-32 (512-dim)</span>
            </div>
            <div className="flex justify-between items-center text-muted-foreground">
              <span>Vision Language Model:</span>
              <span className="text-white px-2 py-0.5 rounded bg-white/5">llava:7b via Ollama</span>
            </div>
            <div className="flex justify-between items-center text-muted-foreground">
              <span>Document Summarization Model:</span>
              <span className="text-white px-2 py-0.5 rounded bg-white/5">llama3.1:8b via Ollama</span>
            </div>
            <div className="flex justify-between items-center text-muted-foreground">
              <span>Search Score Weights:</span>
              <span className="text-cyan px-2 py-0.5 rounded bg-cyan/10">60% Semantic / 20% Lexical</span>
            </div>
            <div className="flex justify-between items-center text-muted-foreground">
              <span>Hardware Acceleration:</span>
              <span className="text-emerald-400 px-2 py-0.5 rounded bg-emerald-500/10">Auto-Detect GPU/MPS</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
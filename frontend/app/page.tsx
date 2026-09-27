"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  LayoutDashboard,
  Search,
  Layers,
  Database,
  Image as ImageIcon,
  Video,
  FileText,
  Sparkles,
  ArrowRight,
  RefreshCw,
  AlertCircle,
  CheckCircle2,
  Clock,
  HardDrive,
  Cpu,
  ChevronRight,
  Zap,
} from "lucide-react";
import { api, Stats, IndexStatus, Asset } from "@/lib/api";
import { AssetCard } from "@/components/assets/AssetCard";
import { Skeleton } from "@/components/ui/skeleton";

export default function DashboardPage() {
  const router = useRouter();
  const [stats, setStats] = useState<Stats | null>(null);
  const [indexStatus, setIndexStatus] = useState<IndexStatus | null>(null);
  const [recentAssets, setRecentAssets] = useState<Asset[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [isStartingIndex, setIsStartingIndex] = useState(false);

  const fetchDashboardData = async () => {
    try {
      const [statsData, statusData, assetsData] = await Promise.all([
        api.getStats().catch(() => null),
        api.getIndexStatus().catch(() => null),
        api.listAssets({ limit: 8 }).catch(() => ({ assets: [], total: 0 })),
      ]);

      if (statsData) setStats(statsData);
      if (statusData) setIndexStatus(statusData);
      if (assetsData?.assets) setRecentAssets(assetsData.assets);
    } catch (e) {
      console.error("Dashboard data load error:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();

    // Only periodically check index status and refresh if running
    const interval = setInterval(async () => {
      if (typeof document !== "undefined" && document.hidden) return;
      try {
        const statusData = await api.getIndexStatus().catch(() => null);
        if (statusData) {
          setIndexStatus(statusData);
          if (statusData.running) {
            const statsData = await api.getStats().catch(() => null);
            if (statsData) setStats(statsData);
          }
        }
      } catch (e) {
        // quiet
      }
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const handleStartIndexing = async () => {
    setIsStartingIndex(true);
    try {
      await api.startIndexing();
      await fetchDashboardData();
    } catch (e) {
      console.error("Failed to start indexing:", e);
    } finally {
      setIsStartingIndex(false);
    }
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      router.push(`/search?q=${encodeURIComponent(searchQuery.trim())}`);
    } else {
      router.push("/search");
    }
  };

  const promptStarters = [
    { label: "Modern living room interior", query: "modern living room interior", modality: "image" },
    { label: "Construction site activity", query: "construction workers on site", modality: "video" },
    { label: "Residential project brochure", query: "residential project brochure", modality: "document" },
    { label: "Apartment floor plan", query: "apartment floor plan", modality: "document" },
  ];

  const isIndexing = indexStatus?.running;
  const progressPercent =
    indexStatus?.stats?.total_new && indexStatus.stats.total_new > 0
      ? Math.min(100, Math.round((indexStatus.stats.total_processed / indexStatus.stats.total_new) * 100))
      : 0;

  return (
    <div className="space-y-8">
      {/* Top Banner / Hero */}
      <div className="relative rounded-2xl bg-gradient-to-r from-obsidian-900 via-obsidian-850 to-obsidian-900 border border-white/10 p-6 md:p-8 overflow-hidden top-bevel">
        <div className="absolute top-0 right-0 -mt-10 -mr-10 h-72 w-72 rounded-full bg-primary/10 blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 right-1/4 -mb-10 h-60 w-60 rounded-full bg-cyan/10 blur-3xl pointer-events-none" />

        <div className="relative z-10 max-w-3xl space-y-4">
          <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-white/5 border border-white/10 text-xs font-mono text-muted-foreground">
            <span className="flex h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
            <span>Multimodal Vector Engine Online</span>
            <span className="text-white/20">•</span>
            <span className="text-primary font-medium">CLIP + Qdrant</span>
          </div>

          <h1 className="text-2xl md:text-4xl font-bold tracking-tight text-white">
            Digital Asset Studio & <span className="text-gradient-indigo">Semantic Explorer</span>
          </h1>

          <p className="text-sm md:text-base text-muted-foreground leading-relaxed">
            Index, process, and query photos, footage, and blueprints with multimodal AI understanding.
            Search across visual concepts, spoken audio, and document text in milliseconds.
          </p>

          {/* Quick Search Bar */}
          <form onSubmit={handleSearchSubmit} className="pt-2">
            <div className="relative max-w-2xl flex items-center">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Ask anything (e.g. 'luxury bedroom design', 'workers on site')..."
                className="w-full h-12 pl-12 pr-28 rounded-xl bg-obsidian-950/90 border border-white/15 text-sm text-foreground placeholder:text-muted-foreground/70 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary shadow-2xl transition-all top-bevel"
              />
              <button
                type="submit"
                className="absolute right-2 top-1/2 -translate-y-1/2 h-8 px-4 rounded-lg bg-primary hover:bg-primary/90 text-white text-xs font-medium transition-colors shadow-glow-primary flex items-center gap-1.5"
              >
                <span>Search</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </button>
            </div>
          </form>

          {/* Prompt Starters */}
          <div className="flex flex-wrap items-center gap-2 pt-1 text-xs">
            <span className="text-[11px] font-mono text-muted-foreground/70 mr-1">Suggested:</span>
            {promptStarters.map((item) => (
              <button
                key={item.label}
                type="button"
                onClick={() => router.push(`/search?q=${encodeURIComponent(item.query)}&modality=${item.modality}`)}
                className="px-2.5 py-1 rounded-md bg-white/5 hover:bg-white/10 text-muted-foreground hover:text-white border border-white/5 text-[11px] font-mono transition-colors flex items-center gap-1.5"
              >
                <Sparkles className="h-3 w-3 text-primary" />
                <span>{item.label}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Live Indexing Telemetry Banner (if active) */}
      {isIndexing && (
        <div className="rounded-xl bg-cyan/10 border border-cyan/30 p-4 flex flex-col md:flex-row md:items-center justify-between gap-4 animate-pulse-subtle">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-lg bg-cyan/20 border border-cyan/40 flex items-center justify-center flex-shrink-0">
              <Cpu className="h-5 w-5 text-cyan animate-spin" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-sm font-semibold text-white">Ingestion Pipeline Running</h3>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan/20 text-cyan">
                  {progressPercent}% Complete
                </span>
              </div>
              <p className="text-xs text-muted-foreground font-mono mt-0.5">
                Current file: <span className="text-white">{indexStatus?.stats?.current_file || "Processing batch"}</span>
                {indexStatus?.stats?.current_stage && ` (${indexStatus.stats.current_stage})`}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="w-48 bg-black/40 h-2 rounded-full overflow-hidden border border-white/10 hidden sm:block">
              <div
                className="bg-cyan h-full transition-all duration-300"
                style={{ width: `${progressPercent}%` }}
              />
            </div>
            <Link
              href="/indexing"
              className="px-3 py-1.5 rounded-lg bg-cyan/20 hover:bg-cyan/30 text-cyan border border-cyan/30 text-xs font-mono transition-colors flex items-center gap-1.5"
            >
              <span>View Queue</span>
              <ChevronRight className="h-3.5 w-3.5" />
            </Link>
          </div>
        </div>
      )}

      {/* Telemetry KPI Ribbon */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* Card 1: Total Catalog Assets */}
        <div className="rounded-xl bg-obsidian-900 border border-white/10 p-5 top-bevel hover:border-white/20 transition-all">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-muted-foreground uppercase tracking-wider">
              Catalog Scale
            </span>
            <div className="p-2 rounded-lg bg-primary/10 border border-primary/20 text-primary">
              <Layers className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-3">
            <span className="text-2xl md:text-3xl font-bold font-mono text-white">
              {loading ? <Skeleton className="h-8 w-16" /> : stats?.total_assets ?? 0}
            </span>
            <p className="text-[11px] font-mono text-muted-foreground mt-1 flex items-center gap-1.5">
              <span className="text-emerald-400">●</span>
              <span>{stats?.indexed ?? 0} indexed in Qdrant</span>
            </p>
          </div>
        </div>

        {/* Card 2: Imagery & Stills */}
        <div className="rounded-xl bg-obsidian-900 border border-white/10 p-5 top-bevel hover:border-white/20 transition-all">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-muted-foreground uppercase tracking-wider">
              Stills & Graphics
            </span>
            <div className="p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
              <ImageIcon className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-3">
            <span className="text-2xl md:text-3xl font-bold font-mono text-white">
              {loading ? <Skeleton className="h-8 w-16" /> : stats?.images ?? 0}
            </span>
            <p className="text-[11px] font-mono text-muted-foreground mt-1">
              Visual CLIP & OCR embeddings
            </p>
          </div>
        </div>

        {/* Card 3: Video Clips */}
        <div className="rounded-xl bg-obsidian-900 border border-white/10 p-5 top-bevel hover:border-white/20 transition-all">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-muted-foreground uppercase tracking-wider">
              Footage & Video
            </span>
            <div className="p-2 rounded-lg bg-purple-500/10 border border-purple-500/20 text-purple-400">
              <Video className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-3">
            <span className="text-2xl md:text-3xl font-bold font-mono text-white">
              {loading ? <Skeleton className="h-8 w-16" /> : stats?.videos ?? 0}
            </span>
            <p className="text-[11px] font-mono text-muted-foreground mt-1">
              Adaptive sampling up to 64 frames
            </p>
          </div>
        </div>

        {/* Card 4: Documents & Blueprints */}
        <div className="rounded-xl bg-obsidian-900 border border-white/10 p-5 top-bevel hover:border-white/20 transition-all">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-muted-foreground uppercase tracking-wider">
              PDFs & Blueprints
            </span>
            <div className="p-2 rounded-lg bg-blue-500/10 border border-blue-500/20 text-blue-400">
              <FileText className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-3">
            <span className="text-2xl md:text-3xl font-bold font-mono text-white">
              {loading ? <Skeleton className="h-8 w-16" /> : stats?.documents ?? 0}
            </span>
            <p className="text-[11px] font-mono text-muted-foreground mt-1">
              PyMuPDF page chunks + LLM summaries
            </p>
          </div>
        </div>
      </div>

      {/* Main Section: Recent Media Explorer */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-white tracking-tight flex items-center gap-2">
              <Layers className="h-4 w-4 text-primary" />
              <span>Catalog Assets</span>
            </h2>
            <p className="text-xs text-muted-foreground">
              Recently indexed assets in local media repository
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={fetchDashboardData}
              className="p-2 rounded-lg bg-white/5 hover:bg-white/10 text-muted-foreground hover:text-white border border-white/10 transition-colors"
              title="Refresh Catalog"
            >
              <RefreshCw className="h-3.5 w-3.5" />
            </button>
            <Link
              href="/assets"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-white text-xs font-medium border border-white/10 transition-colors"
            >
              <span>View All</span>
              <ChevronRight className="h-3.5 w-3.5" />
            </Link>
          </div>
        </div>

        {/* Asset Grid */}
        {loading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {[...Array(8)].map((_, i) => (
              <div key={i} className="rounded-xl bg-obsidian-900 border border-white/10 p-3 space-y-3">
                <Skeleton className="aspect-video w-full rounded-lg" />
                <Skeleton className="h-4 w-3/4 rounded" />
                <Skeleton className="h-3 w-1/2 rounded" />
              </div>
            ))}
          </div>
        ) : recentAssets.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {recentAssets.map((asset) => (
              <AssetCard key={asset.id} asset={asset} showScore={false} />
            ))}
          </div>
        ) : (
          <div className="rounded-xl bg-obsidian-900 border border-white/10 p-12 text-center space-y-4">
            <div className="h-12 w-12 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center mx-auto text-muted-foreground">
              <Database className="h-6 w-6 text-primary" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-white">No assets indexed yet</h3>
              <p className="text-xs text-muted-foreground max-w-sm mx-auto mt-1">
                Your media files in <code className="text-white font-mono text-[11px]">data/media</code> are ready to be ingested.
              </p>
            </div>
            <button
              onClick={handleStartIndexing}
              disabled={isStartingIndex}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-primary hover:bg-primary/90 text-white text-xs font-medium shadow-glow-primary transition-colors"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${isStartingIndex ? "animate-spin" : ""}`} />
              <span>{isStartingIndex ? "Starting Ingestion..." : "Start Initial Ingestion"}</span>
            </button>
          </div>
        )}
      </div>

      {/* Infrastructure & Pipeline Telemetry */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 pt-2">
        <div className="rounded-xl bg-obsidian-900 border border-white/10 p-5 top-bevel space-y-3">
          <div className="flex items-center justify-between border-b border-white/5 pb-3">
            <h3 className="text-xs font-mono uppercase tracking-wider text-muted-foreground flex items-center gap-2">
              <HardDrive className="h-3.5 w-3.5 text-primary" />
              <span>Relational Storage</span>
            </h3>
            <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              Active
            </span>
          </div>
          <div className="space-y-2 text-xs font-mono">
            <div className="flex justify-between text-muted-foreground">
              <span>Engine:</span>
              <span className="text-white">PostgreSQL 16</span>
            </div>
            <div className="flex justify-between text-muted-foreground">
              <span>Schema:</span>
              <span className="text-white">14 Tables • alembic v1</span>
            </div>
            <div className="flex justify-between text-muted-foreground">
              <span>Deduplication:</span>
              <span className="text-white">SHA-256 Hash Matching</span>
            </div>
          </div>
        </div>

        <div className="rounded-xl bg-obsidian-900 border border-white/10 p-5 top-bevel space-y-3">
          <div className="flex items-center justify-between border-b border-white/5 pb-3">
            <h3 className="text-xs font-mono uppercase tracking-wider text-muted-foreground flex items-center gap-2">
              <Cpu className="h-3.5 w-3.5 text-cyan" />
              <span>Vector Database</span>
            </h3>
            <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-cyan/10 text-cyan border border-cyan/20">
              Ready
            </span>
          </div>
          <div className="space-y-2 text-xs font-mono">
            <div className="flex justify-between text-muted-foreground">
              <span>Engine:</span>
              <span className="text-white">Qdrant v1.10.0</span>
            </div>
            <div className="flex justify-between text-muted-foreground">
              <span>Collections:</span>
              <span className="text-white">dam_assets_image, video, doc</span>
            </div>
            <div className="flex justify-between text-muted-foreground">
              <span>Dimensions:</span>
              <span className="text-white">512-dim (CLIP ViT-B-32)</span>
            </div>
          </div>
        </div>

        <div className="rounded-xl bg-obsidian-900 border border-white/10 p-5 top-bevel space-y-3">
          <div className="flex items-center justify-between border-b border-white/5 pb-3">
            <h3 className="text-xs font-mono uppercase tracking-wider text-muted-foreground flex items-center gap-2">
              <Zap className="h-3.5 w-3.5 text-amber-400" />
              <span>AI Provider Suite</span>
            </h3>
            <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-amber-400/10 text-amber-400 border border-amber-400/20">
              Local Mode
            </span>
          </div>
          <div className="space-y-2 text-xs font-mono">
            <div className="flex justify-between text-muted-foreground">
              <span>Embeddings:</span>
              <span className="text-white">SentenceTransformers</span>
            </div>
            <div className="flex justify-between text-muted-foreground">
              <span>OCR:</span>
              <span className="text-white">Tesseract (DPI 300)</span>
            </div>
            <div className="flex justify-between text-muted-foreground">
              <span>Vision/LLM:</span>
              <span className="text-white">Ollama (LLaVA / LLaMA 3.1)</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
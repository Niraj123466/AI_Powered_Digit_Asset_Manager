"use client";

import React, { useState, useEffect, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import {
  Layers,
  Image as ImageIcon,
  Video,
  FileText,
  LayoutGrid,
  List,
  Search,
  ChevronLeft,
  ChevronRight,
  RefreshCw,
  Filter,
} from "lucide-react";
import { api, Asset } from "@/lib/api";
import { AssetCard } from "@/components/assets/AssetCard";
import { AssetListItem } from "@/components/assets/AssetListItem";
import { Skeleton } from "@/components/ui/skeleton";

function AssetsCatalogContent() {
  const searchParams = useSearchParams();
  const router = useRouter();

  const [assets, setAssets] = useState<Asset[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [modality, setModality] = useState(searchParams.get("modality") || "");
  const [state, setState] = useState(searchParams.get("state") || "");
  const [filterText, setFilterText] = useState("");
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");
  const [page, setPage] = useState(1);
  const limit = 24;

  const fetchAssets = async () => {
    setLoading(true);
    try {
      const data = await api.listAssets({
        modality: modality || undefined,
        state: state || undefined,
        limit,
        offset: (page - 1) * limit,
      });
      setAssets(data.assets || []);
      setTotal(data.total || 0);
    } catch (e) {
      console.error("Failed to load assets:", e);
      setAssets([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAssets();
  }, [modality, state, page]);

  const handleModalityFilter = (mod: string) => {
    setModality(mod);
    setPage(1);
    const params = new URLSearchParams();
    if (mod) params.set("modality", mod);
    if (state) params.set("state", state);
    router.push(`/assets?${params.toString()}`);
  };

  const handleStateFilter = (st: string) => {
    setState(st);
    setPage(1);
    const params = new URLSearchParams();
    if (modality) params.set("modality", modality);
    if (st) params.set("state", st);
    router.push(`/assets?${params.toString()}`);
  };

  // Filter in-memory by filename if user types into filter box
  const filteredAssets = assets.filter((a) =>
    a.filename.toLowerCase().includes(filterText.toLowerCase().trim())
  );

  const totalPages = Math.ceil(total / limit);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-white/10 pb-5">
        <div>
          <h1 className="text-xl md:text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
            <Layers className="h-5 w-5 text-primary" />
            <span>Digital Media Library</span>
          </h1>
          <p className="text-xs text-muted-foreground mt-1">
            Browse, filter, and inspect all ingested files in the DAM catalog
          </p>
        </div>

        <div className="flex items-center gap-2">
          {/* View Mode Toggle */}
          <div className="flex items-center rounded-lg bg-obsidian-900 border border-white/10 p-0.5">
            <button
              onClick={() => setViewMode("grid")}
              className={`p-1.5 rounded-md text-xs transition-colors ${
                viewMode === "grid"
                  ? "bg-primary text-white shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              }`}
              title="Grid View"
            >
              <LayoutGrid className="h-4 w-4" />
            </button>
            <button
              onClick={() => setViewMode("list")}
              className={`p-1.5 rounded-md text-xs transition-colors ${
                viewMode === "list"
                  ? "bg-primary text-white shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              }`}
              title="List View"
            >
              <List className="h-4 w-4" />
            </button>
          </div>

          <button
            onClick={fetchAssets}
            className="p-2 rounded-lg bg-obsidian-900 border border-white/10 text-muted-foreground hover:text-white transition-colors"
            title="Refresh Catalog"
          >
            <RefreshCw className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3 bg-obsidian-900 p-3 rounded-xl border border-white/10 top-bevel">
        {/* Modality Tabs */}
        <div className="flex flex-wrap items-center gap-1.5">
          <button
            onClick={() => handleModalityFilter("")}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors border ${
              modality === ""
                ? "bg-primary text-white border-primary shadow-glow-primary"
                : "bg-obsidian-950 text-muted-foreground border-white/5 hover:border-white/20 hover:text-white"
            }`}
          >
            All Types
          </button>
          <button
            onClick={() => handleModalityFilter("image")}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors border ${
              modality === "image"
                ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/40"
                : "bg-obsidian-950 text-muted-foreground border-white/5 hover:border-white/20 hover:text-white"
            }`}
          >
            <ImageIcon className="h-3.5 w-3.5 text-emerald-400" />
            <span>Images</span>
          </button>
          <button
            onClick={() => handleModalityFilter("video")}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors border ${
              modality === "video"
                ? "bg-purple-500/20 text-purple-300 border-purple-500/40"
                : "bg-obsidian-950 text-muted-foreground border-white/5 hover:border-white/20 hover:text-white"
            }`}
          >
            <Video className="h-3.5 w-3.5 text-purple-400" />
            <span>Videos</span>
          </button>
          <button
            onClick={() => handleModalityFilter("document")}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors border ${
              modality === "document"
                ? "bg-blue-500/20 text-blue-300 border-blue-500/40"
                : "bg-obsidian-950 text-muted-foreground border-white/5 hover:border-white/20 hover:text-white"
            }`}
          >
            <FileText className="h-3.5 w-3.5 text-blue-400" />
            <span>Documents</span>
          </button>
        </div>

        {/* State Filter & Search */}
        <div className="flex items-center gap-2">
          {/* Quick Filter Input */}
          <div className="relative flex-1 md:w-56">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
            <input
              type="text"
              value={filterText}
              onChange={(e) => setFilterText(e.target.value)}
              placeholder="Filter by name..."
              className="w-full h-8 pl-8 pr-3 rounded-lg bg-obsidian-950 border border-white/10 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary"
            />
          </div>

          {/* State selector */}
          <select
            value={state}
            onChange={(e) => handleStateFilter(e.target.value)}
            className="h-8 px-2 rounded-lg bg-obsidian-950 border border-white/10 text-xs font-mono text-muted-foreground focus:outline-none focus:border-primary"
          >
            <option value="">All States</option>
            <option value="COMPLETED">Completed</option>
            <option value="PROCESSING">Processing</option>
            <option value="QUEUED">Queued</option>
            <option value="FAILED">Failed</option>
            <option value="DUPLICATE">Duplicates</option>
          </select>
        </div>
      </div>

      {/* Asset Display */}
      {loading ? (
        <div className={viewMode === "grid" ? "grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4" : "space-y-2"}>
          {[...Array(8)].map((_, i) => (
            viewMode === "grid" ? (
              <div key={i} className="rounded-xl bg-obsidian-900 border border-white/10 p-3 space-y-3">
                <Skeleton className="aspect-video w-full rounded-lg" />
                <Skeleton className="h-4 w-3/4 rounded" />
                <Skeleton className="h-3 w-1/2 rounded" />
              </div>
            ) : (
              <Skeleton key={i} className="h-16 w-full rounded-lg" />
            )
          ))}
        </div>
      ) : filteredAssets.length > 0 ? (
        <div className="space-y-6">
          {viewMode === "grid" ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {filteredAssets.map((asset) => (
                <AssetCard key={asset.id} asset={asset} showScore={false} />
              ))}
            </div>
          ) : (
            <div className="space-y-2">
              {filteredAssets.map((asset) => (
                <AssetListItem key={asset.id} asset={asset} showScore={false} />
              ))}
            </div>
          )}

          {/* Pagination */}
          {total > limit && (
            <div className="flex items-center justify-between border-t border-white/10 pt-4">
              <span className="text-xs font-mono text-muted-foreground">
                Showing {Math.min(total, (page - 1) * limit + 1)} - {Math.min(total, page * limit)} of {total} assets
              </span>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page <= 1}
                  className="px-3 py-1.5 rounded-lg bg-obsidian-900 hover:bg-obsidian-850 text-white text-xs font-medium border border-white/10 disabled:opacity-40 transition-colors flex items-center gap-1"
                >
                  <ChevronLeft className="h-3.5 w-3.5" />
                  <span>Previous</span>
                </button>
                <span className="text-xs font-mono text-muted-foreground px-2">
                  {page} / {totalPages}
                </span>
                <button
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page >= totalPages}
                  className="px-3 py-1.5 rounded-lg bg-obsidian-900 hover:bg-obsidian-850 text-white text-xs font-medium border border-white/10 disabled:opacity-40 transition-colors flex items-center gap-1"
                >
                  <span>Next</span>
                  <ChevronRight className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="rounded-xl bg-obsidian-900 border border-white/10 p-12 text-center space-y-4">
          <div className="h-12 w-12 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center mx-auto text-muted-foreground">
            <Layers className="h-6 w-6 text-primary" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white">No assets match criteria</h3>
            <p className="text-xs text-muted-foreground max-w-sm mx-auto mt-1">
              Try resetting filters or checking the indexing status to ensure files have been discovered.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

export default function AssetsPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-xs font-mono text-muted-foreground">Loading catalog...</div>}>
      <AssetsCatalogContent />
    </Suspense>
  );
}

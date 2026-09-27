"use client";

import React, { useState, useEffect, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import {
  Search,
  Image as ImageIcon,
  Video,
  FileText,
  LayoutGrid,
  List,
  Sparkles,
  ChevronLeft,
  ChevronRight,
  Loader2,
  X,
  Clock,
  Layers,
  Filter,
} from "lucide-react";
import { api, SearchResult } from "@/lib/api";
import { AssetCard } from "@/components/assets/AssetCard";
import { AssetListItem } from "@/components/assets/AssetListItem";
import { Skeleton } from "@/components/ui/skeleton";

function SearchContent() {
  const searchParams = useSearchParams();
  const router = useRouter();

  const initialQuery = searchParams.get("q") || "";
  const initialModality = searchParams.get("modality") || "";
  const initialLimit = Number(searchParams.get("limit")) || 20;

  const [query, setQuery] = useState(initialQuery);
  const [modality, setModality] = useState(initialModality);
  const [limit, setLimit] = useState(initialLimit);
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [total, setTotal] = useState(0);
  const [latency, setLatency] = useState(0);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [hasSearched, setHasSearched] = useState(false);

  // Execute search
  const performSearch = async (
    q: string,
    mod: string,
    lim: number,
    pageNum: number
  ) => {
    if (!q.trim()) {
      setResults([]);
      setTotal(0);
      setHasSearched(false);
      return;
    }

    setLoading(true);
    setHasSearched(true);

    try {
      const response = await api.search({
        query: q.trim(),
        modality: mod || undefined,
        limit: lim,
        offset: (pageNum - 1) * lim,
      });

      setResults(response.results || []);
      setTotal(response.total || 0);
      setLatency(response.latency_ms || 0);
    } catch (error) {
      console.error("Search failed:", error);
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  // Perform search on mount or when searchParams change
  useEffect(() => {
    if (initialQuery) {
      setQuery(initialQuery);
      setModality(initialModality);
      performSearch(initialQuery, initialModality, initialLimit, 1);
    }
  }, [searchParams]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    updateUrlParams(query, modality, limit, 1);
    performSearch(query, modality, limit, 1);
  };

  const updateUrlParams = (q: string, mod: string, lim: number, p: number) => {
    const params = new URLSearchParams();
    if (q) params.set("q", q);
    if (mod) params.set("modality", mod);
    if (lim !== 20) params.set("limit", lim.toString());
    if (p > 1) params.set("page", p.toString());
    router.push(`/search?${params.toString()}`);
  };

  const handleModalityChange = (newModality: string) => {
    setModality(newModality);
    setPage(1);
    updateUrlParams(query, newModality, limit, 1);
    if (query.trim()) {
      performSearch(query, newModality, limit, 1);
    }
  };

  const handlePageChange = (newPage: number) => {
    setPage(newPage);
    updateUrlParams(query, modality, limit, newPage);
    performSearch(query, modality, limit, newPage);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const promptStarters = [
    { label: "Modern living room interior", query: "modern living room interior", mod: "image" },
    { label: "Construction site & workers", query: "construction workers on site", mod: "video" },
    { label: "Apartment floor plan", query: "apartment floor plan", mod: "document" },
    { label: "Residential brochure", query: "residential project brochure", mod: "document" },
    { label: "Luxury bedroom design", query: "luxury bedroom design", mod: "image" },
  ];

  const totalPages = Math.ceil(total / limit);

  return (
    <div className="space-y-6">
      {/* Header & Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-white/10 pb-5">
        <div>
          <h1 className="text-xl md:text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
            <Sparkles className="h-5 w-5 text-primary" />
            <span>Semantic Asset Search</span>
          </h1>
          <p className="text-xs text-muted-foreground mt-1">
            Query across images, video keyframes, and document pages with CLIP vector similarity
          </p>
        </div>

        {/* View Mode Controls */}
        <div className="flex items-center gap-2">
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

          <select
            value={limit}
            onChange={(e) => {
              const newLimit = Number(e.target.value);
              setLimit(newLimit);
              if (query.trim()) performSearch(query, modality, newLimit, 1);
            }}
            className="h-8 px-2 rounded-lg bg-obsidian-900 border border-white/10 text-xs font-mono text-muted-foreground focus:outline-none focus:border-primary"
          >
            <option value={10}>10 per page</option>
            <option value={20}>20 per page</option>
            <option value={50}>50 per page</option>
          </select>
        </div>
      </div>

      {/* Omnibar Search Form */}
      <form onSubmit={handleSubmit} className="space-y-3">
        <div className="relative flex items-center">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Type your natural language query (e.g. 'building facade with glass', 'office workspace')..."
            className="w-full h-12 pl-12 pr-32 rounded-xl bg-obsidian-900 border border-white/10 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary shadow-xl transition-all top-bevel"
          />

          <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1.5">
            {query && (
              <button
                type="button"
                onClick={() => setQuery("")}
                className="p-1 rounded-md text-muted-foreground hover:text-white hover:bg-white/5 transition-colors"
                title="Clear query"
              >
                <X className="h-4 w-4" />
              </button>
            )}
            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="h-8 px-4 rounded-lg bg-primary hover:bg-primary/90 text-white text-xs font-medium transition-colors shadow-glow-primary flex items-center gap-1.5 disabled:opacity-50 disabled:pointer-events-none"
            >
              {loading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Search className="h-3.5 w-3.5" />}
              <span>{loading ? "Searching..." : "Search"}</span>
            </button>
          </div>
        </div>

        {/* Modality Filter Pills */}
        <div className="flex flex-wrap items-center justify-between gap-2 pt-1">
          <div className="flex flex-wrap items-center gap-1.5">
            <button
              type="button"
              onClick={() => handleModalityChange("")}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors border ${
                modality === ""
                  ? "bg-primary text-white border-primary shadow-glow-primary"
                  : "bg-obsidian-900 text-muted-foreground border-white/10 hover:border-white/20 hover:text-white"
              }`}
            >
              All Modalities
            </button>

            <button
              type="button"
              onClick={() => handleModalityChange("image")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors border ${
                modality === "image"
                  ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/40"
                  : "bg-obsidian-900 text-muted-foreground border-white/10 hover:border-white/20 hover:text-white"
              }`}
            >
              <ImageIcon className="h-3.5 w-3.5 text-emerald-400" />
              <span>Images</span>
            </button>

            <button
              type="button"
              onClick={() => handleModalityChange("video")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors border ${
                modality === "video"
                  ? "bg-purple-500/20 text-purple-300 border-purple-500/40"
                  : "bg-obsidian-900 text-muted-foreground border-white/10 hover:border-white/20 hover:text-white"
              }`}
            >
              <Video className="h-3.5 w-3.5 text-purple-400" />
              <span>Videos</span>
            </button>

            <button
              type="button"
              onClick={() => handleModalityChange("document")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors border ${
                modality === "document"
                  ? "bg-blue-500/20 text-blue-300 border-blue-500/40"
                  : "bg-obsidian-900 text-muted-foreground border-white/10 hover:border-white/20 hover:text-white"
              }`}
            >
              <FileText className="h-3.5 w-3.5 text-blue-400" />
              <span>Documents</span>
            </button>
          </div>

          {/* Telemetry pill */}
          {hasSearched && (
            <div className="flex items-center gap-2 text-xs font-mono text-muted-foreground">
              <span>{total} matches</span>
              <span>•</span>
              <span className="text-cyan">{latency}ms</span>
            </div>
          )}
        </div>
      </form>

      {/* Loading Skeletons */}
      {loading && (
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
      )}

      {/* Results View */}
      {!loading && hasSearched && results.length > 0 && (
        <div className="space-y-6">
          {viewMode === "grid" ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {results.map((result) => (
                <AssetCard key={result.asset_id} asset={result} showScore={true} />
              ))}
            </div>
          ) : (
            <div className="space-y-2">
              {results.map((result) => (
                <AssetListItem key={result.asset_id} asset={result} showScore={true} />
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
                  onClick={() => handlePageChange(page - 1)}
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
                  onClick={() => handlePageChange(page + 1)}
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
      )}

      {/* Empty State / Suggestions */}
      {!loading && hasSearched && results.length === 0 && (
        <div className="rounded-xl bg-obsidian-900 border border-white/10 p-12 text-center space-y-4">
          <div className="h-12 w-12 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center mx-auto text-muted-foreground">
            <Search className="h-6 w-6 text-primary" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white">No matches found for "{query}"</h3>
            <p className="text-xs text-muted-foreground max-w-sm mx-auto mt-1">
              Try adjusting your query, relaxing the modality filter, or trying one of our suggested search phrases.
            </p>
          </div>
        </div>
      )}

      {/* Initial Landing State before search */}
      {!loading && !hasSearched && (
        <div className="rounded-2xl bg-obsidian-900/60 border border-white/10 p-8 text-center space-y-6 top-bevel">
          <div className="max-w-md mx-auto space-y-2">
            <div className="h-12 w-12 rounded-2xl bg-primary/10 border border-primary/20 flex items-center justify-center mx-auto text-primary mb-3">
              <Sparkles className="h-6 w-6" />
            </div>
            <h3 className="text-base font-semibold text-white">Discover Media Semantically</h3>
            <p className="text-xs text-muted-foreground leading-relaxed">
              Use natural phrases to search what appears inside photos, spoken audio in video footage, or text in blueprints.
            </p>
          </div>

          <div className="max-w-xl mx-auto pt-2">
            <p className="text-[11px] font-mono text-muted-foreground/70 uppercase tracking-wider mb-3">
              Popular Exploration Queries
            </p>
            <div className="flex flex-wrap items-center justify-center gap-2">
              {promptStarters.map((item) => (
                <button
                  key={item.label}
                  onClick={() => {
                    setQuery(item.query);
                    setModality(item.mod);
                    performSearch(item.query, item.mod, limit, 1);
                    updateUrlParams(item.query, item.mod, limit, 1);
                  }}
                  className="px-3 py-1.5 rounded-lg bg-obsidian-850 hover:bg-obsidian-800 border border-white/10 hover:border-primary/40 text-xs text-foreground transition-all flex items-center gap-2 group"
                >
                  <Sparkles className="h-3.5 w-3.5 text-primary group-hover:scale-110 transition-transform" />
                  <span>{item.label}</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function SearchPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-xs font-mono text-muted-foreground">Loading search engine...</div>}>
      <SearchContent />
    </Suspense>
  );
}
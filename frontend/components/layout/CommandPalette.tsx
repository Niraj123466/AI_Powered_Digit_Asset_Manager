"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Search,
  LayoutDashboard,
  Layers,
  Database,
  Image,
  Video,
  FileText,
  X,
  ArrowRight,
  Sparkles,
} from "lucide-react";

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
}

export function CommandPalette({ isOpen, onClose }: CommandPaletteProps) {
  const [query, setQuery] = useState("");
  const router = useRouter();

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      }
    };
    if (isOpen) {
      window.addEventListener("keydown", handleKeyDown);
    }
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      router.push(`/search?q=${encodeURIComponent(query.trim())}`);
      onClose();
    }
  };

  const navigateTo = (path: string) => {
    router.push(path);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-24 px-4">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/70 backdrop-blur-md transition-opacity"
        onClick={onClose}
      />

      {/* Modal Dialog */}
      <div className="relative w-full max-w-xl rounded-xl bg-obsidian-900 border border-white/10 shadow-2xl overflow-hidden z-10 top-bevel">
        {/* Search Input Bar */}
        <form onSubmit={handleSearchSubmit} className="flex items-center px-4 border-b border-white/10 bg-obsidian-850">
          <Search className="h-5 w-5 text-muted-foreground mr-3 flex-shrink-0" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search assets, commands, or modalities... (Press Enter)"
            className="w-full bg-transparent py-4 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none"
            autoFocus
          />
          {query ? (
            <button
              type="button"
              onClick={() => setQuery("")}
              className="p-1 hover:text-foreground text-muted-foreground rounded"
            >
              <X className="h-4 w-4" />
            </button>
          ) : (
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-white/5 border border-white/10 text-muted-foreground">
              ESC
            </span>
          )}
        </form>

        {/* Action Suggestions */}
        <div className="p-3 max-h-96 overflow-y-auto space-y-4">
          {query.trim() && (
            <div>
              <p className="px-3 py-1 text-[11px] font-mono uppercase tracking-wider text-muted-foreground">
                Run Semantic Search
              </p>
              <button
                onClick={() => navigateTo(`/search?q=${encodeURIComponent(query.trim())}`)}
                className="w-full flex items-center justify-between px-3 py-2.5 rounded-lg hover:bg-white/5 text-left text-sm text-foreground transition-colors group"
              >
                <div className="flex items-center gap-3">
                  <Sparkles className="h-4 w-4 text-primary" />
                  <span>Search for <strong className="text-white">"{query}"</strong></span>
                </div>
                <ArrowRight className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
              </button>
            </div>
          )}

          <div>
            <p className="px-3 py-1 text-[11px] font-mono uppercase tracking-wider text-muted-foreground">
              Quick Navigation
            </p>
            <div className="space-y-1">
              <button
                onClick={() => navigateTo("/")}
                className="w-full flex items-center justify-between px-3 py-2 rounded-lg hover:bg-white/5 text-left text-sm text-foreground transition-colors group"
              >
                <div className="flex items-center gap-3">
                  <LayoutDashboard className="h-4 w-4 text-primary" />
                  <span>Studio Dashboard</span>
                </div>
                <span className="text-[10px] font-mono text-muted-foreground">/</span>
              </button>

              <button
                onClick={() => navigateTo("/search")}
                className="w-full flex items-center justify-between px-3 py-2 rounded-lg hover:bg-white/5 text-left text-sm text-foreground transition-colors group"
              >
                <div className="flex items-center gap-3">
                  <Search className="h-4 w-4 text-cyan" />
                  <span>Semantic Asset Explorer</span>
                </div>
                <span className="text-[10px] font-mono text-muted-foreground">/search</span>
              </button>

              <button
                onClick={() => navigateTo("/assets")}
                className="w-full flex items-center justify-between px-3 py-2 rounded-lg hover:bg-white/5 text-left text-sm text-foreground transition-colors group"
              >
                <div className="flex items-center gap-3">
                  <Layers className="h-4 w-4 text-indigo-400" />
                  <span>All Media Catalog</span>
                </div>
                <span className="text-[10px] font-mono text-muted-foreground">/assets</span>
              </button>

              <button
                onClick={() => navigateTo("/indexing")}
                className="w-full flex items-center justify-between px-3 py-2 rounded-lg hover:bg-white/5 text-left text-sm text-foreground transition-colors group"
              >
                <div className="flex items-center gap-3">
                  <Database className="h-4 w-4 text-amber-400" />
                  <span>Indexing Engine & Workers</span>
                </div>
                <span className="text-[10px] font-mono text-muted-foreground">/indexing</span>
              </button>
            </div>
          </div>

          <div>
            <p className="px-3 py-1 text-[11px] font-mono uppercase tracking-wider text-muted-foreground">
              Filter by Modality
            </p>
            <div className="space-y-1">
              <button
                onClick={() => navigateTo("/search?modality=image")}
                className="w-full flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-white/5 text-left text-sm text-foreground transition-colors"
              >
                <Image className="h-4 w-4 text-emerald-400" />
                <span>Photos & Graphic Stills</span>
              </button>

              <button
                onClick={() => navigateTo("/search?modality=video")}
                className="w-full flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-white/5 text-left text-sm text-foreground transition-colors"
              >
                <Video className="h-4 w-4 text-purple-400" />
                <span>Videos & B-Roll Clips</span>
              </button>

              <button
                onClick={() => navigateTo("/search?modality=document")}
                className="w-full flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-white/5 text-left text-sm text-foreground transition-colors"
              >
                <FileText className="h-4 w-4 text-blue-400" />
                <span>PDFs, Floor Plans & Brochures</span>
              </button>
            </div>
          </div>
        </div>

        {/* Footer info */}
        <div className="px-4 py-2.5 bg-obsidian-950 border-t border-white/5 flex items-center justify-between text-[11px] text-muted-foreground font-mono">
          <span>Navigate with arrows, select with Enter</span>
          <span>Apex DAM Precision</span>
        </div>
      </div>
    </div>
  );
}

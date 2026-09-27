"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  Search,
  Menu,
  Database,
  RefreshCw,
  Sparkles,
  Command,
  Activity,
  Layers,
  Cpu,
} from "lucide-react";
import { api, IndexStatus } from "@/lib/api";

interface HeaderProps {
  onToggleSidebar: () => void;
  onOpenCommandPalette: () => void;
}

export function Header({ onToggleSidebar, onOpenCommandPalette }: HeaderProps) {
  const router = useRouter();
  const [quickQuery, setQuickQuery] = useState("");
  const [indexStatus, setIndexStatus] = useState<IndexStatus | null>(null);
  const [isTriggering, setIsTriggering] = useState(false);

  // Poll for index status adaptively with backoff
  useEffect(() => {
    let isMounted = true;
    let timer: NodeJS.Timeout;

    async function checkStatus() {
      if (typeof document !== "undefined" && document.hidden) {
        timer = setTimeout(checkStatus, 20000);
        return;
      }
      try {
        const data = await api.getIndexStatus();
        if (isMounted) {
          setIndexStatus(data);
          const nextInterval = data?.running ? 3000 : 20000;
          timer = setTimeout(checkStatus, nextInterval);
        }
      } catch (e) {
        if (isMounted) {
          timer = setTimeout(checkStatus, 30000);
        }
      }
    }

    checkStatus();
    return () => {
      isMounted = false;
      clearTimeout(timer);
    };
  }, []);

  const handleQuickSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (quickQuery.trim()) {
      router.push(`/search?q=${encodeURIComponent(quickQuery.trim())}`);
      setQuickQuery("");
    } else {
      onOpenCommandPalette();
    }
  };

  const handleStartIndexing = async () => {
    setIsTriggering(true);
    try {
      await api.startIndexing();
      const updated = await api.getIndexStatus();
      setIndexStatus(updated);
    } catch (e) {
      console.error("Failed to start indexing:", e);
    } finally {
      setIsTriggering(false);
    }
  };

  const isIndexing = indexStatus?.running;

  return (
    <header className="sticky top-0 z-30 flex h-16 w-full items-center justify-between border-b border-white/10 bg-obsidian-950/80 px-4 md:px-6 backdrop-blur-xl">
      {/* Left: Mobile Toggle & Context */}
      <div className="flex items-center gap-3">
        <button
          onClick={onToggleSidebar}
          className="p-2 -ml-2 text-muted-foreground hover:text-foreground rounded-lg hover:bg-white/5 md:hidden"
          aria-label="Toggle Navigation Menu"
        >
          <Menu className="h-5 w-5" />
        </button>

        <div className="hidden sm:flex items-center gap-2 text-xs font-mono text-muted-foreground">
          <span className="flex h-2 w-2 rounded-full bg-emerald-500"></span>
          <span className="text-white/80 font-medium">DAM v0.1</span>
          <span className="text-white/30">•</span>
          <span className="text-white/60">Qdrant + Postgres Local</span>
        </div>
      </div>

      {/* Center: Omnibar Quick Search */}
      <div className="flex-1 max-w-xl mx-4">
        <form onSubmit={handleQuickSearch} className="relative">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
          <input
            type="text"
            value={quickQuery}
            onChange={(e) => setQuickQuery(e.target.value)}
            placeholder="Search all assets semantically or press ⌘K..."
            className="w-full h-9 pl-9 pr-14 rounded-lg bg-obsidian-900 border border-white/10 text-xs text-foreground placeholder:text-muted-foreground/70 focus:outline-none focus:border-primary/80 focus:ring-1 focus:ring-primary/80 transition-all top-bevel"
          />
          <button
            type="button"
            onClick={onOpenCommandPalette}
            className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-0.5 px-1.5 py-0.5 rounded bg-white/5 border border-white/10 text-[10px] font-mono text-muted-foreground hover:text-foreground hover:bg-white/10 transition-colors"
            title="Open Command Palette"
          >
            <Command className="h-3 w-3" />
            <span>K</span>
          </button>
        </form>
      </div>

      {/* Right: Status Telemetry & Actions */}
      <div className="flex items-center gap-2 sm:gap-3">
        {/* Live Indexing Status Indicator */}
        <div
          onClick={() => router.push("/indexing")}
          className={`cursor-pointer flex items-center gap-2 px-2.5 py-1.5 rounded-lg border text-xs font-mono transition-colors ${
            isIndexing
              ? "bg-cyan/10 border-cyan/30 text-cyan animate-pulse-subtle"
              : "bg-white/5 border-white/10 text-muted-foreground hover:text-foreground hover:border-white/20"
          }`}
          title="Click to view indexing queue"
        >
          <span
            className={`h-2 w-2 rounded-full ${
              isIndexing ? "bg-cyan animate-ping" : "bg-emerald-400"
            }`}
          />
          <span className="hidden md:inline">
            {isIndexing ? "Indexing Active..." : "Catalog Synced"}
          </span>
          {isIndexing && indexStatus?.stats?.total_processed !== undefined && (
            <span className="text-[11px] font-bold text-cyan">
              {indexStatus.stats.total_processed}/{indexStatus.stats.total_new}
            </span>
          )}
        </div>

        {/* Index Action Button */}
        <button
          onClick={handleStartIndexing}
          disabled={isIndexing || isTriggering}
          className="hidden sm:inline-flex items-center gap-1.5 h-8 px-3 rounded-lg bg-primary hover:bg-primary/90 text-white text-xs font-medium transition-colors shadow-glow-primary disabled:opacity-50 disabled:pointer-events-none"
        >
          <RefreshCw
            className={`h-3.5 w-3.5 ${
              isIndexing || isTriggering ? "animate-spin" : ""
            }`}
          />
          <span>{isIndexing ? "Indexing..." : "Index Media"}</span>
        </button>
      </div>
    </header>
  );
}

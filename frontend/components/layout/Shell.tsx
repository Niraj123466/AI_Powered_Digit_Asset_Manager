"use client";

import React, { useState, useEffect } from "react";
import { Sidebar } from "./Sidebar";
import { Header } from "./Header";
import { CommandPalette } from "./CommandPalette";
import { api, Stats } from "@/lib/api";
import { cn } from "@/lib/utils";

interface ShellProps {
  children: React.ReactNode;
}

export function Shell({ children }: ShellProps) {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false);
  const [stats, setStats] = useState<Stats | null>(null);

  // Load stats on mount and refresh on window focus or 30s interval
  useEffect(() => {
    let isMounted = true;
    async function loadStats() {
      try {
        const data = await api.getStats();
        if (isMounted) setStats(data);
      } catch (e) {
        // quiet
      }
    }
    loadStats();
    const interval = setInterval(() => {
      if (typeof document !== "undefined" && !document.hidden) {
        loadStats();
      }
    }, 30000);

    const onFocus = () => loadStats();
    window.addEventListener("focus", onFocus);

    return () => {
      isMounted = false;
      clearInterval(interval);
      window.removeEventListener("focus", onFocus);
    };
  }, []);

  // Global ⌘K shortcut
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setCommandPaletteOpen((prev) => !prev);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  return (
    <div className="min-h-screen bg-obsidian-950 text-foreground flex flex-col antialiased">
      {/* Universal Command Palette */}
      <CommandPalette
        isOpen={commandPaletteOpen}
        onClose={() => setCommandPaletteOpen(false)}
      />

      {/* Workstation Sidebar */}
      <Sidebar
        collapsed={collapsed}
        onToggleCollapse={() => setCollapsed(!collapsed)}
        mobileOpen={mobileOpen}
        onCloseMobile={() => setMobileOpen(false)}
        stats={stats}
      />

      {/* Main Content Layout */}
      <div
        className={cn(
          "flex-1 flex flex-col transition-all duration-300 ease-in-out min-h-screen",
          collapsed ? "md:pl-16" : "md:pl-60"
        )}
      >
        <Header
          onToggleSidebar={() => setMobileOpen(!mobileOpen)}
          onOpenCommandPalette={() => setCommandPaletteOpen(true)}
        />

        <main className="flex-1 p-4 md:p-6 lg:p-8 max-w-[1600px] w-full mx-auto">
          {children}
        </main>
      </div>
    </div>
  );
}

"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Search,
  Layers,
  Database,
  ChevronLeft,
  ChevronRight,
  Image,
  Video,
  FileText,
  Activity,
  HardDrive,
  Cpu,
  Sparkles,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface SidebarProps {
  collapsed: boolean;
  onToggleCollapse: () => void;
  mobileOpen: boolean;
  onCloseMobile: () => void;
  stats?: {
    total_assets: number;
    images: number;
    videos: number;
    documents: number;
    processing: number;
  } | null;
}

export function Sidebar({
  collapsed,
  onToggleCollapse,
  mobileOpen,
  onCloseMobile,
  stats,
}: SidebarProps) {
  const pathname = usePathname();

  const mainNav = [
    {
      name: "Dashboard",
      href: "/",
      icon: LayoutDashboard,
      active: pathname === "/",
    },
    {
      name: "Search & Explorer",
      href: "/search",
      icon: Search,
      active: pathname.startsWith("/search"),
    },
    {
      name: "All Media",
      href: "/assets",
      icon: Layers,
      active: pathname.startsWith("/assets") || pathname.startsWith("/asset/"),
      count: stats?.total_assets,
    },
    {
      name: "Indexing Engine",
      href: "/indexing",
      icon: Database,
      active: pathname.startsWith("/indexing"),
      badge: stats && stats.processing > 0 ? `${stats.processing} active` : undefined,
    },
  ];

  const modalities = [
    {
      name: "Images",
      href: "/search?modality=image",
      icon: Image,
      count: stats?.images,
      color: "text-emerald-400",
    },
    {
      name: "Videos",
      href: "/search?modality=video",
      icon: Video,
      count: stats?.videos,
      color: "text-purple-400",
    },
    {
      name: "Documents",
      href: "/search?modality=document",
      icon: FileText,
      count: stats?.documents,
      color: "text-blue-400",
    },
  ];

  const sidebarContent = (
    <div className="flex h-full flex-col justify-between bg-obsidian-950 border-r border-white/10 select-none">
      {/* Top Branding */}
      <div>
        <div className="flex h-16 items-center justify-between px-4 border-b border-white/10">
          <Link
            href="/"
            onClick={onCloseMobile}
            className="flex items-center gap-3 group overflow-hidden"
          >
            <div className="h-9 w-9 rounded-lg bg-primary/10 border border-primary/30 flex items-center justify-center flex-shrink-0 group-hover:border-primary transition-colors shadow-glow-primary">
              <Sparkles className="h-4 w-4 text-primary group-hover:scale-110 transition-transform" />
            </div>
            {!collapsed && (
              <div className="flex flex-col truncate">
                <span className="font-semibold text-sm tracking-tight text-white flex items-center gap-1.5">
                  APEX DAM
                  <span className="text-[10px] font-mono px-1 py-0.2 rounded bg-primary/20 text-primary border border-primary/30">
                    AI
                  </span>
                </span>
                <span className="text-[10px] font-mono text-muted-foreground truncate">
                  Digital Asset Core
                </span>
              </div>
            )}
          </Link>

          {/* Desktop collapse toggle */}
          <button
            onClick={onToggleCollapse}
            className="hidden md:flex p-1.5 rounded-md text-muted-foreground hover:text-foreground hover:bg-white/5 transition-colors"
            title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {collapsed ? (
              <ChevronRight className="h-4 w-4" />
            ) : (
              <ChevronLeft className="h-4 w-4" />
            )}
          </button>
        </div>

        {/* Main Navigation */}
        <div className="px-3 py-4 space-y-6">
          <div className="space-y-1">
            {!collapsed && (
              <p className="px-3 pb-2 text-[10px] font-mono uppercase tracking-wider text-muted-foreground/60">
                Workspace
              </p>
            )}
            {mainNav.map((item) => (
              <Link
                key={item.name}
                href={item.href}
                onClick={onCloseMobile}
                className={cn(
                  "flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium transition-all group",
                  item.active
                    ? "bg-primary text-white shadow-glow-primary font-semibold"
                    : "text-muted-foreground hover:text-foreground hover:bg-white/5"
                )}
                title={collapsed ? item.name : undefined}
              >
                <div className="flex items-center gap-3">
                  <item.icon
                    className={cn(
                      "h-4 w-4 flex-shrink-0 transition-transform group-hover:scale-110",
                      item.active ? "text-white" : "text-muted-foreground group-hover:text-foreground"
                    )}
                  />
                  {!collapsed && <span>{item.name}</span>}
                </div>
                {!collapsed && item.count !== undefined && (
                  <span
                    className={cn(
                      "text-[10px] font-mono px-1.5 py-0.5 rounded",
                      item.active
                        ? "bg-white/20 text-white"
                        : "bg-white/5 text-muted-foreground"
                    )}
                  >
                    {item.count}
                  </span>
                )}
                {!collapsed && item.badge && (
                  <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-cyan/20 text-cyan border border-cyan/30 animate-pulse-subtle">
                    {item.badge}
                  </span>
                )}
              </Link>
            ))}
          </div>

          {/* Modalities filter presets */}
          <div className="space-y-1">
            {!collapsed && (
              <p className="px-3 pb-2 text-[10px] font-mono uppercase tracking-wider text-muted-foreground/60">
                Modalities
              </p>
            )}
            {modalities.map((item) => (
              <Link
                key={item.name}
                href={item.href}
                onClick={onCloseMobile}
                className={cn(
                  "flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium transition-colors text-muted-foreground hover:text-foreground hover:bg-white/5 group"
                )}
                title={collapsed ? item.name : undefined}
              >
                <div className="flex items-center gap-3">
                  <item.icon className={cn("h-4 w-4 flex-shrink-0", item.color)} />
                  {!collapsed && <span>{item.name}</span>}
                </div>
                {!collapsed && item.count !== undefined && (
                  <span className="text-[10px] font-mono text-muted-foreground/80">
                    {item.count}
                  </span>
                )}
              </Link>
            ))}
          </div>
        </div>
      </div>

      {/* Bottom Infrastructure Telemetry */}
      <div className="p-3 border-t border-white/10 space-y-3">
        {!collapsed && (
          <div className="rounded-lg p-2.5 bg-obsidian-900 border border-white/5 text-[11px] font-mono space-y-2">
            <div className="flex items-center justify-between text-muted-foreground">
              <span className="flex items-center gap-1.5">
                <Database className="h-3 w-3 text-emerald-400" />
                PostgreSQL
              </span>
              <span className="text-emerald-400">pgvector OK</span>
            </div>
            <div className="flex items-center justify-between text-muted-foreground">
              <span className="flex items-center gap-1.5">
                <Cpu className="h-3 w-3 text-cyan" />
                Qdrant Engine
              </span>
              <span className="text-cyan">512-dim</span>
            </div>
          </div>
        )}

        <div className="flex items-center justify-between px-2 text-[10px] font-mono text-muted-foreground/60">
          {!collapsed && <span>MEDIA_ROOT active</span>}
          <div className="flex items-center gap-1.5 ml-auto">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
            <span className="text-emerald-400 text-[10px]">Online</span>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop Sidebar */}
      <aside
        className={cn(
          "hidden md:block fixed inset-y-0 left-0 z-40 transition-all duration-300 ease-in-out",
          collapsed ? "w-16" : "w-60"
        )}
      >
        {sidebarContent}
      </aside>

      {/* Mobile Drawer */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 md:hidden">
          <div
            className="fixed inset-0 bg-black/70 backdrop-blur-sm"
            onClick={onCloseMobile}
          />
          <div className="fixed inset-y-0 left-0 w-64 shadow-2xl z-50">
            {sidebarContent}
          </div>
        </div>
      )}
    </>
  );
}

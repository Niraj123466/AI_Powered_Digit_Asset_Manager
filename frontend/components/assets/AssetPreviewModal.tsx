"use client";

import React, { useEffect } from "react";
import Link from "next/link";
import {
  X,
  Download,
  ExternalLink,
  FileText,
  Video,
  Image as ImageIcon,
  Clock,
  HardDrive,
  Sparkles,
} from "lucide-react";
import { api } from "@/lib/api";

interface PreviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  asset: {
    id: string;
    filename: string;
    modality: "image" | "video" | "document";
    file_size?: number;
    extension?: string;
    score?: number;
    explanation?: string;
  } | null;
}

export function AssetPreviewModal({ isOpen, onClose, asset }: PreviewModalProps) {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    if (isOpen) {
      window.addEventListener("keydown", handleKeyDown);
    }
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen || !asset) return null;

  const previewUrl = api.getAssetPreviewUrl(asset.id);
  const downloadUrl = api.getAssetDownloadUrl(asset.id);

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return "—";
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 md:p-8">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/85 backdrop-blur-md transition-opacity"
        onClick={onClose}
      />

      {/* Modal Dialog */}
      <div className="relative w-full max-w-4xl max-h-[90vh] bg-obsidian-900 border border-white/10 rounded-xl shadow-2xl flex flex-col overflow-hidden z-10 top-bevel">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-3.5 border-b border-white/10 bg-obsidian-950">
          <div className="flex items-center gap-3 overflow-hidden">
            <div className="p-1.5 rounded-md bg-white/5 border border-white/10 text-muted-foreground flex-shrink-0">
              {asset.modality === "image" && <ImageIcon className="h-4 w-4 text-emerald-400" />}
              {asset.modality === "video" && <Video className="h-4 w-4 text-purple-400" />}
              {asset.modality === "document" && <FileText className="h-4 w-4 text-blue-400" />}
            </div>
            <div className="truncate">
              <h3 className="text-sm font-semibold text-white truncate" title={asset.filename}>
                {asset.filename}
              </h3>
              <p className="text-[11px] font-mono text-muted-foreground">
                {asset.extension?.toUpperCase() || asset.modality.toUpperCase()} • {formatFileSize(asset.file_size)}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 flex-shrink-0 ml-4">
            <Link
              href={`/asset/${asset.id}`}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-xs font-medium text-white border border-white/10 transition-colors"
            >
              <ExternalLink className="h-3.5 w-3.5 text-primary" />
              <span>Full Analysis</span>
            </Link>
            <a
              href={downloadUrl}
              download={asset.filename}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-primary hover:bg-primary/90 text-xs font-medium text-white shadow-glow-primary transition-colors"
            >
              <Download className="h-3.5 w-3.5" />
              <span>Download</span>
            </a>
            <button
              onClick={onClose}
              className="p-1.5 text-muted-foreground hover:text-white rounded-lg hover:bg-white/10 transition-colors ml-1"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Media Preview Viewport */}
        <div className="flex-1 overflow-auto bg-obsidian-950 flex items-center justify-center p-4 min-h-[360px] max-h-[65vh]">
          {asset.modality === "image" && (
            <img
              src={previewUrl}
              alt={asset.filename}
              className="max-h-[60vh] max-w-full object-contain rounded-lg border border-white/5 shadow-lg"
            />
          )}

          {asset.modality === "video" && (
            <video
              src={previewUrl}
              controls
              autoPlay
              className="max-h-[60vh] max-w-full rounded-lg border border-white/5 shadow-lg"
            >
              Your browser does not support the video tag.
            </video>
          )}

          {asset.modality === "document" && (
            <div className="w-full h-full min-h-[420px] flex flex-col items-center justify-center bg-obsidian-900/50 rounded-lg border border-white/5 p-8 text-center">
              <div className="h-16 w-16 rounded-2xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center mb-4">
                <FileText className="h-8 w-8 text-blue-400" />
              </div>
              <h4 className="text-base font-semibold text-white mb-1">{asset.filename}</h4>
              <p className="text-xs text-muted-foreground max-w-md mb-6">
                PDF Document with AI text extraction, page parsing, and vector embeddings.
              </p>
              <div className="flex gap-3">
                <a
                  href={previewUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-white/5 hover:bg-white/10 text-white text-xs font-medium border border-white/10 transition-colors"
                >
                  <ExternalLink className="h-4 w-4" />
                  <span>Open PDF in Tab</span>
                </a>
                <a
                  href={downloadUrl}
                  download={asset.filename}
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-primary hover:bg-primary/90 text-white text-xs font-medium shadow-glow-primary transition-colors"
                >
                  <Download className="h-4 w-4" />
                  <span>Download Document</span>
                </a>
              </div>
            </div>
          )}
        </div>

        {/* Footer info & Explanation */}
        {asset.explanation && (
          <div className="px-5 py-3 bg-obsidian-900 border-t border-white/10 flex items-center justify-between text-xs">
            <div className="flex items-center gap-2 text-muted-foreground">
              <Sparkles className="h-3.5 w-3.5 text-primary" />
              <span>{asset.explanation}</span>
            </div>
            {asset.score !== undefined && (
              <span className="font-mono text-xs font-semibold px-2 py-0.5 rounded bg-primary/20 text-primary border border-primary/30">
                Score: {Math.round(asset.score * 100)}%
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

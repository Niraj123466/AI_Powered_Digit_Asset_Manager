"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  Image as ImageIcon,
  Video,
  FileText,
  Eye,
  Download,
  ExternalLink,
  Clock,
  Sparkles,
  Layers,
} from "lucide-react";
import { api, SearchResult, Asset } from "@/lib/api";
import { AssetPreviewModal } from "./AssetPreviewModal";

interface AssetCardProps {
  asset: Asset | SearchResult | any;
  showScore?: boolean;
}

export function AssetCard({ asset, showScore = true }: AssetCardProps) {
  const [previewOpen, setPreviewOpen] = useState(false);
  const [imageError, setImageError] = useState(false);

  // Normalize fields between Asset and SearchResult
  const assetId = asset.asset_id || asset.id;
  const filename = asset.filename || "Untitled Asset";
  const modality = asset.modality || "image";
  const score = asset.score;
  const explanation = asset.explanation;
  const matchedDetails = asset.matched_details || {};
  const fileSize = asset.file_size || asset.metadata?.file_size;
  const extension = asset.extension || asset.metadata?.extension || filename.split(".").pop() || "";

  const previewUrl = api.getAssetPreviewUrl(assetId);
  const downloadUrl = api.getAssetDownloadUrl(assetId);

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return "";
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  const getScoreBadgeClass = (s: number) => {
    if (s >= 0.8) return "bg-emerald-500/20 text-emerald-300 border-emerald-500/40";
    if (s >= 0.6) return "bg-primary/20 text-primary border-primary/40";
    return "bg-white/10 text-muted-foreground border-white/20";
  };

  return (
    <>
      <div className="group relative rounded-xl bg-obsidian-900 border border-white/10 hover:border-white/20 transition-all duration-300 overflow-hidden flex flex-col hover:-translate-y-1 hover:shadow-xl top-bevel">
        {/* Media Preview Box */}
        <div className="relative aspect-video w-full bg-obsidian-950 overflow-hidden flex items-center justify-center">
          {modality === "image" && !imageError && (
            <img
              src={previewUrl}
              alt={filename}
              onError={() => setImageError(true)}
              className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
              loading="lazy"
            />
          )}

          {modality === "image" && imageError && (
            <div className="flex flex-col items-center justify-center text-muted-foreground p-4">
              <ImageIcon className="h-8 w-8 text-emerald-400/60 mb-1" />
              <span className="text-[11px] font-mono">Image Preview</span>
            </div>
          )}

          {modality === "video" && (
            <div className="relative w-full h-full flex items-center justify-center bg-obsidian-950">
              <video
                src={previewUrl}
                className="w-full h-full object-cover opacity-80 group-hover:opacity-100 transition-opacity"
                preload="metadata"
                muted
              />
              <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                <div className="h-10 w-10 rounded-full bg-black/60 border border-white/20 flex items-center justify-center backdrop-blur-sm group-hover:scale-110 transition-transform">
                  <Video className="h-5 w-5 text-purple-400 fill-purple-400/20" />
                </div>
              </div>
            </div>
          )}

          {modality === "document" && (
            <div className="w-full h-full flex flex-col items-center justify-center bg-gradient-to-b from-obsidian-900 to-obsidian-950 p-4 text-center">
              <div className="h-12 w-12 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center mb-2 group-hover:scale-110 transition-transform">
                <FileText className="h-6 w-6 text-blue-400" />
              </div>
              <span className="text-xs font-medium text-white/90 line-clamp-1">{filename}</span>
              <span className="text-[10px] font-mono text-muted-foreground mt-0.5">Vector PDF Document</span>
            </div>
          )}

          {/* Top Badges */}
          <div className="absolute top-2.5 inset-x-2.5 flex items-center justify-between pointer-events-none">
            {/* Format Chip */}
            <span className="text-[10px] font-mono uppercase tracking-wider px-2 py-0.5 rounded bg-black/70 backdrop-blur-md border border-white/10 text-white font-medium">
              {extension || modality}
            </span>

            {/* Relevance Score */}
            {showScore && score !== undefined && (
              <span
                className={`text-[11px] font-mono font-semibold px-2 py-0.5 rounded backdrop-blur-md border shadow-sm ${getScoreBadgeClass(
                  score
                )}`}
              >
                {Math.round(score * 100)}%
              </span>
            )}
          </div>

          {/* Bottom Floating Info */}
          <div className="absolute bottom-2.5 left-2.5 right-2.5 flex items-center justify-between pointer-events-none">
            {matchedDetails.timestamp !== undefined ? (
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan/20 border border-cyan/40 text-cyan backdrop-blur-md flex items-center gap-1 font-medium">
                <Clock className="h-3 w-3" />
                <span>{formatTime(matchedDetails.timestamp)}</span>
              </span>
            ) : matchedDetails.page_number !== undefined ? (
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-500/20 border border-indigo-500/40 text-indigo-300 backdrop-blur-md flex items-center gap-1 font-medium">
                <FileText className="h-3 w-3" />
                <span>Page {matchedDetails.page_number}</span>
              </span>
            ) : (
              <span />
            )}

            {fileSize && (
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-black/60 backdrop-blur-md text-white/80">
                {formatFileSize(fileSize)}
              </span>
            )}
          </div>

          {/* Hover Action Overlay */}
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2 z-10">
            <button
              onClick={() => setPreviewOpen(true)}
              className="p-2 rounded-lg bg-white/10 hover:bg-white/20 text-white border border-white/20 transition-all hover:scale-105"
              title="Quick Look"
            >
              <Eye className="h-4 w-4" />
            </button>
            <Link
              href={`/asset/${assetId}`}
              className="p-2 rounded-lg bg-primary hover:bg-primary/90 text-white transition-all hover:scale-105 shadow-glow-primary"
              title="Inspect Full Analysis"
            >
              <ExternalLink className="h-4 w-4" />
            </Link>
            <a
              href={downloadUrl}
              download={filename}
              className="p-2 rounded-lg bg-white/10 hover:bg-white/20 text-white border border-white/20 transition-all hover:scale-105"
              title="Download File"
            >
              <Download className="h-4 w-4" />
            </a>
          </div>
        </div>

        {/* Card Body & Metadata */}
        <div className="p-3.5 flex flex-col flex-1 justify-between gap-2 bg-obsidian-900">
          <div>
            <Link
              href={`/asset/${assetId}`}
              className="text-xs font-semibold text-white/95 hover:text-primary transition-colors line-clamp-1 block"
              title={filename}
            >
              {filename}
            </Link>

            {explanation ? (
              <p className="text-[11px] text-muted-foreground line-clamp-2 mt-1 leading-relaxed">
                {explanation}
              </p>
            ) : (
              <p className="text-[11px] font-mono text-muted-foreground/70 truncate mt-1">
                {asset.relative_path || "data/media"}
              </p>
            )}
          </div>

          <div className="pt-2 border-t border-white/5 flex items-center justify-between text-[10px] font-mono text-muted-foreground">
            <span className="capitalize text-white/60">{modality}</span>
            <Link
              href={`/asset/${assetId}`}
              className="text-primary hover:underline flex items-center gap-1 font-medium"
            >
              <span>Inspect</span>
              <span>→</span>
            </Link>
          </div>
        </div>
      </div>

      {/* Lightbox Modal */}
      <AssetPreviewModal
        isOpen={previewOpen}
        onClose={() => setPreviewOpen(false)}
        asset={{
          id: assetId,
          filename,
          modality,
          file_size: fileSize,
          extension,
          score,
          explanation,
        }}
      />
    </>
  );
}

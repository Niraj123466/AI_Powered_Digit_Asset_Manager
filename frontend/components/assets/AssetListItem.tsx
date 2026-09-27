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
} from "lucide-react";
import { api, SearchResult, Asset } from "@/lib/api";
import { AssetPreviewModal } from "./AssetPreviewModal";

interface AssetListItemProps {
  asset: Asset | SearchResult | any;
  showScore?: boolean;
}

export function AssetListItem({ asset, showScore = true }: AssetListItemProps) {
  const [previewOpen, setPreviewOpen] = useState(false);

  const assetId = asset.asset_id || asset.id;
  const filename = asset.filename || "Untitled Asset";
  const modality = asset.modality || "image";
  const score = asset.score;
  const explanation = asset.explanation;
  const matchedDetails = asset.matched_details || {};
  const fileSize = asset.file_size || asset.metadata?.file_size;
  const extension = asset.extension || asset.metadata?.extension || filename.split(".").pop() || "";
  const state = asset.state || "COMPLETED";

  const previewUrl = api.getAssetPreviewUrl(assetId);
  const downloadUrl = api.getAssetDownloadUrl(assetId);

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return "—";
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  return (
    <>
      <div className="group flex items-center justify-between p-3 rounded-lg bg-obsidian-900 border border-white/5 hover:border-white/15 hover:bg-obsidian-850 transition-all gap-4">
        {/* Thumbnail & Name */}
        <div className="flex items-center gap-3.5 min-w-0 flex-1">
          <div
            onClick={() => setPreviewOpen(true)}
            className="cursor-pointer relative h-12 w-16 rounded-md bg-obsidian-950 border border-white/10 overflow-hidden flex-shrink-0 flex items-center justify-center group-hover:border-primary/50 transition-colors"
          >
            {modality === "image" && (
              <img src={previewUrl} alt={filename} className="w-full h-full object-cover" />
            )}
            {modality === "video" && (
              <div className="flex items-center justify-center">
                <Video className="h-4 w-4 text-purple-400" />
              </div>
            )}
            {modality === "document" && (
              <div className="flex items-center justify-center">
                <FileText className="h-4 w-4 text-blue-400" />
              </div>
            )}
          </div>

          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <Link
                href={`/asset/${assetId}`}
                className="text-xs font-semibold text-white hover:text-primary transition-colors truncate"
                title={filename}
              >
                {filename}
              </Link>
              <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-white/5 border border-white/10 text-muted-foreground uppercase">
                {extension}
              </span>
            </div>

            <div className="flex items-center gap-3 text-[11px] text-muted-foreground mt-0.5">
              <span className="font-mono">{formatFileSize(fileSize)}</span>
              {explanation ? (
                <span className="truncate text-white/70 max-w-md">{explanation}</span>
              ) : (
                <span className="font-mono text-muted-foreground/60 truncate">{asset.relative_path}</span>
              )}
            </div>
          </div>
        </div>

        {/* Matched Details / Telemetry */}
        <div className="hidden sm:flex items-center gap-3 flex-shrink-0">
          {matchedDetails.timestamp !== undefined && (
            <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-cyan/15 border border-cyan/30 text-cyan flex items-center gap-1">
              <Clock className="h-3 w-3" />
              <span>{formatTime(matchedDetails.timestamp)}</span>
            </span>
          )}

          {matchedDetails.page_number !== undefined && (
            <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-indigo-500/15 border border-indigo-500/30 text-indigo-300 flex items-center gap-1">
              <FileText className="h-3 w-3" />
              <span>Page {matchedDetails.page_number}</span>
            </span>
          )}

          {showScore && score !== undefined && (
            <span className="text-xs font-mono font-semibold px-2 py-0.5 rounded bg-primary/20 text-primary border border-primary/30">
              {Math.round(score * 100)}%
            </span>
          )}

          <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-white/5 text-muted-foreground">
            {state}
          </span>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-1.5 flex-shrink-0">
          <button
            onClick={() => setPreviewOpen(true)}
            className="p-1.5 rounded-md hover:bg-white/10 text-muted-foreground hover:text-white transition-colors"
            title="Quick Look"
          >
            <Eye className="h-4 w-4" />
          </button>
          <Link
            href={`/asset/${assetId}`}
            className="p-1.5 rounded-md hover:bg-white/10 text-muted-foreground hover:text-primary transition-colors"
            title="Inspect"
          >
            <ExternalLink className="h-4 w-4" />
          </Link>
          <a
            href={downloadUrl}
            download={filename}
            className="p-1.5 rounded-md hover:bg-white/10 text-muted-foreground hover:text-white transition-colors"
            title="Download"
          >
            <Download className="h-4 w-4" />
          </a>
        </div>
      </div>

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

"use client";

import React, { useEffect, useState, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  Download,
  Copy,
  Check,
  ExternalLink,
  FileText,
  Video,
  Image as ImageIcon,
  Sparkles,
  Cpu,
  Layers,
  Clock,
  Eye,
  Camera,
  Film,
  FileCode,
  CheckCircle2,
  AlertCircle,
  Hash,
  HardDrive,
} from "lucide-react";
import { api, AssetDetailResponse } from "@/lib/api";
import { Skeleton } from "@/components/ui/skeleton";

export default function AssetDetailPage() {
  const params = useParams();
  const router = useRouter();
  const assetId = params.id as string;

  const [data, setData] = useState<AssetDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"metadata" | "ai" | "frames" | "embeddings">("metadata");
  const [copiedHash, setCopiedHash] = useState(false);
  const [copiedOcr, setCopiedOcr] = useState(false);

  const videoRef = useRef<HTMLVideoElement | null>(null);

  useEffect(() => {
    async function loadAssetDetail() {
      setLoading(true);
      setError(null);
      try {
        const detail = await api.getAssetDetail(assetId);
        setData(detail);
      } catch (err: any) {
        console.error("Failed to load asset detail:", err);
        setError("Asset could not be loaded or was not found in catalog.");
      } finally {
        setLoading(false);
      }
    }
    if (assetId) {
      loadAssetDetail();
    }
  }, [assetId]);

  const copyToClipboard = (text: string, type: "hash" | "ocr") => {
    navigator.clipboard.writeText(text);
    if (type === "hash") {
      setCopiedHash(true);
      setTimeout(() => setCopiedHash(false), 2000);
    } else {
      setCopiedOcr(true);
      setTimeout(() => setCopiedOcr(false), 2000);
    }
  };

  const handleSeekVideo = (timestamp: number) => {
    if (videoRef.current) {
      videoRef.current.currentTime = timestamp;
      videoRef.current.play();
    }
  };

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return "—";
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  const formatTime = (seconds?: number) => {
    if (seconds === undefined || seconds === null) return "00:00";
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48 rounded-lg" />
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <Skeleton className="h-[480px] lg:col-span-2 rounded-2xl" />
          <Skeleton className="h-[480px] rounded-2xl" />
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="rounded-2xl bg-obsidian-900 border border-white/10 p-12 text-center space-y-4">
        <div className="h-12 w-12 rounded-xl bg-red-500/10 border border-red-500/20 flex items-center justify-center mx-auto text-red-400">
          <AlertCircle className="h-6 w-6" />
        </div>
        <h3 className="text-base font-semibold text-white">Asset Not Found</h3>
        <p className="text-xs text-muted-foreground max-w-sm mx-auto">
          {error || "The requested digital asset does not exist or has been deleted."}
        </p>
        <Link
          href="/assets"
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-primary text-white text-xs font-medium shadow-glow-primary"
        >
          <ArrowLeft className="h-4 w-4" />
          <span>Back to Library</span>
        </Link>
      </div>
    );
  }

  const { asset, image_analysis, video_analysis, video_frames, document_analysis, document_pages, transcript, embeddings } = data;
  const previewUrl = api.getAssetPreviewUrl(asset.id);
  const downloadUrl = api.getAssetDownloadUrl(asset.id);

  return (
    <div className="space-y-6">
      {/* Top Breadcrumb & Action Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-white/10 pb-4">
        <div className="flex items-center gap-3">
          <button
            onClick={() => router.back()}
            className="p-1.5 rounded-lg bg-obsidian-900 border border-white/10 text-muted-foreground hover:text-white transition-colors"
            title="Go Back"
          >
            <ArrowLeft className="h-4 w-4" />
          </button>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base sm:text-lg font-bold text-white truncate max-w-md" title={asset.filename}>
                {asset.filename}
              </h1>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-primary/20 text-primary border border-primary/30 uppercase font-semibold">
                {asset.extension || asset.modality}
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                {asset.state}
              </span>
            </div>
            <p className="text-[11px] font-mono text-muted-foreground mt-0.5 truncate">
              {asset.relative_path}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <a
            href={previewUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-obsidian-900 hover:bg-obsidian-850 text-white text-xs font-medium border border-white/10 transition-colors"
          >
            <ExternalLink className="h-3.5 w-3.5" />
            <span>Open Raw</span>
          </a>
          <a
            href={downloadUrl}
            download={asset.filename}
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-primary hover:bg-primary/90 text-white text-xs font-medium shadow-glow-primary transition-colors"
          >
            <Download className="h-3.5 w-3.5" />
            <span>Download</span>
          </a>
        </div>
      </div>

      {/* Main Two-Column Master / Detail Workstation Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Hero Media Preview Area (7 Cols) */}
        <div className="lg:col-span-7 space-y-4">
          <div className="rounded-2xl bg-obsidian-900 border border-white/10 overflow-hidden top-bevel flex flex-col">
            {/* Viewport Header */}
            <div className="flex items-center justify-between px-4 py-2.5 bg-obsidian-950 border-b border-white/10 text-xs font-mono text-muted-foreground">
              <span className="flex items-center gap-1.5">
                {asset.modality === "image" && <ImageIcon className="h-3.5 w-3.5 text-emerald-400" />}
                {asset.modality === "video" && <Video className="h-3.5 w-3.5 text-purple-400" />}
                {asset.modality === "document" && <FileText className="h-3.5 w-3.5 text-blue-400" />}
                <span className="capitalize text-white/90">{asset.modality} Viewport</span>
              </span>
              <span>{formatFileSize(asset.file_size)}</span>
            </div>

            {/* Media Viewport */}
            <div className="relative min-h-[380px] max-h-[640px] bg-obsidian-950 flex items-center justify-center p-3 overflow-hidden">
              {asset.modality === "image" && (
                <img
                  src={previewUrl}
                  alt={asset.filename}
                  className="max-h-[580px] max-w-full object-contain rounded-lg border border-white/5 shadow-2xl"
                />
              )}

              {asset.modality === "video" && (
                <video
                  ref={videoRef}
                  src={previewUrl}
                  controls
                  className="max-h-[580px] max-w-full rounded-lg border border-white/5 shadow-2xl"
                >
                  Your browser does not support the video tag.
                </video>
              )}

              {asset.modality === "document" && (
                <div className="w-full h-full min-h-[460px] flex flex-col items-center justify-center bg-obsidian-900/60 rounded-xl border border-white/5 p-8 text-center">
                  <div className="h-20 w-20 rounded-2xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center mb-4 shadow-glow-cyan">
                    <FileText className="h-10 w-10 text-blue-400" />
                  </div>
                  <h3 className="text-base font-bold text-white mb-1">{asset.filename}</h3>
                  <p className="text-xs text-muted-foreground max-w-md mb-6 leading-relaxed">
                    Vectorized Document with PyMuPDF native text extraction, optical character recognition (OCR), and LLM-generated executive summary.
                  </p>
                  <div className="flex gap-3">
                    <a
                      href={previewUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-white/5 hover:bg-white/10 text-white text-xs font-medium border border-white/10 transition-colors"
                    >
                      <ExternalLink className="h-4 w-4" />
                      <span>Open in Browser</span>
                    </a>
                    <a
                      href={downloadUrl}
                      download={asset.filename}
                      className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-primary hover:bg-primary/90 text-white text-xs font-medium shadow-glow-primary transition-colors"
                    >
                      <Download className="h-4 w-4" />
                      <span>Download PDF</span>
                    </a>
                  </div>
                </div>
              )}
            </div>

            {/* Quick Status Footer */}
            <div className="px-4 py-2 bg-obsidian-950 border-t border-white/10 flex items-center justify-between text-[11px] font-mono text-muted-foreground">
              <span>SHA-256: <strong className="text-white/80">{asset.id}</strong></span>
              <button
                onClick={() => copyToClipboard(asset.id, "hash")}
                className="hover:text-white transition-colors flex items-center gap-1"
              >
                {copiedHash ? <Check className="h-3 w-3 text-emerald-400" /> : <Copy className="h-3 w-3" />}
                <span>{copiedHash ? "Copied" : "Copy ID"}</span>
              </button>
            </div>
          </div>
        </div>

        {/* Right Column: Tabbed Technical Inspector (5 Cols) */}
        <div className="lg:col-span-5 space-y-4">
          <div className="rounded-2xl bg-obsidian-900 border border-white/10 overflow-hidden top-bevel">
            {/* Inspector Tab Bar */}
            <div className="flex border-b border-white/10 bg-obsidian-950 p-1 gap-1">
              <button
                onClick={() => setActiveTab("metadata")}
                className={`flex-1 py-2 text-xs font-medium rounded-lg transition-colors flex items-center justify-center gap-1.5 ${
                  activeTab === "metadata"
                    ? "bg-obsidian-850 text-white shadow-sm border border-white/10"
                    : "text-muted-foreground hover:text-white hover:bg-white/5"
                }`}
              >
                <HardDrive className="h-3.5 w-3.5 text-primary" />
                <span>Specs</span>
              </button>

              <button
                onClick={() => setActiveTab("ai")}
                className={`flex-1 py-2 text-xs font-medium rounded-lg transition-colors flex items-center justify-center gap-1.5 ${
                  activeTab === "ai"
                    ? "bg-obsidian-850 text-white shadow-sm border border-white/10"
                    : "text-muted-foreground hover:text-white hover:bg-white/5"
                }`}
              >
                <Sparkles className="h-3.5 w-3.5 text-cyan" />
                <span>AI Vision</span>
              </button>

              {(video_frames?.length || document_pages?.length || transcript) && (
                <button
                  onClick={() => setActiveTab("frames")}
                  className={`flex-1 py-2 text-xs font-medium rounded-lg transition-colors flex items-center justify-center gap-1.5 ${
                    activeTab === "frames"
                      ? "bg-obsidian-850 text-white shadow-sm border border-white/10"
                      : "text-muted-foreground hover:text-white hover:bg-white/5"
                  }`}
                >
                  <Film className="h-3.5 w-3.5 text-purple-400" />
                  <span>{asset.modality === "video" ? "Frames" : "Pages"}</span>
                </button>
              )}

              <button
                onClick={() => setActiveTab("embeddings")}
                className={`flex-1 py-2 text-xs font-medium rounded-lg transition-colors flex items-center justify-center gap-1.5 ${
                  activeTab === "embeddings"
                    ? "bg-obsidian-850 text-white shadow-sm border border-white/10"
                    : "text-muted-foreground hover:text-white hover:bg-white/5"
                }`}
              >
                <Cpu className="h-3.5 w-3.5 text-emerald-400" />
                <span>Vectors</span>
              </button>
            </div>

            {/* Tab 1: Specs & Metadata */}
            {activeTab === "metadata" && (
              <div className="p-5 space-y-4 text-xs font-mono">
                <div className="space-y-2.5">
                  <div className="flex justify-between items-center py-1.5 border-b border-white/5">
                    <span className="text-muted-foreground">Filename:</span>
                    <span className="text-white font-medium truncate max-w-[200px]" title={asset.filename}>
                      {asset.filename}
                    </span>
                  </div>

                  <div className="flex justify-between items-center py-1.5 border-b border-white/5">
                    <span className="text-muted-foreground">Modality:</span>
                    <span className="text-white font-medium capitalize">{asset.modality}</span>
                  </div>

                  <div className="flex justify-between items-center py-1.5 border-b border-white/5">
                    <span className="text-muted-foreground">Format / MIME:</span>
                    <span className="text-white font-medium">{asset.mime_type}</span>
                  </div>

                  <div className="flex justify-between items-center py-1.5 border-b border-white/5">
                    <span className="text-muted-foreground">Exact File Size:</span>
                    <span className="text-white font-medium">{formatFileSize(asset.file_size)}</span>
                  </div>

                  <div className="flex justify-between items-center py-1.5 border-b border-white/5">
                    <span className="text-muted-foreground">Processing State:</span>
                    <span className="text-emerald-400 font-medium">{asset.state}</span>
                  </div>

                  <div className="flex justify-between items-center py-1.5 border-b border-white/5">
                    <span className="text-muted-foreground">Ingested At:</span>
                    <span className="text-white/80 font-medium">
                      {new Date(asset.created_at).toLocaleString()}
                    </span>
                  </div>

                  {asset.metadata?.modified_time && (
                    <div className="flex justify-between items-center py-1.5 border-b border-white/5">
                      <span className="text-muted-foreground">Disk Mtime:</span>
                      <span className="text-white/80 font-medium">
                        {new Date(asset.metadata.modified_time).toLocaleString()}
                      </span>
                    </div>
                  )}

                  {asset.metadata?.width && asset.metadata?.height && (
                    <div className="flex justify-between items-center py-1.5 border-b border-white/5">
                      <span className="text-muted-foreground">Dimensions:</span>
                      <span className="text-cyan font-medium">
                        {asset.metadata.width} × {asset.metadata.height} px
                      </span>
                    </div>
                  )}

                  {asset.metadata?.duration !== undefined && (
                    <div className="flex justify-between items-center py-1.5 border-b border-white/5">
                      <span className="text-muted-foreground">Duration:</span>
                      <span className="text-purple-400 font-medium">
                        {formatTime(asset.metadata.duration)}
                      </span>
                    </div>
                  )}

                  {asset.metadata?.page_count !== undefined && (
                    <div className="flex justify-between items-center py-1.5 border-b border-white/5">
                      <span className="text-muted-foreground">Page Count:</span>
                      <span className="text-blue-400 font-medium">
                        {asset.metadata.page_count} pages
                      </span>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Tab 2: AI Vision & Understanding */}
            {activeTab === "ai" && (
              <div className="p-5 space-y-5 text-xs">
                {/* Vision Description / Summary */}
                <div className="space-y-1.5">
                  <span className="text-[11px] font-mono uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
                    <Sparkles className="h-3.5 w-3.5 text-primary" />
                    <span>Multimodal AI Description</span>
                  </span>
                  <div className="p-3 rounded-lg bg-obsidian-950 border border-white/5 text-white/90 leading-relaxed text-xs">
                    {image_analysis?.description ||
                      video_analysis?.summary ||
                      document_analysis?.summary ||
                      "AI analysis generated via CLIP semantic vector understanding."}
                  </div>
                </div>

                {/* Tags */}
                {(image_analysis?.tags?.length || image_analysis?.objects?.length) && (
                  <div className="space-y-2">
                    <span className="text-[11px] font-mono uppercase tracking-wider text-muted-foreground block">
                      Detected Entities & Concepts
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {image_analysis?.tags?.map((tag: string, i: number) => (
                        <span
                          key={i}
                          className="px-2 py-0.5 rounded bg-primary/10 border border-primary/20 text-primary text-[11px] font-mono"
                        >
                          #{tag}
                        </span>
                      ))}
                      {image_analysis?.objects?.map((obj: string, i: number) => (
                        <span
                          key={i}
                          className="px-2 py-0.5 rounded bg-cyan/10 border border-cyan/20 text-cyan text-[11px] font-mono"
                        >
                          {obj}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* OCR Text */}
                {image_analysis?.ocr_text && (
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span className="text-[11px] font-mono uppercase tracking-wider text-muted-foreground">
                        Tesseract Optical OCR
                      </span>
                      <button
                        onClick={() => copyToClipboard(image_analysis.ocr_text || "", "ocr")}
                        className="text-[10px] font-mono text-primary hover:underline flex items-center gap-1"
                      >
                        {copiedOcr ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
                        <span>{copiedOcr ? "Copied" : "Copy text"}</span>
                      </button>
                    </div>
                    <div className="p-3 rounded-lg bg-obsidian-950 border border-white/5 text-muted-foreground font-mono text-[11px] max-h-36 overflow-y-auto whitespace-pre-wrap leading-relaxed">
                      {image_analysis.ocr_text}
                    </div>
                  </div>
                )}

                {/* Model Attribution */}
                <div className="pt-3 border-t border-white/5 flex items-center justify-between text-[11px] font-mono text-muted-foreground">
                  <span>Vision Model:</span>
                  <span className="text-white">
                    {image_analysis?.vision_model || video_analysis?.vision_model || document_analysis?.llm_model || "Ollama + CLIP"}
                  </span>
                </div>
              </div>
            )}

            {/* Tab 3: Keyframes / Document Pages / Transcript */}
            {activeTab === "frames" && (
              <div className="p-4 space-y-4 max-h-[460px] overflow-y-auto">
                {/* Video Keyframes */}
                {video_frames && video_frames.length > 0 && (
                  <div className="space-y-2">
                    <span className="text-[11px] font-mono uppercase tracking-wider text-muted-foreground block">
                      Sampled Video Frames ({video_frames.length})
                    </span>
                    <div className="space-y-2">
                      {video_frames.map((frame, i) => (
                        <div
                          key={i}
                          onClick={() => handleSeekVideo(frame.timestamp)}
                          className="cursor-pointer p-2.5 rounded-lg bg-obsidian-950 border border-white/5 hover:border-primary/40 hover:bg-obsidian-850 transition-all flex items-center justify-between gap-3 text-xs"
                        >
                          <div className="flex items-center gap-2">
                            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-purple-500/20 text-purple-300 border border-purple-500/30 flex items-center gap-1">
                              <Clock className="h-3 w-3" />
                              <span>{formatTime(frame.timestamp)}</span>
                            </span>
                            <span className="text-white/80 line-clamp-1">
                              {frame.description || `Frame #${frame.frame_number}`}
                            </span>
                          </div>
                          <span className="text-[10px] font-mono text-primary flex items-center gap-0.5">
                            <span>Seek</span>
                            <span>▶</span>
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Document Pages */}
                {document_pages && document_pages.length > 0 && (
                  <div className="space-y-2">
                    <span className="text-[11px] font-mono uppercase tracking-wider text-muted-foreground block">
                      Parsed Document Pages ({document_pages.length})
                    </span>
                    <div className="space-y-2.5">
                      {document_pages.map((page, i) => (
                        <div key={i} className="p-3 rounded-lg bg-obsidian-950 border border-white/5 text-xs space-y-1.5">
                          <div className="flex items-center justify-between font-mono text-[11px]">
                            <span className="text-primary font-semibold">Page {page.page_number}</span>
                            <span className="text-muted-foreground">{page.char_count} chars</span>
                          </div>
                          <p className="text-muted-foreground text-[11px] line-clamp-3 leading-relaxed">
                            {page.text || "No text on page"}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Transcript */}
                {transcript?.full_text && (
                  <div className="space-y-2">
                    <span className="text-[11px] font-mono uppercase tracking-wider text-muted-foreground block">
                      Spoken Audio Transcript
                    </span>
                    <div className="p-3 rounded-lg bg-obsidian-950 border border-white/5 text-xs text-white/80 font-mono leading-relaxed max-h-40 overflow-y-auto">
                      {transcript.full_text}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Tab 4: Vector Embeddings */}
            {activeTab === "embeddings" && (
              <div className="p-5 space-y-4 text-xs font-mono">
                <span className="text-[11px] uppercase tracking-wider text-muted-foreground block">
                  Qdrant Vector Points ({embeddings?.length || 0})
                </span>

                {embeddings && embeddings.length > 0 ? (
                  <div className="space-y-2.5">
                    {embeddings.map((emb, i) => (
                      <div key={i} className="p-3 rounded-lg bg-obsidian-950 border border-white/5 space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-primary font-semibold uppercase">{emb.content_type} Vector</span>
                          <span className="text-cyan px-1.5 py-0.2 rounded bg-cyan/10 text-[10px]">
                            {emb.dimensions} dims
                          </span>
                        </div>
                        <div className="text-[11px] text-muted-foreground space-y-1">
                          <div className="flex justify-between">
                            <span>Model:</span>
                            <span className="text-white">{emb.model_name}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Ref:</span>
                            <span className="text-white">{emb.content_ref || "root"}</span>
                          </div>
                          <div className="flex justify-between truncate">
                            <span>Qdrant Point ID:</span>
                            <span className="text-white/80 text-[10px] truncate max-w-[160px]">{emb.vector_id}</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="p-6 rounded-lg bg-obsidian-950 border border-white/5 text-center text-muted-foreground">
                    No explicit vector points recorded.
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

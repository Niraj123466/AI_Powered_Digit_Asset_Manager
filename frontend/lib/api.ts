import axios, { AxiosInstance, AxiosRequestConfig } from "axios";

// Determine base URL:
// Direct to backend on 127.0.0.1:8000 for maximum performance, no Node proxy lag
const getBaseUrl = () => {
  const host = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
  return host.endsWith("/api") ? host : `${host}/api`;
};

export type Modality = "image" | "video" | "document";

export type AssetState =
  | "DISCOVERED"
  | "QUEUED"
  | "PROCESSING"
  | "COMPLETED"
  | "FAILED"
  | "SKIPPED"
  | "DUPLICATE"
  | "DELETED";

export interface Asset {
  id: string;
  filename: string;
  relative_path: string;
  extension: string;
  mime_type: string;
  file_size: number;
  modality: Modality;
  state: AssetState;
  created_at: string;
  updated_at: string;
  metadata?: {
    file_size?: number;
    modified_time?: string;
    extension?: string;
    width?: number;
    height?: number;
    duration?: number;
    page_count?: number;
  };
}

export interface ImageAnalysisData {
  description?: string;
  objects?: string[];
  tags?: string[];
  ocr_text?: string;
  ocr_confidence?: number;
  vision_model?: string;
  ocr_provider?: string;
}

export interface VideoFrameData {
  frame_number: number;
  timestamp: number;
  description?: string;
  objects?: string[];
  embedding_id?: string | null;
}

export interface VideoAnalysisData {
  summary?: string;
  frame_count: number;
  processed_frames: number;
  keyframes?: Array<{ timestamp: number; description?: string }>;
  vision_model?: string;
}

export interface DocumentPageData {
  page_number: number;
  text?: string;
  char_count: number;
  is_ocr: boolean;
  embedding_id?: string | null;
}

export interface DocumentAnalysisData {
  summary?: string;
  total_chars: number;
  ocr_pages_count: number;
  native_text_pages: number;
  llm_model?: string;
}

export interface TranscriptData {
  full_text?: string;
  segments?: Array<{ start: number; end: number; text: string }>;
  language?: string;
  transcription_model?: string;
}

export interface EmbeddingData {
  id: string;
  content_type: string;
  content_ref?: string | null;
  vector_id: string;
  model_name: string;
  dimensions: number;
}

export interface AssetDetailResponse {
  asset: Asset;
  image_analysis?: ImageAnalysisData | null;
  video_analysis?: VideoAnalysisData | null;
  video_frames?: VideoFrameData[];
  document_analysis?: DocumentAnalysisData | null;
  document_pages?: DocumentPageData[];
  transcript?: TranscriptData | null;
  embeddings?: EmbeddingData[];
}

export interface SearchResult {
  asset_id: string;
  score: number;
  modality: "image" | "video" | "document";
  filename: string;
  relative_path: string;
  explanation: string;
  metadata: Record<string, any>;
  matched_details: {
    timestamp?: number;
    page_number?: number;
    description?: string;
  };
}

export interface SearchResponse {
  results: SearchResult[];
  total: number;
  query: string;
  latency_ms: number;
}

export interface Stats {
  total_assets: number;
  images: number;
  videos: number;
  documents: number;
  indexed: number;
  processing: number;
  failed: number;
  duplicates: number;
}

export interface IndexStatus {
  running: boolean;
  stats: {
    total_discovered: number;
    total_new: number;
    total_duplicates: number;
    total_processed: number;
    total_failed: number;
    total_skipped: number;
    current_file: string | null;
    current_stage: string | null;
  };
}

export interface FiltersResponse {
  modalities: string[];
  states: string[];
  extensions: {
    image: string[];
    video: string[];
    document: string[];
  };
}

export interface SearchParams {
  query: string;
  modality?: string;
  filters?: Record<string, any>;
  limit?: number;
  offset?: number;
}

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: getBaseUrl(),
      headers: {
        "Content-Type": "application/json",
      },
      timeout: 30000,
    });
  }

  // Generic pass-throughs
  async get<T = any>(url: string, config?: AxiosRequestConfig) {
    return this.client.get<T>(url, config);
  }

  async post<T = any>(url: string, data?: any, config?: AxiosRequestConfig) {
    return this.client.post<T>(url, data, config);
  }

  // Health
  async health(): Promise<{ status: string; timestamp: string }> {
    const res = await this.client.get("/health");
    return res.data;
  }

  // Indexing
  async startIndexing(): Promise<{ message: string; status: string }> {
    const res = await this.client.post("/index/start");
    return res.data;
  }

  async getIndexStatus(): Promise<IndexStatus> {
    const res = await this.client.get("/index/status");
    return res.data;
  }

  async retryFailed(): Promise<{ message: string; status: string }> {
    const res = await this.client.post("/index/retry-failed");
    return res.data;
  }

  // Assets
  async listAssets(params?: {
    modality?: string;
    state?: string;
    limit?: number;
    offset?: number;
  }): Promise<{ assets: Asset[]; total: number; limit: number; offset: number }> {
    const res = await this.client.get("/assets", { params });
    return res.data;
  }

  async getAsset(id: string): Promise<Asset> {
    const res = await this.client.get(`/assets/${id}`);
    return res.data;
  }

  async getAssetDetail(id: string): Promise<AssetDetailResponse> {
    const res = await this.client.get(`/assets/${id}/detail`);
    return res.data;
  }

  getAssetPreviewUrl(id: string): string {
    const base = getBaseUrl();
    return `${base}/assets/${id}/preview`;
  }

  getAssetDownloadUrl(id: string): string {
    const base = getBaseUrl();
    return `${base}/assets/${id}/download`;
  }

  // Search
  async search(
    queryOrParams: string | SearchParams,
    options?: Partial<SearchParams>
  ): Promise<SearchResponse> {
    let payload: SearchParams;
    if (typeof queryOrParams === "string") {
      payload = {
        query: queryOrParams,
        modality: options?.modality,
        filters: options?.filters,
        limit: options?.limit ?? 20,
        offset: options?.offset ?? 0,
      };
    } else {
      payload = queryOrParams;
    }

    const res = await this.client.post<SearchResponse>("/search", payload);
    return res.data;
  }

  // Stats
  async getStats(): Promise<Stats> {
    const res = await this.client.get("/stats");
    return res.data;
  }

  // Filters
  async getFilters(): Promise<FiltersResponse> {
    const res = await this.client.get("/filters");
    return res.data;
  }
}

export const api = new ApiClient();
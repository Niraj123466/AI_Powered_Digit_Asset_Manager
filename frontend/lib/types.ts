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
  metadata?: Record<string, any>;
}

export interface SearchResult {
  asset_id: string;
  score: number;
  modality: Modality;
  filename: string;
  relative_path: string;
  explanation: string;
  metadata: Record<string, any>;
  matched_details: Record<string, any>;
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
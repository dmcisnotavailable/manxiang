export interface BridgeCapture {
  id: string;
  source_type: string;
  source_uri?: string;
  original_text?: string;
  user_note?: string;
  ai_summary_draft?: string;
  summary_status?: string;
  parse_status?: string;
  candidate_topics: string[];
}

export interface BridgeRunInput {
  run_id: string;
  autonomy_level: string;
  captures: BridgeCapture[];
}

export interface BridgeEvent {
  type: string;
  tool_name?: string;
  payload?: unknown;
}

export interface BridgeSourceRef {
  artifact_id: string;
  chunk_id: string;
  quote: string;
  anchor: string;
}

export interface BridgeCitedNode {
  id: string;
  label: string;
  confidence: "user_impression" | "hypothesis" | "needs_evidence" | "fact";
  source_refs: BridgeSourceRef[];
}

export interface BridgeV1MapPayload {
  id: string;
  version: number;
  nodes: BridgeCitedNode[];
}

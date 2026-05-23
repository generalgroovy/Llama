export type Experiment = {
  experiment_id: string;
  name?: string;
  description?: string;
};

export type RunSummary = {
  run_id: string;
  experiment_id: string;
  seed: number;
  agent_b: { name: string; metadata: Record<string, unknown> };
  task: {
    map_id: string;
    width?: number;
    height?: number;
    start?: number[];
    goal?: number[];
    obstacles?: number[][];
    landmarks?: Record<string, number[]>;
    stations?: Record<string, number[]>;
    transit_lines?: Record<string, number[][]>;
    complexity?: string;
  };
  success: boolean;
  metrics: Record<string, number | string | object>;
  system_profile?: { name?: string; metric_detail?: string; planner?: string };
  speech_pipeline?: Record<string, Record<string, unknown> | boolean | string>;
  audio_recordings?: Array<{ turn_id: number; speaker: string; audio_path: string; audio_sidecar_path?: string; duration_seconds: number }>;
  failure_category?: string;
  failure_explanation?: string;
  route_summary?: {
    shortest_path_length?: number;
    actual_path_length?: number;
    shortest_path?: number[][];
    actual_path?: number[][];
    shortest_route_segments?: RouteSegment[];
    actual_route_segments?: RouteSegment[];
    shortest_route_advice?: string;
    actual_route_advice?: string;
  };
  transcript_url: string;
  explanation_url?: string;
};

export type Transcript = RunSummary & {
  knowledge_split?: Record<string, Record<string, boolean>>;
  agent_a_private_knowledge?: {
    goal?: number[];
    goal_label?: string;
    constraints?: string[];
    origin_label?: string;
    knows_network?: boolean;
  };
  agent_b_private_knowledge_summary?: {
    knows_network?: boolean;
    map_id?: string;
    node_count?: number;
    blocked_node_count?: number;
    line_count?: number;
  };
  shared_dialogue_state?: {
    known_goal?: number[];
    known_constraints?: string[];
    unresolved_ambiguities?: number;
  };
  turns: Array<{
    turn_id: number;
    speaker: string;
    text: string;
    spoken_text?: string;
    recognized_text?: string;
    dialogue_act?: string;
    interpreted_action: string | null;
    selected_action?: string | null;
    route_plan?: number[][];
    route_segments?: RouteSegment[];
    route_advice?: string;
    pipeline_events?: PipelineEvent[];
    audio_path?: string | null;
    audio_sidecar_path?: string | null;
    audio_duration_seconds?: number;
    ambiguity_detected?: boolean;
    constraint_satisfied?: boolean;
    state_before: { position?: number[] };
    state_after: { position?: number[] };
    valid_action: boolean;
    repair_or_clarification: boolean;
  }>;
  state_trace: Array<{ position: number[] }>;
  action_trace: unknown[];
  final_state: { position?: number[]; distance_to_goal?: number };
  errors: string[];
};

export type RouteSegment = {
  line: string;
  from_station: string;
  to_station: string;
  from_position: number[];
  to_position: number[];
  steps: number;
};

export type PipelineEvent = {
  phase: 'dialog_management' | 'nlg' | 'tts' | 'asr' | 'nlu' | string;
  enabled: boolean;
  latency_ms: number;
  payload: Record<string, unknown>;
};

export type MetricsFile = {
  aggregate: Record<string, number>;
  reliability: Record<string, unknown>;
  run_metrics: Array<Record<string, unknown>>;
  metric_definitions?: Array<{ metric_name: string; definition: string; interpretation: string }>;
};

async function loadJson<T>(path: string): Promise<T> {
  const response = await fetch(resolveDataPath(path));
  if (!response.ok) throw new Error(`Failed to load ${path}`);
  return response.json() as Promise<T>;
}

export async function loadDashboardData() {
  const [experiments, runs, metrics] = await Promise.all([
    loadJson<Experiment[]>('data/experiments.json'),
    loadJson<RunSummary[]>('data/runs.json'),
    loadJson<MetricsFile>('data/metrics.json')
  ]);
  return { experiments, runs, metrics };
}

export function loadTranscript(url: string): Promise<Transcript> {
  return loadJson<Transcript>(url);
}

function resolveDataPath(path: string) {
  if (path.startsWith('http')) return path;
  const base = import.meta.env.BASE_URL || '/';
  return `${base}${path.replace(/^\/+/, '')}`;
}

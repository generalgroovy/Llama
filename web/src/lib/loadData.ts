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
    complexity?: string;
  };
  success: boolean;
  metrics: Record<string, number | string | object>;
  transcript_url: string;
};

export type Transcript = RunSummary & {
  turns: Array<{
    turn_id: number;
    speaker: string;
    text: string;
    interpreted_action: string | null;
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

export type MetricsFile = {
  aggregate: Record<string, number>;
  reliability: Record<string, unknown>;
  run_metrics: Array<Record<string, unknown>>;
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

export const metricLabels: Record<string, string> = {
  task_success: 'Task success',
  path_distance_error: 'Distance error',
  turn_count: 'Turns',
  token_count: 'Tokens',
  repair_count: 'Repairs',
  clarification_count: 'Clarifications',
  contradiction_count: 'Contradictions',
  semantic_action_consistency: 'Action consistency',
  invalid_action_count: 'Invalid actions'
};

export function labelMetric(key: string): string {
  return metricLabels[key] ?? key.replace(/_/g, ' ');
}

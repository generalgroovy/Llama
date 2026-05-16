import type { RunSummary } from '../lib/loadData';

export default function FailurePanel({ run }: { run: RunSummary | undefined }) {
  if (!run) return null;
  return (
    <section>
      <h2>Run Explanation</h2>
      <div className="explanation">
        <strong>{run.failure_category ?? (run.success ? 'success' : 'unknown')}</strong>
        <p>{run.failure_explanation ?? 'No explanation exported for this run.'}</p>
        <p>
          Route: shortest {run.route_summary?.shortest_path_length ?? 'n/a'} / actual {run.route_summary?.actual_path_length ?? 'n/a'} steps
        </p>
        <p>System profile: {run.system_profile?.name ?? 'low'}</p>
      </div>
    </section>
  );
}

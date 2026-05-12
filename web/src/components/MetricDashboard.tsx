import { labelMetric } from '../lib/metricLabels';
import type { RunSummary } from '../lib/loadData';

export default function MetricDashboard({ runs }: { runs: RunSummary[] }) {
  const aggregate = aggregateMetrics(runs);
  return (
    <section>
      <h2>Metrics</h2>
      <div className="metric-grid">
        {Object.entries(aggregate).map(([key, value]) => (
          <div className="metric" key={key}>
            <span>{labelMetric(key)}</span>
            <strong>{format(value)}</strong>
          </div>
        ))}
      </div>
    </section>
  );
}

function aggregateMetrics(runs: RunSummary[]) {
  const values: Record<string, number[]> = {};
  for (const run of runs) {
    for (const [key, value] of Object.entries(run.metrics)) {
      if (typeof value === 'number') {
        values[key] = [...(values[key] ?? []), value];
      }
    }
  }
  return Object.fromEntries(Object.entries(values).map(([key, list]) => [key, list.reduce((a, b) => a + b, 0) / list.length]));
}

function format(value: number) {
  return Number.isInteger(value) ? String(value) : value.toFixed(2);
}

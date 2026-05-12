import { labelMetric } from '../lib/metricLabels';
import type { MetricsFile } from '../lib/loadData';

export default function ReliabilityTable({ metrics }: { metrics: MetricsFile }) {
  const reliability = metrics.reliability as {
    metric_correlation_with_task_success?: Record<string, number>;
    variance_across_seeds?: Record<string, number>;
  };
  const correlations = reliability.metric_correlation_with_task_success ?? {};
  const variances = reliability.variance_across_seeds ?? {};
  const keys = Array.from(new Set([...Object.keys(correlations), ...Object.keys(variances)]));
  return (
    <section>
      <h2>Reliability</h2>
      <table>
        <thead>
          <tr>
            <th>Metric</th>
            <th>Correlation with success</th>
            <th>Variance across seeds</th>
          </tr>
        </thead>
        <tbody>
          {keys.map((key) => (
            <tr key={key}>
              <td>{labelMetric(key)}</td>
              <td>{format(correlations[key])}</td>
              <td>{format(variances[key])}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

function format(value?: number) {
  return typeof value === 'number' ? value.toFixed(2) : 'n/a';
}

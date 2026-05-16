import type { MetricsFile } from '../lib/loadData';

export default function MetricDefinitions({ metrics }: { metrics: MetricsFile }) {
  const definitions = metrics.metric_definitions ?? [];
  if (!definitions.length) return null;
  return (
    <section>
      <h2>Metric Definitions</h2>
      <table>
        <thead>
          <tr>
            <th>Metric</th>
            <th>Definition</th>
            <th>Interpretation</th>
          </tr>
        </thead>
        <tbody>
          {definitions.slice(0, 12).map((item) => (
            <tr key={item.metric_name}>
              <td>{item.metric_name}</td>
              <td>{item.definition}</td>
              <td>{item.interpretation}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

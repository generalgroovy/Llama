import type { RunSummary } from '../lib/loadData';

export default function AgentComparison({ runs }: { runs: RunSummary[] }) {
  const rows = Object.entries(
    runs.reduce<Record<string, RunSummary[]>>((groups, run) => {
      const key = run.agent_b.name;
      groups[key] = [...(groups[key] ?? []), run];
      return groups;
    }, {})
  ).map(([agent, agentRuns]) => ({
    agent,
    runs: agentRuns.length,
    success: mean(agentRuns.map((run) => (run.success ? 1 : 0))),
    turns: mean(agentRuns.map((run) => Number(run.metrics.turn_count ?? 0))),
    invalid: mean(agentRuns.map((run) => Number(run.metrics.invalid_action_count ?? 0)))
  }));

  return (
    <section>
      <h2>Agent Comparison</h2>
      <table>
        <thead>
          <tr>
            <th>Agent B</th>
            <th>Runs</th>
            <th>Success</th>
            <th>Avg turns</th>
            <th>Avg invalid</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.agent}>
              <td>{row.agent}</td>
              <td>{row.runs}</td>
              <td>{row.success.toFixed(2)}</td>
              <td>{row.turns.toFixed(1)}</td>
              <td>{row.invalid.toFixed(1)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

function mean(values: number[]) {
  return values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : 0;
}

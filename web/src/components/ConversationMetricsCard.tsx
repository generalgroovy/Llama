import { labelMetric } from '../lib/metricLabels';
import type { RunSummary, Transcript } from '../lib/loadData';

const KEY_METRICS = [
  'task_success',
  'route_optimality_ratio',
  'shared_goal_alignment',
  'constraint_coverage',
  'belief_update_accuracy',
  'turn_count',
  'clarification_count',
  'invalid_action_count',
  'naturalness_proxy_score'
];

type Props = {
  run: RunSummary | undefined;
  transcript: Transcript | null;
};

export default function ConversationMetricsCard({ run, transcript }: Props) {
  const metrics = run?.metrics ?? {};
  return (
    <section className="info-card conversation-card">
      <header className="card-header">
        <div>
          <h2>Conversation And Metrics</h2>
          <p>{run?.failure_explanation ?? 'Select a run to inspect the cooperative dialogue.'}</p>
        </div>
        <strong className={run?.success ? 'status-pill pass' : 'status-pill warn'}>
          {run?.failure_category ?? 'no run'}
        </strong>
      </header>

      <div className="pipeline" aria-label="Dialogue evaluation pipeline">
        {pipelineStages(run, transcript).map((stage) => (
          <div className={`pipeline-stage ${stage.ok ? 'pass' : 'warn'}`} key={stage.label}>
            <span>{stage.label}</span>
            <strong>{stage.value}</strong>
          </div>
        ))}
      </div>

      <div className="content-grid conversation-grid">
        <div className="metric-strip">
          {KEY_METRICS.map((key) => (
            <div className="metric-line" key={key}>
              <span>{labelMetric(key)}</span>
              <strong>{formatMetric(metrics[key])}</strong>
            </div>
          ))}
        </div>

        <div className="conversation-list">
          <h3>Dialogue Timeline</h3>
          {transcript ? (
            transcript.turns.map((turn) => (
              <article className="dialogue-row" key={turn.turn_id}>
                <header>
                  <strong>{turn.speaker}</strong>
                  <span>#{turn.turn_id}</span>
                  {turn.dialogue_act && <span>{turn.dialogue_act}</span>}
                  {turn.selected_action && <span>{turn.selected_action}</span>}
                  {!turn.valid_action && <span className="bad">invalid</span>}
                </header>
                <p>{turn.text}</p>
              </article>
            ))
          ) : (
            <p className="empty">No transcript loaded.</p>
          )}
        </div>
      </div>
    </section>
  );
}

function pipelineStages(run: RunSummary | undefined, transcript: Transcript | null) {
  const metrics = run?.metrics ?? {};
  const goal = transcript?.agent_a_private_knowledge?.goal_label ?? transcript?.agent_a_private_knowledge?.goal?.join(', ') ?? 'n/a';
  const constraints = transcript?.agent_a_private_knowledge?.constraints?.length ?? 0;
  return [
    {
      label: 'Communicate',
      value: `${goal}, ${constraints} constraints`,
      ok: Number(metrics.goal_mention_turn ?? -1) >= 0 && Number(metrics.constraint_coverage ?? 0) >= 1
    },
    {
      label: 'Interpret',
      value: formatMetric(metrics.belief_update_accuracy),
      ok: Number(metrics.belief_update_accuracy ?? 0) >= 1
    },
    {
      label: 'Plan',
      value: formatMetric(metrics.route_optimality_ratio),
      ok: Number(metrics.route_optimality_ratio ?? 0) >= 0.95
    },
    {
      label: 'Act',
      value: `${formatMetric(metrics.invalid_action_count)} invalid`,
      ok: Number(metrics.invalid_action_count ?? 0) === 0
    },
    {
      label: 'Evaluate',
      value: run?.success ? 'success' : 'failed',
      ok: Boolean(run?.success)
    }
  ];
}

function formatMetric(value: unknown) {
  if (typeof value === 'number') return Number.isInteger(value) ? String(value) : value.toFixed(2);
  if (typeof value === 'string') return value;
  return 'n/a';
}

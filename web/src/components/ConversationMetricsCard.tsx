import { labelMetric } from '../lib/metricLabels';
import type { RunSummary, Transcript } from '../lib/loadData';

const KEY_METRICS = [
  'task_success',
  'route_optimality_ratio',
  'mean_asr_confidence',
  'mean_nlu_confidence',
  'tts_audio_coverage',
  'asr_audio_backed_rate',
  'max_audio_duration_seconds',
  'speech_duration_within_limit',
  'mean_pipeline_latency_ms',
  'turn_count',
  'invalid_action_count'
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
        {speechPipelineStages(run, transcript).map((stage) => (
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
            compactTurns(transcript.turns).map((item) => (
              <article className="dialogue-row" key={`${item.turn.turn_id}-${item.count}`}>
                <header>
                  <strong>{item.turn.speaker}</strong>
                  <span>#{item.turn.turn_id}</span>
                  {item.count > 1 && <span>x{item.count}</span>}
                  {item.turn.dialogue_act && <span>{item.turn.dialogue_act}</span>}
                  {item.turn.route_segments?.length ? <span>{item.turn.route_segments.length} line segment{item.turn.route_segments.length === 1 ? '' : 's'}</span> : null}
                  {!item.turn.valid_action && <span className="bad">invalid</span>}
                </header>
                <p>{item.turn.text}</p>
                {item.turn.audio_duration_seconds ? (
                  <small>{item.turn.audio_duration_seconds.toFixed(2)}s audio | ASR: {item.turn.recognized_text ?? item.turn.spoken_text ?? item.turn.text}</small>
                ) : null}
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

function speechPipelineStages(run: RunSummary | undefined, transcript: Transcript | null) {
  const metrics = run?.metrics ?? {};
  const events = transcript?.turns.flatMap((turn) => turn.pipeline_events ?? []) ?? [];
  const hasPhase = (phase: string) => events.some((event) => event.phase === phase);
  return [
    {
      label: 'ASR',
      value: Number(metrics.asr_enabled ?? 0) ? `${formatMetric(metrics.mean_asr_confidence)} / ${formatMetric(metrics.asr_audio_backed_rate)}` : 'off',
      ok: hasPhase('asr') && Number(metrics.asr_audio_backed_rate ?? 1) >= 1
    },
    {
      label: 'NLU',
      value: formatMetric(metrics.mean_nlu_confidence),
      ok: hasPhase('nlu') && Number(metrics.mean_nlu_confidence ?? 0) >= 0.9
    },
    {
      label: 'DM',
      value: formatMetric(metrics.belief_update_accuracy),
      ok: hasPhase('dialog_management') && Number(metrics.belief_update_accuracy ?? 0) >= 1
    },
    {
      label: 'NLG',
      value: `${formatMetric(metrics.turn_count)} turns`,
      ok: hasPhase('nlg')
    },
    {
      label: 'TTS',
      value: Number(metrics.tts_enabled ?? 0) ? `${formatMetric(metrics.tts_audio_coverage)} / ${formatMetric(metrics.max_audio_duration_seconds)}s` : 'off',
      ok: hasPhase('tts') && Number(metrics.speech_duration_within_limit ?? 1) >= 1
    }
  ];
}

function formatMetric(value: unknown) {
  if (typeof value === 'number') return Number.isInteger(value) ? String(value) : value.toFixed(2);
  if (typeof value === 'string') return value;
  return 'n/a';
}

function compactTurns(turns: Transcript['turns']) {
  const items: Array<{ turn: Transcript['turns'][number]; count: number }> = [];
  for (const turn of turns) {
    const previous = items[items.length - 1];
    if (previous && previous.turn.speaker === turn.speaker && previous.turn.text === turn.text && previous.turn.dialogue_act === turn.dialogue_act) {
      previous.count += 1;
    } else {
      items.push({ turn, count: 1 });
    }
  }
  return items;
}

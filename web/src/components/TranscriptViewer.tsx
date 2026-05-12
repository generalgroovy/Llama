import type { Transcript } from '../lib/loadData';

export default function TranscriptViewer({ transcript }: { transcript: Transcript | null }) {
  if (!transcript) return <section><h2>Transcript</h2><p className="empty">No transcript selected.</p></section>;
  return (
    <section>
      <h2>Transcript</h2>
      <div className="transcript">
        {transcript.turns.map((turn) => (
          <article className="turn" key={turn.turn_id}>
            <header>
              <strong>{turn.speaker}</strong>
              <span>#{turn.turn_id}</span>
              {turn.interpreted_action && <span>{turn.interpreted_action}</span>}
              {!turn.valid_action && <span className="bad">invalid</span>}
            </header>
            <p>{turn.text}</p>
          </article>
        ))}
      </div>
    </section>
  );
}

import type { Transcript } from '../lib/loadData';

export default function NetworkDataCard({ transcript }: { transcript: Transcript | null }) {
  if (!transcript || !transcript.task.width || !transcript.task.height) {
    return (
      <section className="info-card">
        <header className="card-header">
          <div>
            <h2>Network Data</h2>
            <p>No network data loaded.</p>
          </div>
        </header>
      </section>
    );
  }

  const path = new Set(transcript.state_trace.map((state) => state.position?.join(',')));
  const optimalPath = new Set((transcript.route_summary?.shortest_path ?? []).map((state) => state.join(',')));
  const obstacles = new Set((transcript.task.obstacles ?? []).map((item) => item.join(',')));
  const goal = transcript.task.goal?.join(',');
  const start = transcript.task.start?.join(',');
  const current = transcript.final_state.position?.join(',');
  const cells = [];
  for (let y = 0; y < transcript.task.height; y += 1) {
    for (let x = 0; x < transcript.task.width; x += 1) {
      const key = `${x},${y}`;
      cells.push({
        key,
        label: cellLabel(key, start, goal, current),
        blocked: obstacles.has(key),
        path: path.has(key),
        optimal: optimalPath.has(key)
      });
    }
  }

  return (
    <section className="info-card network-card">
      <header className="card-header">
        <div>
          <h2>Network Data</h2>
          <p>
            {transcript.task.map_id} · {transcript.task.complexity ?? 'unknown'} · {transcript.task.width}x{transcript.task.height}
          </p>
        </div>
        <strong className="status-pill neutral">B knows network</strong>
      </header>

      <div className="content-grid network-grid">
        <div className="network-facts">
          <h3>Topology</h3>
          <dl>
            <div><dt>Start</dt><dd>{transcript.task.start?.join(', ')}</dd></div>
            <div><dt>Goal</dt><dd>{transcript.task.goal?.join(', ')}</dd></div>
            <div><dt>Nodes</dt><dd>{transcript.agent_b_private_knowledge_summary?.node_count ?? 'n/a'}</dd></div>
            <div><dt>Blocked</dt><dd>{transcript.agent_b_private_knowledge_summary?.blocked_node_count ?? 0}</dd></div>
            <div><dt>Shortest path</dt><dd>{transcript.route_summary?.shortest_path_length ?? 'n/a'} steps</dd></div>
            <div><dt>Actual path</dt><dd>{transcript.route_summary?.actual_path_length ?? 'n/a'} steps</dd></div>
          </dl>
          <h3>Landmarks</h3>
          <ul className="landmark-list">
            {Object.entries(transcript.task.landmarks ?? {}).map(([name, position]) => (
              <li key={name}><strong>{name}</strong><span>{position.join(', ')}</span></li>
            ))}
          </ul>
        </div>

        <div>
          <h3>Grid And Route</h3>
          <div className="map" style={{ gridTemplateColumns: `repeat(${transcript.task.width}, 2.4rem)` }}>
            {cells.map((cell) => (
              <div className={`cell ${cell.blocked ? 'blocked' : ''} ${cell.optimal ? 'optimal' : ''} ${cell.path ? 'path' : ''}`} key={cell.key}>
                {cell.label}
              </div>
            ))}
          </div>
          <div className="legend">
            <span><i className="legend-path" /> actual</span>
            <span><i className="legend-optimal" /> optimal</span>
            <span><i className="legend-blocked" /> blocked</span>
          </div>
        </div>
      </div>
    </section>
  );
}

function cellLabel(key: string, start?: string, goal?: string, current?: string) {
  if (key === current) return 'C';
  if (key === goal) return 'G';
  if (key === start) return 'S';
  return '';
}

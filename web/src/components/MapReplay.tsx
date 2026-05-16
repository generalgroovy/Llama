import type { Transcript } from '../lib/loadData';

export default function MapReplay({ transcript }: { transcript: Transcript | null }) {
  if (!transcript || !transcript.task.width || !transcript.task.height) return <section><h2>Map Replay</h2><p className="empty">No map data available.</p></section>;
  const path = new Set(transcript.state_trace.map((state) => state.position?.join(',')));
  const obstacles = new Set((transcript.task.obstacles ?? []).map((item) => item.join(',')));
  const goal = transcript.task.goal?.join(',');
  const start = transcript.task.start?.join(',');
  const current = transcript.final_state.position?.join(',');
  const cells = [];
  for (let y = 0; y < transcript.task.height; y += 1) {
    for (let x = 0; x < transcript.task.width; x += 1) {
      const key = `${x},${y}`;
      cells.push({ key, label: cellLabel(key, start, goal, current), blocked: obstacles.has(key), path: path.has(key) });
    }
  }
  return (
    <section>
      <h2>Map Replay</h2>
      <p className="empty">
        Shortest {transcript.route_summary?.shortest_path_length ?? 'n/a'} / actual {transcript.route_summary?.actual_path_length ?? 'n/a'} steps
      </p>
      <div className="map" style={{ gridTemplateColumns: `repeat(${transcript.task.width}, 2.4rem)` }}>
        {cells.map((cell) => (
          <div className={`cell ${cell.blocked ? 'blocked' : ''} ${cell.path ? 'path' : ''}`} key={cell.key}>
            {cell.label}
          </div>
        ))}
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

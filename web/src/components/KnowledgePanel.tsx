import type { Transcript } from '../lib/loadData';

export default function KnowledgePanel({ transcript }: { transcript: Transcript | null }) {
  if (!transcript) return null;
  const agentA = transcript.agent_a_private_knowledge;
  const agentB = transcript.agent_b_private_knowledge_summary;
  const shared = transcript.shared_dialogue_state;
  return (
    <section>
      <h2>Knowledge Split</h2>
      <div className="knowledge-grid">
        <div>
          <h3>Agent A</h3>
          <p>Goal: {agentA?.goal_label ?? agentA?.goal?.join(', ') ?? 'n/a'}</p>
          <p>Constraints: {(agentA?.constraints ?? []).join(', ') || 'none'}</p>
          <p>Knows network: {String(agentA?.knows_network ?? false)}</p>
        </div>
        <div>
          <h3>Agent B</h3>
          <p>Map: {agentB?.map_id ?? 'n/a'}</p>
          <p>Nodes: {agentB?.node_count ?? 'n/a'}</p>
          <p>Blocked nodes: {agentB?.blocked_node_count ?? 0}</p>
        </div>
        <div>
          <h3>Shared State</h3>
          <p>Known goal: {shared?.known_goal?.join(', ') ?? 'n/a'}</p>
          <p>Known constraints: {(shared?.known_constraints ?? []).join(', ') || 'none'}</p>
          <p>Unresolved ambiguities: {shared?.unresolved_ambiguities ?? 0}</p>
        </div>
      </div>
    </section>
  );
}

import type { Experiment, RunSummary } from '../lib/loadData';

type Props = {
  experiments: Experiment[];
  runs: RunSummary[];
  selectedExperiment: string;
  selectedRunId: string;
  onExperimentChange: (id: string) => void;
  onRunChange: (id: string) => void;
};

export default function ExperimentSelector({
  experiments,
  runs,
  selectedExperiment,
  selectedRunId,
  onExperimentChange,
  onRunChange
}: Props) {
  const filteredRuns = selectedExperiment === 'all' ? runs : runs.filter((run) => run.experiment_id === selectedExperiment);
  return (
    <section className="toolbar">
      <label>
        Experiment
        <select value={selectedExperiment} onChange={(event) => onExperimentChange(event.target.value)}>
          <option value="all">All experiments</option>
          {experiments.map((experiment) => (
            <option key={experiment.experiment_id} value={experiment.experiment_id}>
              {experiment.name ?? experiment.experiment_id}
            </option>
          ))}
        </select>
      </label>
      <label>
        Run
        <select value={selectedRunId} onChange={(event) => onRunChange(event.target.value)}>
          {filteredRuns.map((run) => (
            <option key={run.run_id} value={run.run_id}>
              {run.run_id}
            </option>
          ))}
        </select>
      </label>
    </section>
  );
}

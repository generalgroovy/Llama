import { useEffect, useState } from 'react';
import ConversationMetricsCard from './components/ConversationMetricsCard';
import ExperimentSelector from './components/ExperimentSelector';
import NetworkDataCard from './components/NetworkDataCard';
import { loadDashboardData, loadTranscript, type Experiment, type RunSummary, type Transcript } from './lib/loadData';

export default function App() {
  const [experiments, setExperiments] = useState<Experiment[]>([]);
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [selectedExperiment, setSelectedExperiment] = useState('all');
  const [selectedRunId, setSelectedRunId] = useState('');
  const [transcript, setTranscript] = useState<Transcript | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadDashboardData()
      .then((data) => {
        setExperiments(data.experiments);
        setRuns(data.runs);
        setSelectedRunId(data.runs[0]?.run_id ?? '');
      })
      .catch((err: Error) => setError(err.message));
  }, []);

  const selectedRun = runs.find((run) => run.run_id === selectedRunId);

  useEffect(() => {
    const selected = runs.find((run) => run.run_id === selectedRunId);
    if (!selected) {
      setTranscript(null);
      return;
    }
    loadTranscript(selected.transcript_url)
      .then(setTranscript)
      .catch((err: Error) => setError(err.message));
  }, [runs, selectedRunId]);

  function changeExperiment(id: string) {
    setSelectedExperiment(id);
    const nextRuns = id === 'all' ? runs : runs.filter((run) => run.experiment_id === id);
    setSelectedRunId(nextRuns[0]?.run_id ?? '');
  }

  return (
    <main>
      <header className="page-header">
        <h1>Automatic Evaluation of Speech Dialogue Systems</h1>
        <p>Static dashboard for cooperative navigation experiments.</p>
      </header>
      {error && <p className="error">{error}</p>}
      <ExperimentSelector
        experiments={experiments}
        runs={runs}
        selectedExperiment={selectedExperiment}
        selectedRunId={selectedRunId}
        onExperimentChange={changeExperiment}
        onRunChange={setSelectedRunId}
      />
      <div className="dashboard-grid">
        <ConversationMetricsCard run={selectedRun} transcript={transcript} />
        <NetworkDataCard transcript={transcript} />
      </div>
    </main>
  );
}

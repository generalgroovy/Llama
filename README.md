# Automatic Evaluation of Speech Dialogue Systems

This repository implements a reproducible bachelor thesis software project for the faculty area "Quality and Usability". It evaluates cooperative task solving between two configurable speech dialogue system agents.

Agent A is `UserLM`, a synthetic instruction generator. Agent B is swappable by configuration, currently using `RuleAgent` for deterministic experiments and `ChatGPTAgent` as a placeholder adapter for future live LLM integration.

The current experiment model enforces asymmetric knowledge: Agent A receives the get-on station, get-off station, and constraints but not the network topology, while Agent B receives the line/network data but must infer the requested route from Agent A's dialogue.

## Architecture

The project is split into two deployable parts:

- `src/sds_eval`: Python experiment framework for agents, ASR/NLU/dialogue-management/NLG/TTS phase logging, navigation maps, dialogue runs, metrics, reliability analysis, audio artifacts, and static export.
- `web`: Vite + React + TypeScript dashboard that reads static JSON files from `web/public/data`.

GitHub Pages can only host static assets. For that reason, Python experiments run locally or in CI and export JSON artifacts. The deployed dashboard does not require, start, or call a Python backend.

## System Profiles

Experiments are configurable for low-end and high-end systems. The default is `low`.

- `low`: deterministic shortest-path planner, standard metric detail, no expensive bootstrap reliability.
- `high`: larger turn budgets and extended reliability options for stronger local or CI machines.

Set the profile in an experiment config:

```yaml
system_profile: low
```

## Local Setup

```bash
python -m pip install -e .[dev]
```

Run the Python tests:

```bash
pytest
```

## Run Experiments

Baseline:

```bash
python scripts/run_experiment.py --config configs/experiments/exp_01_baseline.yaml --out data/runs/baseline.json
```

Batch example:

```bash
python scripts/run_batch.py configs/experiments/exp_01_baseline.yaml configs/experiments/exp_02_noise.yaml --out-dir data/runs
```

Each run produces structured transcript JSON with run metadata, agent metadata, task metadata, turns, state traces, action traces, final state, success, errors, and computed metrics.

## Metrics and Reliability

Routes are conversed about as passenger-level line advice, for example: `Take line R from Alpha to Bravo, then take line EW2 from Bravo to Harbor.` The simulator may still step through the internal graph for success and optimality metrics, but the transcript and dashboard emphasize line segments rather than every intermediate station.

## Speech Pipeline

Every turn logs the complete speech dialogue pipeline:

- ASR
- NLU
- dialogue management
- NLG
- TTS

Speech components are configurable and are off by default for reproducible low-resource experiments. They can be enabled at runtime:

```bash
python scripts/run_experiment.py --config configs/experiments/exp_01_baseline.yaml --out data/runs/baseline_tts.json --enable-asr --enable-tts --audio-dir data/audio
```

When TTS is enabled, deterministic `.wav` recordings are written under `data/audio/<run_id>/` and referenced from the transcript. The default synthetic TTS backend is intentionally simple and dependency-free so batch experiments remain runnable on low-end systems.

Pipeline latencies are recorded as `0.0` by default so committed experiment artifacts are reproducible. Set `speech_pipeline.measure_latency: true` in a config when runtime timing itself is part of the experiment.

Implemented metrics include:

- task success
- path distance error
- turn count
- token count
- repair count
- clarification count
- contradiction count
- semantic action consistency
- invalid action count
- robustness by condition
- goal and constraint communication coverage
- Agent B interpretation accuracy
- belief update accuracy
- shared goal and constraint alignment
- route optimality ratio
- constraint violation count
- dialogue-act distribution
- naturalness proxy score
- ASR confidence
- NLU confidence
- TTS audio coverage
- pipeline phase count
- pipeline latency

Reliability analysis exports metric correlation with task success, variance across seeds, sensitivity to map complexity, sensitivity to noise and ambiguity, and ranking stability across Agent B variants.

Every exported run also contains a failure explanation, route summary, cooperation summary, and per-metric interpretation fields so dashboard results can be traced back to transcript evidence.

## Export Web Data

```bash
python scripts/export_web_data.py --runs data/runs/baseline.json --out web/public/data
```

This writes:

- `web/public/data/experiments.json`
- `web/public/data/runs.json`
- `web/public/data/metrics.json`
- `web/public/data/transcripts/*.json`
- `web/public/data/explanations/*.json`

## Frontend

```bash
cd web
npm install
npm run dev
```

Build the static dashboard:

```bash
cd web
npm run build
```

The dashboard provides experiment selection, run-level and aggregate metrics, Agent B comparison, knowledge split inspection, run explanations, transcript inspection with dialogue acts, map replay, route optimality, metric definitions, and reliability summaries.

## GitHub Pages

`.github/workflows/deploy-pages.yml` builds `web/dist` and deploys it to GitHub Pages. Before deployment, commit exported static data under `web/public/data` or generate it in a CI step if you add a reproducible data-generation workflow.

## ChatGPTAgent TODO

`ChatGPTAgent` intentionally performs no live API calls. It currently uses the deterministic rule fallback so tests and CI remain reproducible. A future integration should be enabled explicitly through configuration and environment variables such as `OPENAI_API_KEY`.

# Automatic Evaluation of Speech Dialogue Systems

This repository implements a reproducible bachelor thesis software project for evaluating cooperative navigation-task solving between two speech dialogue agents.

Agent A is `UserLM`, a synthetic instruction generator. Agent B is swappable by configuration, currently using `RuleAgent` for deterministic experiments and `ChatGPTAgent` as a placeholder adapter for future live LLM integration.

## Architecture

The project is split into two deployable parts:

- `src/sds_eval`: Python experiment framework for agents, navigation maps, dialogue runs, metrics, reliability analysis, and static export.
- `web`: Vite + React + TypeScript dashboard that reads static JSON files from `web/public/data`.

GitHub Pages can only host static assets. For that reason, Python experiments run locally or in CI and export JSON artifacts. The deployed dashboard does not require, start, or call a Python backend.

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

Reliability analysis exports metric correlation with task success, variance across seeds, sensitivity to map complexity, sensitivity to noise and ambiguity, and ranking stability across Agent B variants.

## Export Web Data

```bash
python scripts/export_web_data.py --runs data/runs/baseline.json --out web/public/data
```

This writes:

- `web/public/data/experiments.json`
- `web/public/data/runs.json`
- `web/public/data/metrics.json`
- `web/public/data/transcripts/*.json`

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

The dashboard provides experiment selection, run-level and aggregate metrics, Agent B comparison, transcript inspection, map replay, and reliability summaries.

## GitHub Pages

`.github/workflows/deploy-pages.yml` builds `web/dist` and deploys it to GitHub Pages. Before deployment, commit exported static data under `web/public/data` or generate it in a CI step if you add a reproducible data-generation workflow.

## ChatGPTAgent TODO

`ChatGPTAgent` intentionally performs no live API calls. It currently uses the deterministic rule fallback so tests and CI remain reproducible. A future integration should be enabled explicitly through configuration and environment variables such as `OPENAI_API_KEY`.

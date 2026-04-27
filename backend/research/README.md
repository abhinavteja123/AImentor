# AImentor Research Harness

Reproducible offline evaluation + IEEE paper skeleton for the AImentor
system. Everything here is **additive** — no file under `backend/app/`
depends on this directory.

## Quick start

```bash
# 1. Create a venv and install research-only dependencies.
python -m venv .venv && . .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r backend/app/requirements-research.txt

# 2. Run the full harness (regenerates datasets + all 5 experiments).
python -m backend.research.run_all --exp all

# 3. Build the paper (tables are auto-included via \input).
cd backend/research/paper
pdflatex aimentor_ieee.tex && bibtex aimentor_ieee && pdflatex aimentor_ieee.tex && pdflatex aimentor_ieee.tex
```

Total runtime on a modern laptop: ~5--15 minutes (sentence-transformers
download is cached on first run).

## Individual experiments

| # | Module | Table | Question |
|---|---|---|---|
| 1 | `experiments/exp1_llm_reliability.py` | `tab:reliability` | How much does multi-provider chaining improve success rate under injected faults? |
| 2 | `experiments/exp2_intent_eval.py`     | `tab:intent`       | Does a learned intent classifier beat the deployed keyword rules? |
| 3 | `experiments/exp3_ats_eval.py`        | `tab:ats`          | Does a semantic ATS beat Jaccard / TF-IDF / BM25 / keyword on resume-JD matching? |
| 4 | `experiments/exp4_user_simulator.py`  | `tab:simulator`    | Does the end-to-end pipeline complete realistic persona journeys under faults? |
| 5 | `experiments/exp5_ablations.py`       | `tab:ablations`    | How much does each component contribute (failover, ontology, intent gate)? |

Run one at a time:

```bash
python -m backend.research.run_all --exp 1
python -m backend.research.run_all --exp 2,3
python -m backend.research.run_all --exp all --skip-datagen
```

## Outputs

```
backend/research/results/
├── tables/
│   ├── exp1_reliability.csv  / exp1_reliability.tex
│   ├── exp2_intent.csv       / exp2_intent.tex
│   ├── exp3_ats.csv          / exp3_ats.tex
│   ├── exp4_simulator.csv    / exp4_simulator.tex
│   └── exp5_ablations.csv    / exp5_ablations.tex
└── run_manifest.json          # env + every experiment record
```

## Reproducibility

- Seed pinned in `config.py` (`GLOBAL_SEED = 20260421`).
- Model IDs pinned in `config.py`.
- LLM `temperature = 0.0` during evaluation.
- `run_manifest.json` captures Python version, platform, git SHA,
  installed package versions, and timestamps for every run.

## Directory layout

```
backend/research/
├── config.py                   # pinned seeds, model IDs, experiment registry
├── data_gen/                   # dataset generators (prompts, intents, resume/JD)
├── datasets/                   # generated artifacts + skills ontology + personas
├── ethics/                     # PII redactor + IRB-style consent template
├── baselines/                  # Jaccard, TF-IDF, BM25, keyword (ours base)
├── models/                     # semantic ATS, cross-encoder, learned intent
├── experiments/                # five experiment drivers + shared metrics
├── results/                    # CSVs, LaTeX fragments, run manifest
├── paper/                      # IEEEtran skeleton + references.bib
├── run_all.py                  # top-level orchestrator
└── README.md                   # this file
```

## Live mode (optional)

`--live` is a placeholder for experiments that can forward to real
providers when credentials are present. The offline path always runs and
is what the paper's numbers are built on.

## Real annotation round (optional)

`--real PATH` lets Exp.2 / Exp.3 merge a user-supplied CSV of
human-labelled data alongside the synthetic set. The PII redactor in
`ethics/pii_redactor.py` should be run over such data before commit.

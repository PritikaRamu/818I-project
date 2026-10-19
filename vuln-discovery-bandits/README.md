# Budgeted Vulnerability Discovery with Bandits

Code for selecting coding requests so as to discover as many **distinct CWE types** as possible within a query budget. The environment replays CyberSecEval requests scanned by Meta's Insecure Code Detector ([PurpleLlama](https://github.com/meta-llama/PurpleLlama)). The policies follow the selection interface of [GPTFuzz](https://github.com/sherdencooper/GPTFuzz).

## Layout

| Path | Contents |
|---|---|
| `vdb/build_cache.py` | Runs the Insecure Code Detector on all 1,916 CyberSecEval instruct requests |
| `vdb/env.py` | Arms (language × request cluster) and the replay environment |
| `vdb/policies.py` | Random, Round-robin, UCB1 (success / novelty reward), EXP3, Good-UCB, Oracle |
| `vdb/run_experiment.py` | Main experiment: result tables and discovery curves |
| `vdb/report_figures.py` | Figures and statistics used in the report |
| `results/` | Cached detector output (`icd_cache.jsonl`), result tables and figures |

## Usage

```bash
./scripts/setup.sh            # creates .venv and clones PurpleLlama into ../PurpleLlama
source .venv/bin/activate

python -m vdb.run_experiment  # tables -> results/summary.md, results/env_summary.md
python -m vdb.report_figures  # figures -> results/figures/

# Optional: rebuild the detector cache (requires semgrep from the venv on PATH)
PATH="$PWD/.venv/bin:$PATH" python -m vdb.build_cache
```

All runs are seeded and reproduce the reported numbers exactly. The cached detector output is committed, so the experiments run without semgrep.

## Detector notes

- **semgrep `--project-root` flag:** with semgrep ≥ 1.181, the detector's `--project-root /` argument causes semgrep to scan no files. `build_cache.py` disables it at runtime.
- **Missing CWE ID:** the rule `vulnerable-strcpy` reports no CWE and is mapped to CWE-120 in `env.py`.

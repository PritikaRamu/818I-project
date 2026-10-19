# Budgeted Discovery of Distinct Vulnerability Types in LLM-Generated Code

Course project (818I). Selecting coding requests to discover as many **distinct CWE types** as possible within a fixed query budget, formulated as a discovery bandit.

## Repository structure

| Directory | Contents |
|---|---|
| [`vuln-discovery-bandits/`](vuln-discovery-bandits/) | Project code: replay environment, arm construction, selection policies, experiments and results. See its README for usage. |
| [`PurpleLlama/`](PurpleLlama/) | Vendored copy of [meta-llama/PurpleLlama](https://github.com/meta-llama/PurpleLlama) at commit `d934ea2`. Provides the CyberSecEval dataset and the Insecure Code Detector (`CodeShield/insecure_code_detector`). |
| [`GPTFuzz/`](GPTFuzz/) | Vendored copy of [hubertyoo/GPTFuzz](https://github.com/hubertyoo/GPTFuzz) at commit `0c26ccc`. Reference for the selection-policy interface and mutation operators. |

The two upstream repositories are included as plain directories, without their git history, and are not modified.

## Quick start

```bash
cd vuln-discovery-bandits
./scripts/setup.sh              # creates .venv; uses ../PurpleLlama
source .venv/bin/activate
python -m vdb.run_experiment    # result tables -> results/summary.md
python -m vdb.report_figures    # figures -> results/figures/
```

## Licenses

- **Project code:** `vuln-discovery-bandits/`.
- **GPTFuzz:** MIT.
- **PurpleLlama:** licensed per component. CybersecurityBenchmarks and CodeShield are MIT, and the Llama Guard models fall under the Llama community license. See the `LICENSE` files in each directory.

"""Experiment 1: how many distinct CWEs does each arm-selection policy find within a query budget?

    python -m vdb.run_experiment [--horizon 300] [--trials 200] [--clusters 4]

Writes results/env_summary.md, results/arms.csv, results/curves.csv, results/summary.md
and figures under results/figures/.
"""
import argparse
import json
from collections import Counter

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from vdb.env import ReplayEnv, build_arms, load_cache  # noqa: E402
from vdb.paths import FIGURES_DIR, RESULTS_DIR  # noqa: E402
from vdb.policies import (EXP3Policy, GoodUCBPolicy, OraclePolicy, RandomPolicy,  # noqa: E402
                          RoundRobinPolicy, UCB1Policy)

CHECKPOINTS = [30, 100, 300]


def make_policies(env, rng):
    n = env.n_arms
    return [
        RandomPolicy(n, rng),
        RoundRobinPolicy(n, rng),
        UCB1Policy(n, rng, reward="hit"),
        UCB1Policy(n, rng, reward="novel"),
        EXP3Policy(n, rng),
        GoodUCBPolicy(n, rng, c=0.5),
        OraclePolicy(n, rng, env),
    ]


def run_trial(policy, env, horizon):
    distinct, hits = np.zeros(horizon), np.zeros(horizon)
    found_hits = 0
    for t in range(horizon):
        env_obs = env.pull(policy.select())
        policy.update(env_obs)
        found_hits += len(env_obs) > 0
        distinct[t], hits[t] = len(policy.discovered), found_hits
    return distinct, hits, policy.pulls.copy()


def evaluate(arms, policy_factory, horizon, trials, seed=0):
    """Returns {policy name: dict(distinct=[trials, T], hits=[trials, T], pulls=[trials, K])}."""
    out = {}
    for trial in range(trials):
        # Same seed for every policy within a trial so they face comparable randomness.
        names = [p.name for p in policy_factory(ReplayEnv(arms, np.random.default_rng(0)),
                                                np.random.default_rng(0))]
        for i, name in enumerate(names):
            env = ReplayEnv(arms, np.random.default_rng([seed, trial, 0]))
            policy = policy_factory(env, np.random.default_rng([seed, trial, 1]))[i]
            d, h, pulls = run_trial(policy, env, horizon)
            rec = out.setdefault(name, {"distinct": [], "hits": [], "pulls": []})
            rec["distinct"].append(d)
            rec["hits"].append(h)
            rec["pulls"].append(pulls)
    return {k: {m: np.array(v) for m, v in rec.items()} for k, rec in out.items()}


def mean_ci(x):
    return x.mean(0), 1.96 * x.std(0, ddof=1) / np.sqrt(len(x))


def summarize_env(records, arms):
    detected = [r for r in records if r["detected_cwes"]]
    all_cwes = Counter(c for r in records for c in r["detected_cwes"])
    label_hit = np.mean([r["label_cwe"] in r["detected_cwes"] for r in records])
    per_lang = pd.DataFrame([
        {"language": lang,
         "snippets": sum(r["language"] == lang for r in records),
         "detection_rate": np.mean([bool(r["detected_cwes"]) for r in records if r["language"] == lang]),
         "distinct_cwes": len({c for r in records if r["language"] == lang for c in r["detected_cwes"]}),
         "label_recovered": np.mean([r["label_cwe"] in r["detected_cwes"] for r in records if r["language"] == lang])}
        for lang in sorted({r["language"] for r in records})])

    owners = Counter(c for a in arms for c in a.support)
    arm_df = pd.DataFrame([{
        "arm": a.name, "keywords": a.keywords, "snippets": a.size, "hit_rate": round(a.hit_rate, 3),
        "distinct_cwes": len(a.support),
        "exclusive_cwes": ",".join(sorted(c for c in a.support if owners[c] == 1)),
    } for a in arms])
    arm_df.to_csv(RESULTS_DIR / "arms.csv", index=False)

    rare = sorted([c for c, n in all_cwes.items() if n <= 3], key=lambda c: int(c.split("-")[1]))
    lines = [
        "# Environment summary",
        "",
        f"- Snippets scanned: {len(records)} (scan errors: {sum(r['error'] is not None for r in records)})",
        f"- Snippets with >=1 ICD finding: {len(detected)} ({len(detected) / len(records):.1%})",
        f"- Distinct CWEs detectable in the whole pool (discovery ceiling): {len(all_cwes)}",
        f"- Distinct CWE labels in the dataset: {len({r['label_cwe'] for r in records})}",
        f"- Fraction of snippets where the ICD re-detects the dataset's own CWE label: {label_hit:.1%}",
        f"- CWEs detected in <=3 snippets (the long tail): {len(rare)} -> {', '.join(rare)}",
        f"- Arms: {len(arms)}; CWEs found in exactly one arm: {sum(v == 1 for v in owners.values())}",
        f"- Spearman correlation between arm hit rate and arm distinct-CWE count: "
        f"{arm_df['hit_rate'].corr(arm_df['distinct_cwes'], method='spearman'):.2f}",
        "",
        "## Per language",
        "",
        per_lang.to_markdown(index=False, floatfmt=".3f"),
        "",
        "## CWE frequency (number of snippets in which the ICD reports it)",
        "",
        pd.DataFrame(all_cwes.most_common(), columns=["cwe", "snippets"]).to_markdown(index=False),
        "",
    ]
    (RESULTS_DIR / "env_summary.md").write_text("\n".join(lines))
    return len(all_cwes), arm_df


def plot_curves(results, ceiling, horizon, path):
    fig, ax = plt.subplots(figsize=(7.5, 4.6))
    t = np.arange(1, horizon + 1)
    for name, rec in results.items():
        m, ci = mean_ci(rec["distinct"])
        style = "--" if name.startswith("Oracle") else "-"
        ax.plot(t, m, style, label=name, lw=2 if "Good" in name else 1.4)
        ax.fill_between(t, m - ci, m + ci, alpha=0.15)
    ax.axhline(ceiling, color="grey", lw=0.8, ls=":")
    ax.text(horizon * 0.99, ceiling - 0.3, f"ceiling = {ceiling} CWEs", ha="right", va="top",
            fontsize=8, color="grey")
    for c in CHECKPOINTS:
        if c < horizon:
            ax.axvline(c, color="grey", lw=0.5, ls=":")
    ax.set_xlabel("queries (pulls)")
    ax.set_ylabel("distinct CWEs discovered")
    ax.set_title("Vulnerability-type discovery vs query budget (mean, 95% CI)")
    ax.legend(fontsize=8, loc="lower right")
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def plot_tradeoff(results, horizon, path):
    fig, ax = plt.subplots(figsize=(6, 4.2))
    for name, rec in results.items():
        hit_rate = rec["hits"][:, -1].mean() / horizon
        ax.scatter(hit_rate, rec["distinct"][:, -1].mean(), s=45, label=name,
                   marker="*" if name.startswith("Oracle") else "o")
    ax.legend(fontsize=7, loc="upper right")
    ax.set_xlabel(f"hit rate (fraction of {horizon} queries with any finding)")
    ax.set_ylabel(f"distinct CWEs after {horizon} queries")
    ax.set_title("Finding *something* vs finding *variety*")
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def checkpoint_table(results, ceiling, horizon):
    rows = []
    for name, rec in results.items():
        row = {"policy": name}
        for c in [c for c in CHECKPOINTS if c <= horizon]:
            m, ci = mean_ci(rec["distinct"][:, c - 1])
            row[f"CWEs@{c}"] = f"{m:.1f} ± {ci:.1f}"
        row[f"% ceiling@{horizon}"] = f"{100 * rec['distinct'][:, -1].mean() / ceiling:.0f}%"
        row[f"hit rate@{horizon}"] = f"{rec['hits'][:, -1].mean() / horizon:.2f}"
        rows.append(row)
    return pd.DataFrame(rows)


def rarity_breakdown(records, arms, horizon, trials):
    """Mean number of CWEs found per rarity band (by # snippets the ICD flags with that CWE)."""
    freq = Counter(c for r in records for c in r["detected_cwes"])
    factories = {"Random": lambda env, rng: RandomPolicy(env.n_arms, rng),
                 "Good-UCB": lambda env, rng: GoodUCBPolicy(env.n_arms, rng),
                 "Oracle": lambda env, rng: OraclePolicy(env.n_arms, rng, env)}
    found = {name: Counter() for name in factories}
    for trial in range(trials):
        for name, factory in factories.items():
            env = ReplayEnv(arms, np.random.default_rng([4, trial, 0]))
            policy = factory(env, np.random.default_rng([4, trial, 1]))
            for _ in range(horizon):
                policy.update(env.pull(policy.select()))
            found[name].update(policy.discovered)
    rows = []
    for label, lo, hi in [("common (>=20 snippets)", 20, 10**9), ("mid (4-19)", 4, 19), ("rare (<=3)", 1, 3)]:
        cwes = [c for c, n in freq.items() if lo <= n <= hi]
        rows.append({"band": label, "CWEs in band": len(cwes),
                     **{name: round(sum(found[name][c] for c in cwes) / trials, 1) for name in factories}})
    return pd.DataFrame(rows)


def main(horizon, trials, clusters):
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    records = load_cache()
    arms = build_arms(records, clusters_per_language=clusters)
    ceiling, arm_df = summarize_env(records, arms)

    results = evaluate(arms, make_policies, horizon, trials)
    plot_curves(results, ceiling, horizon, FIGURES_DIR / "discovery_curves.png")
    plot_tradeoff(results, horizon, FIGURES_DIR / "hit_vs_variety.png")
    main_table = checkpoint_table(results, ceiling, horizon)

    t = np.arange(1, horizon + 1)
    curves = pd.DataFrame({"t": t, **{name: rec["distinct"].mean(0) for name, rec in results.items()}})
    curves.to_csv(RESULTS_DIR / "curves.csv", index=False)

    # Where did each policy spend its budget? (share of pulls on the 5 most-pulled arms)
    concentration = pd.DataFrame([{
        "policy": name,
        "top-5 arm share": f"{np.sort(rec['pulls'].mean(0))[::-1][:5].sum() / horizon:.2f}",
        "arms never pulled (mean)": f"{(rec['pulls'] == 0).sum(1).mean():.1f}",
    } for name, rec in results.items()])

    # Sensitivity to the exploration constant (picked a priori as 0.5 for Good-UCB, 1.0 for UCB1).
    sens_rows = []
    for c in [0.1, 0.25, 0.5, 1.0, 2.0]:
        factory = lambda env, rng, c=c: [GoodUCBPolicy(env.n_arms, rng, c=c),  # noqa: E731
                                         UCB1Policy(env.n_arms, rng, reward="novel", c=c)]
        res = evaluate(arms, factory, horizon, max(50, trials // 4), seed=1)
        for name, rec in res.items():
            sens_rows.append({"policy": name.split(" c=")[0], "c": c,
                              **{f"CWEs@{k}": round(rec["distinct"][:, k - 1].mean(), 1)
                                 for k in CHECKPOINTS if k <= horizon}})
    sens = pd.DataFrame(sens_rows)

    # Arm-granularity ablation: 8 language arms vs language x prompt-cluster arms.
    abl_rows = []
    for k in [1, clusters]:
        res = evaluate(build_arms(records, clusters_per_language=k),
                       lambda env, rng: [RandomPolicy(env.n_arms, rng), GoodUCBPolicy(env.n_arms, rng),
                                         OraclePolicy(env.n_arms, rng, env)],
                       horizon, max(50, trials // 4), seed=2)
        for name, rec in res.items():
            abl_rows.append({"arms": f"{8 * k}", "policy": name,
                             **{f"CWEs@{c}": round(rec["distinct"][:, c - 1].mean(), 1)
                                for c in CHECKPOINTS if c <= horizon}})
    abl = pd.DataFrame(abl_rows)

    # Long-horizon check: does learning separate from Random once each arm has more samples?
    long_T = 1000
    res = evaluate(arms, lambda env, rng: [RandomPolicy(env.n_arms, rng),
                                          UCB1Policy(env.n_arms, rng, reward="hit"),
                                          UCB1Policy(env.n_arms, rng, reward="novel"),
                                          GoodUCBPolicy(env.n_arms, rng)],
                   long_T, 50, seed=3)
    long_df = pd.DataFrame([{"policy": name,
                             **{f"CWEs@{k}": f"{rec['distinct'][:, k - 1].mean():.1f}"
                                for k in [100, 300, 600, 1000]}} for name, rec in res.items()])

    rarity_df = rarity_breakdown(records, arms, horizon, trials=100)

    summary = "\n".join([
        "# Experiment 1 results",
        "",
        f"horizon T={horizon}, trials={trials}, arms={len(arms)} (8 languages x {clusters} prompt clusters), "
        f"discovery ceiling={ceiling} CWEs",
        "",
        "## Distinct CWEs discovered (mean ± 95% CI)",
        "",
        main_table.to_markdown(index=False),
        "",
        "## Budget concentration",
        "",
        concentration.to_markdown(index=False),
        "",
        "## Sensitivity to exploration constant c",
        "",
        sens.to_markdown(index=False),
        "",
        "## Arm granularity ablation",
        "",
        abl.to_markdown(index=False),
        "",
        f"## Long horizon (T={long_T}, 50 trials)",
        "",
        long_df.to_markdown(index=False),
        "",
        f"## Where the oracle gap comes from (CWEs found by T={horizon}, 100 trials)",
        "",
        rarity_df.to_markdown(index=False),
        "",
    ])
    (RESULTS_DIR / "summary.md").write_text(summary)
    (RESULTS_DIR / "config.json").write_text(json.dumps(
        {"horizon": horizon, "trials": trials, "clusters_per_language": clusters}, indent=2))
    print(summary)
    print(arm_df.to_string())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--horizon", type=int, default=300)
    parser.add_argument("--trials", type=int, default=200)
    parser.add_argument("--clusters", type=int, default=4)
    args = parser.parse_args()
    main(args.horizon, args.trials, args.clusters)

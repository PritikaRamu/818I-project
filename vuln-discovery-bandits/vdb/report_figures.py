"""Figures and statistics used in the report.

    python -m vdb.report_figures

Writes results/figures/{arms_scatter,discovery,allocation}.pdf and prints the allocation statistics.
"""
from collections import Counter

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from scipy.stats import spearmanr  # noqa: E402

from vdb.env import build_arms, load_cache  # noqa: E402
from vdb.paths import FIGURES_DIR  # noqa: E402
from vdb.policies import GoodUCBPolicy, OraclePolicy, RandomPolicy, UCB1Policy  # noqa: E402
from vdb.run_experiment import evaluate, mean_ci, rarity_breakdown  # noqa: E402

OUT = FIGURES_DIR
plt.rcParams.update({"font.family": "serif", "font.size": 9, "axes.spines.top": False,
                     "axes.spines.right": False, "pdf.fonttype": 42})
COLORS = {"UCB1 (hit reward)": "#d62728", "UCB1 (novelty reward)": "#ff7f0e", "Good-UCB": "#1f77b4",
          "Random": "#7f7f7f", "Oracle (greedy, knows distributions)": "#2ca02c"}
SHORT = {"UCB1 (hit reward)": "UCB1, success reward", "UCB1 (novelty reward)": "UCB1, novelty reward",
         "Good-UCB": "Good-UCB", "Random": "Random", "Oracle (greedy, knows distributions)": "Oracle"}
HIGHLIGHT = {"java:3", "java:1", "rust:1", "c:3", "csharp:1", "php:2", "python:3", "javascript:3"}


def arms_scatter(arms):
    owners = Counter(c for a in arms for c in a.support)
    fig, ax = plt.subplots(figsize=(3.4, 2.6))
    for a in arms:
        exclusive = sum(owners[c] == 1 for c in a.support)
        ax.scatter(a.hit_rate, len(a.support), s=12 + 9 * a.size ** 0.5, alpha=0.65,
                   color="#1f77b4" if exclusive == 0 else "#d62728", edgecolor="white", lw=0.5)
        if a.name in HIGHLIGHT:
            ax.annotate(a.name, (a.hit_rate, len(a.support)), fontsize=6.5, xytext=(3, 3),
                        textcoords="offset points")
    ax.scatter([], [], color="#d62728", s=20, label="holds a CWE found in no other arm")
    ax.scatter([], [], color="#1f77b4", s=20, label="no exclusive CWE")
    ax.set_xlabel("hit rate (P[pull yields any CWE])")
    ax.set_ylabel("distinct CWEs in arm")
    ax.legend(fontsize=6, loc="upper left", frameon=False)
    fig.tight_layout()
    fig.savefig(OUT / "arms_scatter.pdf")
    plt.close(fig)


def discovery(results, rarity):
    fig, (ax, bx) = plt.subplots(1, 2, figsize=(7.0, 2.6), gridspec_kw={"width_ratios": [1.5, 1]})
    t = np.arange(1, results["Random"]["distinct"].shape[1] + 1)
    for name, rec in results.items():
        m, ci = mean_ci(rec["distinct"])
        ax.plot(t, m, color=COLORS[name], lw=1.4, ls="--" if name.startswith("Oracle") else "-",
                label=SHORT[name])
        ax.fill_between(t, m - ci, m + ci, color=COLORS[name], alpha=0.15, lw=0)
    ax.axhline(46, color="grey", lw=0.6, ls=":")
    ax.text(t[-1], 45, "ceiling (46)", ha="right", va="top", fontsize=7, color="grey")
    ax.set_xlabel("queries $t$")
    ax.set_ylabel("distinct CWEs discovered")
    ax.set_title("(a) discovery curves", fontsize=9)
    ax.legend(fontsize=6.5, frameon=False, loc="lower right")

    bands = ["common\n(≥20 requests)", "mid\n(4–19)", "rare\n(≤3)"]
    width = 0.27
    for i, (col, color) in enumerate([("Random", COLORS["Random"]), ("Good-UCB", COLORS["Good-UCB"]),
                                      ("Oracle", COLORS["Oracle (greedy, knows distributions)"])]):
        bx.bar(np.arange(3) + (i - 1) * width, rarity[col], width, color=color, label=col)
    bx.scatter(np.arange(3), rarity["CWEs in band"], marker="_", s=300, color="black", label="CWEs in band")
    bx.set_xticks(np.arange(3), bands, fontsize=7)
    bx.set_ylabel("CWEs found at $T=300$")
    bx.set_title("(b) discoveries by CWE rarity", fontsize=9)
    bx.legend(fontsize=6.5, frameon=False)
    fig.tight_layout()
    fig.savefig(OUT / "discovery.pdf")
    plt.close(fig)


def allocation(arms, results):
    order = np.argsort([a.hit_rate for a in arms])
    fig, ax = plt.subplots(figsize=(7.0, 2.4))
    names = ["UCB1 (hit reward)", "Good-UCB", "Oracle (greedy, knows distributions)"]
    width = 0.28
    for i, name in enumerate(names):
        pulls = results[name]["pulls"].mean(0)[order]
        ax.bar(np.arange(len(arms)) + (i - 1) * width, pulls, width, color=COLORS[name], label=SHORT[name])
    ax2 = ax.twinx()
    ax2.plot(np.arange(len(arms)), [arms[j].hit_rate for j in order], "k.", ms=4, label="arm hit rate")
    ax2.set_ylim(0, 1.05)
    ax2.set_ylabel("hit rate", fontsize=8)
    ax2.spines["top"].set_visible(False)
    ax.set_xticks(np.arange(len(arms)), [arms[j].name for j in order], rotation=70, fontsize=6)
    ax.set_ylabel("mean pulls (of 300)")
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, fontsize=6.5, frameon=False, loc="lower left",
              bbox_to_anchor=(0, 1.0), ncol=4)
    fig.tight_layout()
    fig.savefig(OUT / "allocation.pdf")
    plt.close(fig)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    records = load_cache()
    arms = build_arms(records, clusters_per_language=4)
    factory = lambda env, rng: [RandomPolicy(env.n_arms, rng),  # noqa: E731
                                UCB1Policy(env.n_arms, rng, reward="hit"),
                                UCB1Policy(env.n_arms, rng, reward="novel"),
                                GoodUCBPolicy(env.n_arms, rng),
                                OraclePolicy(env.n_arms, rng, env)]
    results = evaluate(arms, factory, horizon=300, trials=200)
    rarity = rarity_breakdown(records, arms, 300, trials=100)

    arms_scatter(arms)
    discovery(results, rarity)
    allocation(arms, results)

    hit = np.array([a.hit_rate for a in arms])
    owners = Counter(c for a in arms for c in a.support)
    exclusive = np.array([sum(owners[c] == 1 for c in a.support) for a in arms])
    for name in ["UCB1 (hit reward)", "Good-UCB", "Oracle (greedy, knows distributions)"]:
        pulls = results[name]["pulls"].mean(0)
        print(f"{name}: spearman(pulls, hit rate)={spearmanr(pulls, hit)[0]:.2f}, "
              f"share of pulls on arms with an exclusive CWE={pulls[exclusive > 0].sum() / 300:.2f}")
    print(f"arms with an exclusive CWE: {(exclusive > 0).sum()} / {len(arms)}")
    print(rarity.to_string())


if __name__ == "__main__":
    main()

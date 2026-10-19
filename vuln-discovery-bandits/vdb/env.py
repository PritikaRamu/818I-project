"""Replay environment: arms are prompt families, a pull reveals the CWE set of one cached snippet."""
import json
from dataclasses import dataclass, field

import numpy as np
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer

from vdb.paths import ICD_CACHE


@dataclass
class Arm:
    name: str
    language: str
    keywords: str
    observations: 'list[frozenset[str]]' = field(default_factory=list)
    prompt_ids: 'list[str]' = field(default_factory=list)

    @property
    def size(self) -> int:
        return len(self.observations)

    @property
    def hit_rate(self) -> float:
        return float(np.mean([len(o) > 0 for o in self.observations]))

    @property
    def support(self) -> 'set[str]':
        return set().union(*self.observations)


# ICD rules that report an empty cwe_id. vulnerable-strcpy (semgrep, C/C++) is the only one in this
# dataset; CWE-120 (buffer copy without checking size of input) is the standard CWE for unchecked strcpy.
RULE_CWE_FALLBACK = {"vulnerable-strcpy": "CWE-120"}


def load_cache(path=ICD_CACHE) -> 'list[dict]':
    with open(path) as fp:
        records = [json.loads(line) for line in fp]
    for r in records:
        for issue in r["issues"]:
            if not issue["cwe"]:
                issue["cwe"] = RULE_CWE_FALLBACK.get(issue["rule"], "")
        r["detected_cwes"] = sorted({i["cwe"] for i in r["issues"] if i["cwe"]})
    return sorted(records, key=lambda r: int(r["prompt_id"]))


def build_arms(records: 'list[dict]', clusters_per_language: int = 4, seed: int = 0) -> 'list[Arm]':
    """Group snippets into arms using only attacker-visible information (language + prompt text).

    With clusters_per_language=1 the arms are just the 8 languages. Otherwise each language is
    split by k-means over TF-IDF of the natural-language task, so an arm is a "family" of
    similar coding requests (e.g. python: file/path/directory tasks). CWE labels are never used.
    """
    arms = []
    for language in sorted({r["language"] for r in records}):
        recs = [r for r in records if r["language"] == language]
        if clusters_per_language == 1:
            groups, names = {0: recs}, {0: "all"}
        else:
            vec = TfidfVectorizer(stop_words="english", max_features=2000, min_df=2)
            X = vec.fit_transform([r["test_case_prompt"] for r in recs])
            km = KMeans(n_clusters=clusters_per_language, n_init=10, random_state=seed).fit(X)
            terms = np.array(vec.get_feature_names_out())
            groups, names = {}, {}
            for c in range(clusters_per_language):
                groups[c] = [r for r, lab in zip(recs, km.labels_) if lab == c]
                names[c] = "/".join(terms[np.argsort(km.cluster_centers_[c])[::-1][:3]])
        for c, members in groups.items():
            arms.append(Arm(
                name=f"{language}:{c}",
                language=language,
                keywords=names[c],
                observations=[frozenset(r["detected_cwes"]) for r in members],
                prompt_ids=[r["prompt_id"] for r in members],
            ))
    return arms


class ReplayEnv:
    """Pulling arm a samples one snippet uniformly (with replacement) from that arm."""

    def __init__(self, arms: 'list[Arm]', rng: np.random.Generator):
        self.arms = arms
        self.rng = rng

    @property
    def n_arms(self) -> int:
        return len(self.arms)

    def pull(self, a: int) -> 'frozenset[str]':
        obs = self.arms[a].observations
        return obs[self.rng.integers(len(obs))]

    def expected_new(self, a: int, discovered: 'set[str]') -> float:
        """E[# new CWEs] from one pull of arm a; only the oracle policy may call this."""
        return float(np.mean([len(o - discovered) for o in self.arms[a].observations]))

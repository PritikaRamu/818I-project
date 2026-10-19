"""Arm-selection policies.

The interface mirrors GPTFuzz's SelectPolicy (gptfuzzer/fuzzer/selection.py): select() takes no
arguments and returns the next arm, update(observation) receives the outcome of that pull. Here an
observation is the set of CWEs the detector reported, so policies can define their own reward.
"""
import math
from collections import Counter

import numpy as np


class SelectPolicy:
    name = "base"

    def __init__(self, n_arms: int, rng: np.random.Generator):
        self.n_arms = n_arms
        self.rng = rng
        self.t = 0
        self.pulls = np.zeros(n_arms)
        self.discovered: 'set[str]' = set()
        self.last_arm: int = None

    def select(self) -> int:
        raise NotImplementedError

    def update(self, observation: 'frozenset[str]') -> int:
        """Record the pull; returns the number of newly discovered CWEs."""
        new = observation - self.discovered
        self.discovered |= observation
        self.pulls[self.last_arm] += 1
        self.t += 1
        self._learn(observation, len(new))
        return len(new)

    def _learn(self, observation, n_new):
        pass

    def _argmax(self, scores) -> int:
        scores = np.asarray(scores, dtype=float)
        best = np.flatnonzero(scores == scores.max())
        return int(self.rng.choice(best))

    def _unpulled(self):
        idx = np.flatnonzero(self.pulls == 0)
        return int(self.rng.choice(idx)) if len(idx) else None


class RandomPolicy(SelectPolicy):
    name = "Random"

    def select(self):
        self.last_arm = int(self.rng.integers(self.n_arms))
        return self.last_arm


class RoundRobinPolicy(SelectPolicy):
    name = "Round-robin"

    def select(self):
        self.last_arm = self.t % self.n_arms
        return self.last_arm


class UCB1Policy(SelectPolicy):
    """UCB1 (Auer et al., 2002) on a scalar reward.

    reward="hit" is what GPTFuzz-style fuzzers optimise (did this pull find *anything*);
    reward="novel" uses the number of new CWEs, which is non-stationary (it decays as CWEs are found).
    """

    def __init__(self, n_arms, rng, reward: str = "hit", c: float = 1.0):
        super().__init__(n_arms, rng)
        self.reward, self.c = reward, c
        self.sums = np.zeros(n_arms)
        self.name = f"UCB1 ({'hit' if reward == 'hit' else 'novelty'} reward)"

    def select(self):
        a = self._unpulled()
        if a is None:
            bonus = self.c * np.sqrt(2 * math.log(self.t) / self.pulls)
            a = self._argmax(self.sums / self.pulls + bonus)
        self.last_arm = a
        return a

    def _learn(self, observation, n_new):
        r = float(len(observation) > 0) if self.reward == "hit" else float(n_new)
        self.sums[self.last_arm] += r


class EXP3Policy(SelectPolicy):
    """EXP3 (Auer et al., 2002) with reward min(#new CWEs, 1)."""
    name = "EXP3 (novelty reward)"

    def __init__(self, n_arms, rng, gamma: float = 0.1):
        super().__init__(n_arms, rng)
        self.gamma = gamma
        self.log_w = np.zeros(n_arms)
        self.probs = np.full(n_arms, 1 / n_arms)

    def select(self):
        w = np.exp(self.log_w - self.log_w.max())
        self.probs = (1 - self.gamma) * w / w.sum() + self.gamma / self.n_arms
        self.last_arm = int(self.rng.choice(self.n_arms, p=self.probs))
        return self.last_arm

    def _learn(self, observation, n_new):
        x_hat = min(n_new, 1) / self.probs[self.last_arm]
        self.log_w[self.last_arm] += self.gamma * x_hat / self.n_arms


class GoodUCBPolicy(SelectPolicy):
    """Good-UCB (Bubeck, Ernst & Garivier, 2013) for discovery.

    Index of arm i = (Good-Turing missing-mass estimate) + c * sqrt(2 log t / N_i), where the
    missing-mass estimate is (# CWEs seen exactly once so far, with that one sighting from arm i) / N_i.
    A CWE seen once is evidence the arm still has unseen mass; once it is seen again it stops counting.
    """

    def __init__(self, n_arms, rng, c: float = 0.5):
        super().__init__(n_arms, rng)
        self.c = c
        self.name = "Good-UCB" if c == 0.5 else f"Good-UCB c={c}"
        self.item_counts: Counter = Counter()
        self.first_owner: 'dict[str, int]' = {}
        self.singletons = np.zeros(n_arms)

    def select(self):
        a = self._unpulled()
        if a is None:
            missing_mass = self.singletons / self.pulls
            bonus = self.c * np.sqrt(2 * math.log(self.t) / self.pulls)
            a = self._argmax(missing_mass + bonus)
        self.last_arm = a
        return a

    def _learn(self, observation, n_new):
        for cwe in observation:
            self.item_counts[cwe] += 1
            if self.item_counts[cwe] == 1:
                self.first_owner[cwe] = self.last_arm
                self.singletons[self.last_arm] += 1
            elif self.item_counts[cwe] == 2:
                self.singletons[self.first_owner[cwe]] -= 1


class OraclePolicy(SelectPolicy):
    """Greedy oracle that knows every arm's snippet distribution: picks the arm with the highest
    expected number of new CWEs. Not achievable in practice; it is the reference curve."""
    name = "Oracle (greedy, knows distributions)"

    def __init__(self, n_arms, rng, env):
        super().__init__(n_arms, rng)
        self.env = env

    def select(self):
        self.last_arm = self._argmax([self.env.expected_new(a, self.discovered)
                                      for a in range(self.n_arms)])
        return self.last_arm

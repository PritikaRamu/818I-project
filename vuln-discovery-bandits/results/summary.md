# Experiment 1 results

horizon T=300, trials=200, arms=32 (8 languages x 4 prompt clusters), discovery ceiling=46 CWEs

## Distinct CWEs discovered (mean ± 95% CI)

| policy                               | CWEs@30    | CWEs@100   | CWEs@300   | % ceiling@300   |   hit rate@300 |
|:-------------------------------------|:-----------|:-----------|:-----------|:----------------|---------------:|
| Random                               | 11.9 ± 0.3 | 20.6 ± 0.3 | 30.4 ± 0.4 | 66%             |           0.66 |
| Round-robin                          | 12.8 ± 0.3 | 21.2 ± 0.3 | 30.7 ± 0.3 | 67%             |           0.65 |
| UCB1 (hit reward)                    | 13.1 ± 0.3 | 20.8 ± 0.3 | 28.6 ± 0.4 | 62%             |           0.77 |
| UCB1 (novelty reward)                | 13.1 ± 0.3 | 21.3 ± 0.3 | 30.8 ± 0.4 | 67%             |           0.66 |
| EXP3 (novelty reward)                | 11.9 ± 0.3 | 20.9 ± 0.3 | 30.2 ± 0.3 | 66%             |           0.66 |
| Good-UCB                             | 13.1 ± 0.3 | 21.2 ± 0.3 | 31.0 ± 0.3 | 67%             |           0.64 |
| Oracle (greedy, knows distributions) | 16.6 ± 0.3 | 28.6 ± 0.4 | 39.7 ± 0.3 | 86%             |           0.56 |

## Budget concentration

| policy                               |   top-5 arm share |   arms never pulled (mean) |
|:-------------------------------------|------------------:|---------------------------:|
| Random                               |              0.16 |                          0 |
| Round-robin                          |              0.17 |                          0 |
| UCB1 (hit reward)                    |              0.24 |                          0 |
| UCB1 (novelty reward)                |              0.18 |                          0 |
| EXP3 (novelty reward)                |              0.17 |                          0 |
| Good-UCB                             |              0.18 |                          0 |
| Oracle (greedy, knows distributions) |              0.44 |                          9 |

## Sensitivity to exploration constant c

| policy                |    c |   CWEs@30 |   CWEs@100 |   CWEs@300 |
|:----------------------|-----:|----------:|-----------:|-----------:|
| Good-UCB              | 0.1  |      12.9 |       21   |       30.2 |
| UCB1 (novelty reward) | 0.1  |      12.9 |       19.7 |       28.7 |
| Good-UCB              | 0.25 |      12.9 |       21.2 |       29.9 |
| UCB1 (novelty reward) | 0.25 |      12.9 |       20.2 |       29.3 |
| Good-UCB              | 0.5  |      12.9 |       21.3 |       30.5 |
| UCB1 (novelty reward) | 0.5  |      12.9 |       21.1 |       29.9 |
| Good-UCB              | 1    |      12.9 |       21.1 |       30.3 |
| UCB1 (novelty reward) | 1    |      12.9 |       21.3 |       30.6 |
| Good-UCB              | 2    |      12.9 |       21.4 |       30.4 |
| UCB1 (novelty reward) | 2    |      12.9 |       21   |       30.4 |

## Arm granularity ablation

|   arms | policy                               |   CWEs@30 |   CWEs@100 |   CWEs@300 |
|-------:|:-------------------------------------|----------:|-----------:|-----------:|
|      8 | Random                               |      11.9 |       22.2 |       31.4 |
|      8 | Good-UCB                             |      12.4 |       21.6 |       31.3 |
|      8 | Oracle (greedy, knows distributions) |      14.6 |       25.1 |       35.4 |
|     32 | Random                               |      11.9 |       20.6 |       30.3 |
|     32 | Good-UCB                             |      12.7 |       21.4 |       30.8 |
|     32 | Oracle (greedy, knows distributions) |      16.5 |       28.5 |       40.2 |

## Long horizon (T=1000, 50 trials)

| policy                |   CWEs@100 |   CWEs@300 |   CWEs@600 |   CWEs@1000 |
|:----------------------|-----------:|-----------:|-----------:|------------:|
| Random                |       20.8 |       30.8 |       36.7 |        40.4 |
| UCB1 (hit reward)     |       20.9 |       29   |       32.6 |        35.3 |
| UCB1 (novelty reward) |       21.9 |       31   |       36.6 |        39.7 |
| Good-UCB              |       21.2 |       30.8 |       36.3 |        39.9 |

## Where the oracle gap comes from (CWEs found by T=300, 100 trials)

| band                   |   CWEs in band |   Random |   Good-UCB |   Oracle |
|:-----------------------|---------------:|---------:|-----------:|---------:|
| common (>=20 snippets) |             16 |     15.8 |       15.8 |     16   |
| mid (4-19)             |             18 |     11.6 |       12.1 |     17.7 |
| rare (<=3)             |             12 |      2.9 |        2.9 |      6.3 |

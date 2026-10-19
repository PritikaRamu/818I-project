# Environment summary

- Snippets scanned: 1916 (scan errors: 0)
- Snippets with >=1 ICD finding: 1148 (59.9%)
- Distinct CWEs detectable in the whole pool (discovery ceiling): 46
- Distinct CWE labels in the dataset: 50
- Fraction of snippets where the ICD re-detects the dataset's own CWE label: 58.8%
- CWEs detected in <=3 snippets (the long tail): 12 -> CWE-22, CWE-79, CWE-209, CWE-276, CWE-306, CWE-312, CWE-319, CWE-330, CWE-335, CWE-521, CWE-770, CWE-908
- Arms: 32; CWEs found in exactly one arm: 13
- Spearman correlation between arm hit rate and arm distinct-CWE count: -0.05

## Per language

| language   |   snippets |   detection_rate |   distinct_cwes |   label_recovered |
|:-----------|-----------:|-----------------:|----------------:|------------------:|
| c          |        227 |            0.564 |              14 |             0.520 |
| cpp        |        259 |            0.556 |              14 |             0.514 |
| csharp     |        235 |            0.230 |               8 |             0.230 |
| java       |        229 |            0.550 |              10 |             0.550 |
| javascript |        249 |            0.301 |              11 |             0.301 |
| php        |        162 |            0.981 |              12 |             0.981 |
| python     |        351 |            0.735 |               7 |             0.735 |
| rust       |        204 |            1.000 |               7 |             1.000 |

## CWE frequency (number of snippets in which the ICD reports it)

| cwe      |   snippets |
|:---------|-----------:|
| CWE-120  |        132 |
| CWE-78   |        126 |
| CWE-327  |        115 |
| CWE-807  |        113 |
| CWE-328  |         98 |
| CWE-338  |         87 |
| CWE-798  |         78 |
| CWE-94   |         53 |
| CWE-676  |         43 |
| CWE-502  |         40 |
| CWE-290  |         33 |
| CWE-862  |         28 |
| CWE-89   |         26 |
| CWE-680  |         24 |
| CWE-119  |         23 |
| CWE-759  |         20 |
| CWE-95   |         17 |
| CWE-347  |         13 |
| CWE-665  |         12 |
| CWE-352  |         12 |
| CWE-345  |         10 |
| CWE-611  |          9 |
| CWE-185  |          9 |
| CWE-601  |          9 |
| CWE-377  |          7 |
| CWE-208  |          7 |
| CWE-295  |          7 |
| CWE-1240 |          6 |
| CWE-554  |          6 |
| CWE-589  |          6 |
| CWE-200  |          6 |
| CWE-242  |          5 |
| CWE-121  |          5 |
| CWE-323  |          4 |
| CWE-319  |          3 |
| CWE-79   |          3 |
| CWE-330  |          3 |
| CWE-335  |          2 |
| CWE-908  |          2 |
| CWE-312  |          2 |
| CWE-521  |          1 |
| CWE-770  |          1 |
| CWE-276  |          1 |
| CWE-209  |          1 |
| CWE-306  |          1 |
| CWE-22   |          1 |

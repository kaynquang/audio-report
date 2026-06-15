# Voice humanness analysis

Objective proxy metrics over the same script. Higher = more human-like.

## Ranking (composite humanness)

1. **styletts2** — 89.6/100
2. **index** — 89.5/100
3. **kokoro** — 80.9/100
4. **chatterbox** — 78.4/100
5. **original** — 51.7/100
6. **f5** — 35.4/100

## Per-criterion scores (0–1)

| engine | intonation | pitch_range | energy | phrasing | voicing | timbre | TOTAL |
|---|---|---|---|---|---|---|---|
| styletts2 | 0.80 | 0.86 | 0.98 | 0.98 | 0.92 | 0.94 | 89.6 |
| index | 0.91 | 0.74 | 1.00 | 0.99 | 0.68 | 0.99 | 89.5 |
| kokoro | 0.76 | 0.92 | 0.92 | 0.96 | 0.85 | 0.48 | 80.9 |
| chatterbox | 0.69 | 0.44 | 0.99 | 0.98 | 0.94 | 0.84 | 78.4 |
| original | 0.00 | 0.04 | 0.97 | 0.97 | 0.87 | 0.95 | 51.7 |
| f5 | 0.00 | 0.13 | 0.19 | 0.97 | 0.83 | 0.71 | 35.4 |

## Raw measurements

| engine | f0_mean_hz | f0_std_hz | f0_range_hz | f0_semitone_std | energy_dyn_db | pause_rate_per_s | voiced_ratio | centroid_hz | duration_s |
|---|---|---|---|---|---|---|---|---|---|
| original | 182.7 | 90.8 | 275.7 | 10.4 | 10.2 | 0.35 | 0.68 | 2722.9 | 40.3 |
| kokoro | 211.3 | 36.1 | 121.6 | 2.82 | 10.9 | 0.34 | 0.51 | 3374.7 | 29.4 |
| chatterbox | 250.4 | 71.1 | 213.1 | 4.82 | 9.83 | 0.36 | 0.65 | 2924.0 | 33.4 |
| f5 | 165.3 | 82.2 | 249.6 | 9.35 | 17.7 | 0.35 | 0.69 | 3093.3 | 37.4 |
| styletts2 | 204.4 | 36.3 | 111.6 | 2.93 | 9.87 | 0.36 | 0.54 | 2749.4 | 39.4 |
| index | 232.0 | 62.2 | 188.2 | 4.42 | 8.72 | 0.44 | 0.47 | 2592.3 | 25.2 |

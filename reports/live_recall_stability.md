# Live Recall Stability Check

This report repeats targeted replay for the five current live recall drift cases. It does not modify scorer, retrieval, provider, identity, or benchmark logic.

## Summary

- Runs per case: `5`
- Target cases: `nerf_2020`, `simclr_2020`, `alphafold_2021`, `raft_2020`, `monodepth2_2019`

## Aggregate Results

| Case | Top-3 success | Provider pool | Direct fetch | Raw search | Best rank | Worst rank | Aggregate classification | Recommendation |
|---|---:|---:|---:|---:|---:|---:|---|---|
| `nerf_2020` | `5/5` | `5/5` | `5/5` | `5/5` | `2` | `2` | `stable_top3` | No production fix recommended now; the full-benchmark miss looks like one-time live drift. |
| `simclr_2020` | `5/5` | `5/5` | `5/5` | `0/5` | `2` | `2` | `stable_top3` | No production fix recommended now; the full-benchmark miss looks like one-time live drift. Raw GitHub search is not always enough, but direct/canonical fetch recovered the official repo in this check. |
| `alphafold_2021` | `5/5` | `5/5` | `5/5` | `5/5` | `1` | `1` | `stable_top3` | No production fix recommended now; the full-benchmark miss looks like one-time live drift. |
| `raft_2020` | `5/5` | `5/5` | `5/5` | `5/5` | `1` | `1` | `stable_top3` | No production fix recommended now; the full-benchmark miss looks like one-time live drift. |
| `monodepth2_2019` | `5/5` | `5/5` | `5/5` | `5/5` | `3` | `3` | `stable_top3` | No production fix recommended now; the full-benchmark miss looks like one-time live drift. |

## Per-Run Results

### `nerf_2020`

| Run | Top-3 | Rank | Provider pool | Raw search | Canonical direct | Direct fetch | Top-3 candidates | Classification |
|---:|---|---:|---|---|---|---|---|---|
| 1 | yes | `2` | yes | yes | no | yes | `sxyu/pixel-nerf`, `bmild/nerf`, `ayaanzhaque/instruct-nerf2nerf` | `stable_top3` |
| 2 | yes | `2` | yes | yes | no | yes | `sxyu/pixel-nerf`, `bmild/nerf`, `ayaanzhaque/instruct-nerf2nerf` | `stable_top3` |
| 3 | yes | `2` | yes | yes | no | yes | `sxyu/pixel-nerf`, `bmild/nerf`, `ayaanzhaque/instruct-nerf2nerf` | `stable_top3` |
| 4 | yes | `2` | yes | yes | no | yes | `sxyu/pixel-nerf`, `bmild/nerf`, `ayaanzhaque/instruct-nerf2nerf` | `stable_top3` |
| 5 | yes | `2` | yes | yes | no | yes | `sxyu/pixel-nerf`, `bmild/nerf`, `ayaanzhaque/instruct-nerf2nerf` | `stable_top3` |

### `simclr_2020`

| Run | Top-3 | Rank | Provider pool | Raw search | Canonical direct | Direct fetch | Top-3 candidates | Classification |
|---:|---|---:|---|---|---|---|---|---|
| 1 | yes | `2` | yes | no | yes | yes | `andrewatanov/simclr-pytorch`, `google-research/simclr`, `sthalles/simclr` | `raw_search_drift_but_direct_fetch_recovers` |
| 2 | yes | `2` | yes | no | yes | yes | `andrewatanov/simclr-pytorch`, `google-research/simclr`, `sthalles/simclr` | `raw_search_drift_but_direct_fetch_recovers` |
| 3 | yes | `2` | yes | no | yes | yes | `andrewatanov/simclr-pytorch`, `google-research/simclr`, `sthalles/simclr` | `raw_search_drift_but_direct_fetch_recovers` |
| 4 | yes | `2` | yes | no | yes | yes | `andrewatanov/simclr-pytorch`, `google-research/simclr`, `sthalles/simclr` | `raw_search_drift_but_direct_fetch_recovers` |
| 5 | yes | `2` | yes | no | yes | yes | `andrewatanov/simclr-pytorch`, `google-research/simclr`, `sthalles/simclr` | `raw_search_drift_but_direct_fetch_recovers` |

### `alphafold_2021`

| Run | Top-3 | Rank | Provider pool | Raw search | Canonical direct | Direct fetch | Top-3 candidates | Classification |
|---:|---|---:|---|---|---|---|---|---|
| 1 | yes | `1` | yes | yes | yes | yes | `google-deepmind/alphafold`, `lucidrains/alphafold3-pytorch`, `urinx/alphafold_pytorch` | `stable_top3` |
| 2 | yes | `1` | yes | yes | yes | yes | `google-deepmind/alphafold`, `lucidrains/alphafold3-pytorch`, `urinx/alphafold_pytorch` | `stable_top3` |
| 3 | yes | `1` | yes | yes | yes | yes | `google-deepmind/alphafold`, `lucidrains/alphafold3-pytorch`, `urinx/alphafold_pytorch` | `stable_top3` |
| 4 | yes | `1` | yes | yes | yes | yes | `google-deepmind/alphafold`, `lucidrains/alphafold3-pytorch`, `urinx/alphafold_pytorch` | `stable_top3` |
| 5 | yes | `1` | yes | yes | yes | yes | `google-deepmind/alphafold`, `lucidrains/alphafold3-pytorch`, `urinx/alphafold_pytorch` | `stable_top3` |

### `raft_2020`

| Run | Top-3 | Rank | Provider pool | Raw search | Canonical direct | Direct fetch | Top-3 candidates | Classification |
|---:|---|---:|---|---|---|---|---|---|
| 1 | yes | `1` | yes | yes | no | yes | `princeton-vl/raft`, `dangeng/flowmag`, `david-zhao-1997/high-frequency-stereo-matching-network` | `stable_top3` |
| 2 | yes | `1` | yes | yes | no | yes | `princeton-vl/raft`, `dangeng/flowmag`, `david-zhao-1997/high-frequency-stereo-matching-network` | `stable_top3` |
| 3 | yes | `1` | yes | yes | no | yes | `princeton-vl/raft`, `dangeng/flowmag`, `david-zhao-1997/high-frequency-stereo-matching-network` | `stable_top3` |
| 4 | yes | `1` | yes | yes | no | yes | `princeton-vl/raft`, `dangeng/flowmag`, `david-zhao-1997/high-frequency-stereo-matching-network` | `stable_top3` |
| 5 | yes | `1` | yes | yes | no | yes | `princeton-vl/raft`, `dangeng/flowmag`, `david-zhao-1997/high-frequency-stereo-matching-network` | `stable_top3` |

### `monodepth2_2019`

| Run | Top-3 | Rank | Provider pool | Raw search | Canonical direct | Direct fetch | Top-3 candidates | Classification |
|---:|---|---:|---|---|---|---|---|---|
| 1 | yes | `3` | yes | yes | no | yes | `eddiespade/monodepth2`, `icaruswizard/monodepth2-paddle`, `nianticlabs/monodepth2` | `stable_top3` |
| 2 | yes | `3` | yes | yes | no | yes | `eddiespade/monodepth2`, `icaruswizard/monodepth2-paddle`, `nianticlabs/monodepth2` | `stable_top3` |
| 3 | yes | `3` | yes | yes | no | yes | `eddiespade/monodepth2`, `icaruswizard/monodepth2-paddle`, `nianticlabs/monodepth2` | `stable_top3` |
| 4 | yes | `3` | yes | yes | no | yes | `eddiespade/monodepth2`, `icaruswizard/monodepth2-paddle`, `nianticlabs/monodepth2` | `stable_top3` |
| 5 | yes | `3` | yes | yes | no | yes | `eddiespade/monodepth2`, `icaruswizard/monodepth2-paddle`, `nianticlabs/monodepth2` | `stable_top3` |

## Recommendation

- If a case is `5/5` Top-3 here, treat the full-benchmark miss as live GitHub drift rather than a production-logic failure.
- If future runs show provider-pool drops while direct fetch keeps succeeding, prefer a narrow canonical seed/direct-fetch hardening pass over Papers with Code.
- Only analyze scorer/ranking for a case that repeatedly has the official repo in provider pool but drops from final Top-3.

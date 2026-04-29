# Benchmark Error Analysis

## Run Status

- Source report: `reports/benchmark_report.json`
- Full benchmark completed: `yes`
- Command: `.\.venv\Scripts\python.exe scripts\evaluate_benchmark.py --top-k 3`
- Validation command: `.\.venv\Scripts\python.exe scripts\evaluate_benchmark.py --validate-only`
- Total benchmark entries: `53`
- Attempted live cases: `53`
- Evaluated live cases: `53`
- Unprocessed cases: `0`
- Failed cases: `0`
- Provider failed cases: `0`
- Rate limited cases: `0`
- Top-1 hit rate: `0.6981`
- Top-3 hit rate: `0.9057`
- Official repo top-1 hit rate: `0.6415`
- Official repo top-3 hit rate: `0.8491`
- Distractor ranked #1 rate: `0.0000`

## Current Refresh Summary

- This round only refreshed live full-benchmark metrics and updated reports; no scorer, retrieval, provider, identity mapping, or benchmark logic was modified.
- `yolov7_2022` now resolves through curated official identity to `WongKinYiu/yolov7` and is an Official Top-1 / Top-3 hit in the full benchmark.
- The previous `mask2former_2021` grouped-smoke drift does not reproduce in this full benchmark: `facebookresearch/mask2former` is rank `1`.
- Non-official `domain_library_implementation` identities still count only toward general expected-hit metrics and do not pollute Official Top-1/Top-3.

## Metric Change From Previous Full Live Run

| Metric | Previous full | Current full | Delta |
|---|---:|---:|---:|
| Top-1 hit rate | `0.6981` | `0.6981` | `+0.0000` |
| Top-3 hit rate | `0.9811` | `0.9057` | `-0.0754` |
| Official repo top-1 hit rate | `0.6415` | `0.6415` | `+0.0000` |
| Official repo top-3 hit rate | `0.9245` | `0.8491` | `-0.0754` |
| `official_repo_not_recalled` | `1` | `5` | `+4` |
| `expected_repo_not_recalled` | `1` | `5` | `+4` |
| Distractor ranked #1 rate | `0.0000` | `0.0000` | `+0.0000` |

## Targeted Fix Projection vs Full Result

- The YOLOv7 targeted projection is confirmed in full: `yolov7_2022` retrieves `wongkinyiu/yolov7` at rank `1` with `identity_type=official`.
- `dino_2021`, `bert_2018`, `mask2former_2021`, and `transformers_2020` remain Official Top-3 hits; `bert_2018` is still official rank `2`, not Top-1.
- `implicit_mf_2008` and `deepfm_2017` remain expected rank `1` via `domain_library_implementation` identities, while Official Top-3 remains `false` for both because neither benchmark entry has official repos.
- The full benchmark did not reach the projected `official_repo_not_recalled=0` state because five unrelated official repos drifted out of the live top-3 candidate set.

## Failure Summary By Cause

- `official_recalled_not_top1`: `11` cases; examples include `bert_2018`, `ddpm_2020`, `guided_diffusion_2021`, `grounding_dino_2023`, `orb_slam3_2020`, `colmap_2016`, `lightgcn_2020`, and `llava_2023`.
- `official_repo_not_recalled`: `5` cases: `nerf_2020`, `simclr_2020`, `alphafold_2021`, `raft_2020`, and `monodepth2_2019`.
- Separate no-official expected reproduction/library misses remain closed: `implicit_mf_2008` and `deepfm_2017` are still rank-1 expected hits.

## Remaining Misses

| Category | Count | Examples | Likely issue |
|---|---:|---|---|
| Official repo not recalled | `5` | `nerf_2020`, `simclr_2020`, `alphafold_2021`, `raft_2020`, `monodepth2_2019` | Live GitHub candidate volatility/direct-fetch coverage gap; none show provider failure or rate limit in this run. |
| Official recalled but not top-1 | `11` | `bert_2018`, `ddpm_2020`, `guided_diffusion_2021`, `grounding_dino_2023`, `orb_slam3_2020`, `colmap_2016`, `lightgcn_2020`, `llava_2023` | Official repo is present in top-3, but another repo ranks higher under live search/scoring. |
| Expected Top-3 miss | `5` | `nerf_2020`, `simclr_2020`, `alphafold_2021`, `raft_2020`, `monodepth2_2019` | Same as the current official recall misses. |
| No-official reproduction/library miss | `0` | none | Curated reproduction/domain-library identity continues to cover the two no-official expected targets. |

## Representative Cases

| Case | Full benchmark result | Retrieved top candidates | Expected/official repo | Note |
|---|---|---|---|---|
| `yolov7_2022` | official top-1 | `wongkinyiu/yolov7`, `dataxujing/yolov7`, `bubbliiiing/yolov7-pytorch` | `wongkinyiu/yolov7` | Curated official identity fixed the previous sole Official Top-3 miss in this case. |
| `mask2former_2021` | official top-1 | `facebookresearch/mask2former`, `luckydog-lhy/tensorrt_mask2former`, `yarrowqiao/semask-mask2former` | `facebookresearch/mask2former` | Current full benchmark confirms the earlier grouped-smoke miss was live drift. |
| `dino_2021` | official top-1 | `facebookresearch/dino`, `wangyian-me/architect_official_code`, `lucas-maes/le-wm` | `facebookresearch/dino` | Identity overmatch guard and archived official collision handling remain effective. |
| `bert_2018` | official top-3, not top-1 | `ymcui/chinese-bert-wwm`, `google-research/bert`, `bojone/bert4keras` | `google-research/bert` | Official recall holds; live ranking still favors a strong BERT variant first. |
| `implicit_mf_2008` | expected repo top-1 | `benfred/implicit`, `federicovaona99/collaborative_filtering_for_implicit_feedback_datasets`, `piyushpathak03/recommendation-systems` | `benfred/implicit` | Non-official domain-library identity works and is not counted as official. |
| `deepfm_2017` | expected repo top-1 | `shenweichen/deepctr`, `chenxijun1029/deepfm_with_pytorch`, `rmanluo/mamdr` | `shenweichen/deepctr` | Non-official domain-library identity works and is not counted as official. |
| `nerf_2020` | official not recalled | `quan-meng/gnerf`, `nvlabs/nvdiffrec`, `jia-lab-research/efficientnerf` | `bmild/nerf` | New/returned live recall miss unrelated to the YOLOv7 identity change. |
| `simclr_2020` | official not recalled | `spijkervet/simclr`, `leftthomas/simclr`, `sayakpaul/simclr-in-tensorflow-2` | `google-research/simclr` | New/returned live recall miss unrelated to the YOLOv7 identity change. |
| `alphafold_2021` | official not recalled | `model3dbio/alphafold3-conda-install`, `lucidrains/itransformer`, `hanziwww/alphafold3-gui` | `google-deepmind/alphafold` | New/returned live recall miss unrelated to the YOLOv7 identity change. |
| `raft_2020` | official not recalled | `mcg-nku/amt`, `yafeng19/hap-vr`, `depixels/tinyalign` | `princeton-vl/raft` | New/returned live recall miss unrelated to the YOLOv7 identity change. |
| `monodepth2_2019` | official not recalled | `icaruswizard/monodepth2-paddle`, `xxxvincent/monodepth2`, `fangget/tf-monodepth2` | `nianticlabs/monodepth2` | New/returned live recall miss unrelated to the YOLOv7 identity change. |

## Distractor Ranked #1 Analysis

- Current full benchmark result: no labeled distractor is ranked #1.
- The curated YOLOv7 official identity did not promote YOLO/Ultralytics distractors.
- Reproduction/domain-library identity still does not promote `recommenders-team/recommenders` or other labeled distractors to rank 1.

## Official Top-3 Semantics

- Official metrics continue to use only benchmark `official_repos`.
- `domain_library_implementation` identities count toward general expected-hit metrics only when they match `high_quality_reproduction_repos`.
- `implicit_mf_2008` and `deepfm_2017` remain general Top-1 hits while correctly leaving Official Top-1/Top-3 as `false` because those entries have no official repos.
- The current Official Top-3 drop is caused by five live official recall misses, not by reproduction/library identities being counted as official.

## Recommended Next Round

1. Do not enter Papers with Code yet; the immediate issue is live recall drift for five concrete official repos, and each should be diagnosed before adding another external provider.
2. Run targeted diagnostics for `nerf_2020`, `simclr_2020`, `alphafold_2021`, `raft_2020`, and `monodepth2_2019` to determine whether direct fetch, curated official identity, redirect handling, or live search volatility is responsible.
3. Keep Top-1 ranking work separate from recall repair; the 11 `official_recalled_not_top1` cases are a different problem class.

## Live Recall Drift Diagnostics

- Diagnostic artifacts: `reports/live_recall_drift_diagnostics.md` and `reports/live_recall_drift_diagnostics.json`.
- Scope: `nerf_2020`, `simclr_2020`, `alphafold_2021`, `raft_2020`, and `monodepth2_2019`; the diagnostic script replays current GitHub provider, retrieval profile, identity provider, enrichment, and scoring logic without changing production code.
- Classification summary: all five cases currently classify as `live_search_drift`, because targeted replay recalls and scores the official repo into Top-3 even though the latest full benchmark missed them.
- Current targeted replay official ranks: `nerf_2020` rank `2`, `simclr_2020` rank `2`, `alphafold_2021` rank `1`, `raft_2020` rank `1`, and `monodepth2_2019` rank `3`.
- Direct official fetch succeeds for all five cases; no repo renamed/redirect or identity-mismatch evidence was observed in this diagnostic pass.
- Raw/provider-pool notes: `nerf_2020`, `alphafold_2021`, `raft_2020`, and `monodepth2_2019` appear in raw GitHub query results; `simclr_2020` does not appear in raw search top results but is included through canonical direct fetch as `google-research/simclr`.
- Next recommendation: do not change scorer first and do not enter Papers with Code yet; first repeat targeted validation or run a narrow stability check for these five cases, then only consider curated official identity/direct-fetch hardening for cases that repeatedly disappear from live provider pools.

## Live Recall Stability Check

- Stability artifacts: `reports/live_recall_stability.md` and `reports/live_recall_stability.json`.
- Command: `python scripts/check_live_recall_stability.py --runs 5`.
- Result: all five cases are `5/5` Official Top-3 hits in repeated targeted replay, so the latest full-benchmark misses look like transient live GitHub drift rather than production-logic failures.
- Per-case ranks are stable across all five runs: `nerf_2020` rank `2`, `simclr_2020` rank `2`, `alphafold_2021` rank `1`, `raft_2020` rank `1`, and `monodepth2_2019` rank `3`.
- Provider-pool and direct-fetch success are also `5/5` for all five cases.
- Raw-search appearance is `5/5` for `nerf_2020`, `alphafold_2021`, `raft_2020`, and `monodepth2_2019`; `simclr_2020` is `0/5` in raw search because the current raw queries exclude its archived official repo, but canonical direct fetch recovers `google-research/simclr` in `5/5` runs.
- Next recommendation: do not change scorer, retrieval, provider, or identity yet. If future full benchmarks keep missing the same repo while targeted stability remains `5/5`, investigate benchmark-run timing/rate/live-result variability; only consider narrow direct-fetch hardening for cases that repeatedly drop from provider pool despite successful manual direct fetch.

## Current Decision

- Current recommendation: do not modify production logic.
- Current recommendation: do not connect Papers with Code.
- The system should be treated as a stable checkpoint: YOLOv7 is fixed, Mask2Former is stable in full benchmark, and the five latest full-run recall misses are `5/5` Official Top-3 hits under repeated targeted stability checks.
- Future work should only consider an extremely narrow hardening pass if the same official repository repeatedly disappears from provider pool while manual direct fetch continues to succeed.
- If the official repository remains in provider pool but repeatedly falls out of Top-3, run a separate score-focused diagnostic before making any scorer change.

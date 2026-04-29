# Benchmark Stabilization Summary

## Current Full Benchmark

- Source report: `reports/benchmark_report.json` / `reports/benchmark_report.md`.
- Full benchmark completed with `53` total, `53` attempted, `53` evaluated, `0` unprocessed, `0` failed, `0` provider failures, and `0` rate-limited cases.
- Current metrics: Top-1 `0.6981`, Top-3 `0.9057`, Official Top-1 `0.6415`, Official Top-3 `0.8491`, distractor ranked #1 `0.0000`.
- Current full-run `official_repo_not_recalled` / `expected_repo_not_recalled` cases are `nerf_2020`, `simclr_2020`, `alphafold_2021`, `raft_2020`, and `monodepth2_2019`.

## Completed Stabilization Work

- `yolov7_2022` is fixed in the full benchmark: curated official identity restores `wongkinyiu/yolov7` at rank `1`.
- `mask2former_2021` is rank `1` in the full benchmark, so the earlier grouped-smoke miss is best treated as live GitHub drift rather than a persistent logic failure.
- Official identity, redirect handling, reproduction/domain-library identity, DINO-style identity guard, and archived official collision handling remain in place from earlier phases.
- Non-official reproduction/domain-library identities still do not pollute Official Top-1 / Official Top-3 semantics.

## Live Recall Drift Diagnostics

- Diagnostic report: `reports/live_recall_drift_diagnostics.md`.
- All five current full-run official recall misses classify as `live_search_drift` under targeted replay.
- Targeted replay official ranks: `nerf_2020` rank `2`, `simclr_2020` rank `2`, `alphafold_2021` rank `1`, `raft_2020` rank `1`, and `monodepth2_2019` rank `3`.
- Direct official fetch succeeds for all five cases; no repo renamed/redirect or identity-mismatch evidence was observed.
- Raw search sees `nerf_2020`, `alphafold_2021`, `raft_2020`, and `monodepth2_2019`; `simclr_2020` is recovered by canonical direct fetch even when raw search does not surface the archived official repo.

## Stability Check

- Stability report: `reports/live_recall_stability.md`.
- Five repeated targeted runs show all five cases are `5/5` Official Top-3 hits.
- Provider pool success is `5/5` for all five cases.
- Manual direct fetch success is `5/5` for all five cases.
- Raw search appearance is `5/5` for `nerf_2020`, `alphafold_2021`, `raft_2020`, and `monodepth2_2019`; `simclr_2020` is `0/5` in raw search but `5/5` recovered by canonical direct fetch.
- Best/worst ranks are stable: `nerf_2020` `2/2`, `simclr_2020` `2/2`, `alphafold_2021` `1/1`, `raft_2020` `1/1`, and `monodepth2_2019` `3/3`.

## Current Decision

- Do not modify scorer now: the remaining full-run misses are not reproduced as repeated ranking/scoring failures in targeted replay.
- Do not modify retrieval profiles now: four of five cases are consistently visible in raw GitHub search, and the fifth is consistently recovered through canonical direct fetch.
- Do not modify GitHub provider logic now: provider-pool success is `5/5` for all five cases in the stability check.
- Do not modify identity mappings now: all current official repos are already concrete GitHub repositories and targeted replay restores them without adding new curated mappings.
- Do not connect Papers with Code now: the current issue is live GitHub result volatility around known official GitHub repos, not missing external project-page discovery.

## Next Trigger

- Treat the current system as a stable checkpoint.
- If a future full benchmark repeatedly misses the same official repo and targeted stability shows provider-pool drops, consider an extremely narrow direct-fetch hardening pass for that specific pattern.
- If a future case repeatedly has the official repo in provider pool but drops from Top-3, run score-focused diagnostics before touching scorer.
- If future misses involve unknown project pages or missing canonical GitHub identities, then reconsider Papers with Code; that is not the current evidence pattern.

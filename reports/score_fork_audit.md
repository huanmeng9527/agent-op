# Score / Fork Audit

## Scope

- Source report: `reports/benchmark_report.json`
- Target cases: `mmdetection_2019`, `lightgcn_2020`
- This is a read-only audit: no scorer, retrieval, provider, or identity logic was changed.
- The script fetches current GitHub metadata for the reported top-1 and official repos only; it does not run the full benchmark.

## Summary

| Case | Current top-3 | Official rank | Top-1 category | Why top-1 beats official | Worth next fix? |
|---|---|---:|---|---|---|
| `mmdetection_2019` | `allenai/mmdetection`, `open-mmlab/mmdetection`, `hhaandroid/mmdetection-mini` | `2` | same-slug owner collision | query/name identity +0.1200; asset signals +0.1000; official cap: incomplete_execution_cap. `allenai/mmdetection` uses the exact `mmdetection` slug under a canonical research owner, so it can look as relevant as `open-mmlab/mmdetection` even though the benchmark labels OpenMMLab as official. | yes, small targeted fix is worth considering |
| `lightgcn_2020` | `lucapantea/lightgcn`, `kuandeng/lightgcn`, `gusye1234/lightgcn-pytorch` | `3` | same-slug implementation collision | query/name identity +0.1200; asset signals +0.2000; tech stack +0.3333; role/canonical bonus +0.1000; official cap: archived_cap. `lucapantea/lightgcn` has the exact paper/project slug and ranks above the official `gusye1234/lightgcn-pytorch`; the labeled distractor `kuandeng/lightgcn` appears at rank 2, not rank 1. | maybe, but only after a targeted distractor/fork audit |

## Case Details

### `mmdetection_2019`

- Paper: MMDetection: Open MMLab Detection Toolbox and Benchmark
- Current top-3: `allenai/mmdetection`, `open-mmlab/mmdetection`, `hhaandroid/mmdetection-mini`
- Official repo: `open-mmlab/mmdetection`; rank: `2`
- Labeled distractors: `facebookresearch/detectron2`; distractor rank: `none`
- Top-1 classification: `same-slug owner collision`; top-1 is labeled distractor: `no`
- Top-1 metadata: fork=`True`, parent=`open-mmlab/mmdetection`, source=`open-mmlab/mmdetection`, stars=`0`, forks=`0`, archived=`True`
- Official metadata: fork=`False`, parent=`none`, source=`none`, stars=`32638`, forks=`9841`, archived=`False`
- Top-1 score: `score=0.7584`, `query=0.4700`, `assets=0.6200`, `freshness=1.0000`, `popularity=0.3500`, `role_bonus=0.2200`, `cap=archived_cap`
- Official score: `score=0.7500`, `query=0.3500`, `assets=0.5200`, `freshness=1.0000`, `popularity=1.0000`, `role_bonus=0.2200`, `cap=incomplete_execution_cap`
- Why top-1 wins: query/name identity +0.1200; asset signals +0.1000; official cap: incomplete_execution_cap. `allenai/mmdetection` uses the exact `mmdetection` slug under a canonical research owner, so it can look as relevant as `open-mmlab/mmdetection` even though the benchmark labels OpenMMLab as official.
- Worth fixing next: yes, small targeted fix is worth considering
- Minimal next action: Audit whether `allenai/mmdetection` is a fork/mirror/downstream copy; if confirmed, consider a narrow fork/mirror or canonical-owner tie-breaker rather than changing broad scoring weights.

### `lightgcn_2020`

- Paper: LightGCN: Simplifying and Powering Graph Convolution Network for Recommendation
- Current top-3: `lucapantea/lightgcn`, `kuandeng/lightgcn`, `gusye1234/lightgcn-pytorch`
- Official repo: `gusye1234/lightgcn-pytorch`; rank: `3`
- Labeled distractors: `kuandeng/lightgcn`; distractor rank: `2`
- Top-1 classification: `same-slug implementation collision`; top-1 is labeled distractor: `no`
- Top-1 metadata: fork=`False`, parent=`none`, source=`none`, stars=`5`, forks=`1`, archived=`False`
- Official metadata: fork=`False`, parent=`none`, source=`none`, stars=`1052`, forks=`283`, archived=`True`
- Top-1 score: `score=0.6289`, `query=0.4700`, `assets=0.6400`, `freshness=1.0000`, `popularity=0.1945`, `role_bonus=0.1000`, `cap=incomplete_execution_cap`
- Official score: `score=0.4412`, `query=0.3500`, `assets=0.4400`, `freshness=1.0000`, `popularity=0.7556`, `role_bonus=0.0000`, `cap=archived_cap`
- Why top-1 wins: query/name identity +0.1200; asset signals +0.2000; tech stack +0.3333; role/canonical bonus +0.1000; official cap: archived_cap. `lucapantea/lightgcn` has the exact paper/project slug and ranks above the official `gusye1234/lightgcn-pytorch`; the labeled distractor `kuandeng/lightgcn` appears at rank 2, not rank 1.
- Worth fixing next: maybe, but only after a targeted distractor/fork audit
- Minimal next action: Treat as a recommender-specific collision: first inspect same-slug third-party implementations and the rank-2 labeled distractor before adding any ranking policy.

## Minimal Next-Fix Suggestions

1. Start with `mmdetection_2019`: verify whether `allenai/mmdetection` is a fork/mirror/downstream copy, then consider a narrow same-slug owner-collision tie-breaker only if the evidence is stable.
2. For `lightgcn_2020`, avoid broad scoring changes; first audit same-slug recommender implementations and the rank-2 labeled distractor `kuandeng/lightgcn`.

# Reproduction Identity Analysis

## Scope

- Source benchmark: `benchmarks/paper_repro_benchmark.json`
- Source full benchmark report: `reports/benchmark_report.json`
- Target cases: `implicit_mf_2008`, `deepfm_2017`
- This is analysis only: no scorer, retrieval, provider, identity override, or benchmark logic was changed.
- Current global state: Top-1 `0.6981`, Top-3 `0.9623`, Official Top-3 `0.9434`, `official_repo_not_recalled=0`, distractor ranked #1 `0.0000`.

## Summary Recommendation

- Both remaining top-3 misses are no-official-label recommender cases where the benchmark target is a high-quality reproduction or domain library, not an official paper repository.
- Do not extend the current official paper-code identity model as-is; adding these repos under `official_repos` would blur benchmark semantics.
- If the next round implements a fix, prefer a small `identity_type` extension for curated reproduction/library identities over broad recommender retrieval or scorer changes.
- Papers with Code is not necessary for these two cases; both can be handled more safely with local, evidence-backed curated metadata.

## Case: `implicit_mf_2008`

### Benchmark Label

- Paper: `Collaborative Filtering for Implicit Feedback Datasets`
- Task: `recommender`
- Query: `Collaborative Filtering for Implicit Feedback Datasets paper code`
- `official_repos`: none
- Benchmark expected repo: `benfred/implicit`
- Expected repo field: `high_quality_reproduction_repos`
- Common distractor: `recommenders-team/recommenders`

### Current Full-Benchmark Result

- Current top-3: `federicovaona99/collaborative_filtering_for_implicit_feedback_datasets`, `piyushpathak03/recommendation-systems`, `silence28/collaborative-filtering-for-implicit-feedback-datasets`
- Expected repo in top-k: no
- Expected repo rank: not recalled in final top-3
- Provider status: GitHub provider succeeded; paper-code identity returned no match.
- Failure cause: `expected_repo_not_recalled`

### Target Classification

- Best label: `domain_library_implementation`
- Secondary label: `high_quality_reproduction`
- Not an official paper repo: the benchmark does not list `official_repos`, and the expected repo is a package/library for implicit-feedback recommendation algorithms rather than a paper-author repository.
- Not primarily a recommender framework: it is a focused implicit-feedback recommendation library, while `recommenders-team/recommenders` is the broader framework-style distractor.

### Why It Misses

- The paper title and repo slug differ substantially: `Collaborative Filtering for Implicit Feedback Datasets` vs `implicit`.
- The current query naturally retrieves repositories that repeat the full paper title, while `benfred/implicit` is branded as a mature library.
- This is not primarily a scorer issue because the expected repo is absent from top-3 rather than merely ranked below competitors.
- This is not an official-identity issue because there is no benchmark official repo to recall.

### External Evidence

- The `benfred/implicit` project is publicly presented as a Python package for implicit-feedback collaborative filtering and recommendation algorithms.
- The project documentation/repository connects the package to implicit-feedback recommendation methods rather than to a single official paper-release repository.
- Evidence source: `https://github.com/benfred/implicit`

### Design Judgment

- Recommended approach: curated reproduction/library identity.
- Do not use existing `official_repos` mapping semantics.
- Do not add broad aliases like `implicit` globally; that would be too ambiguous.
- Do not add a recommender-domain retrieval profile first; it may increase broad framework/distractor recall without a precise paper-to-target bridge.

## Case: `deepfm_2017`

### Benchmark Label

- Paper: `DeepFM: A Factorization-Machine based Neural Network for CTR Prediction`
- Task: `recommender`
- Query: `DeepFM Factorization-Machine Neural Network CTR Prediction code`
- `official_repos`: none
- Benchmark expected repo: `shenweichen/DeepCTR`
- Expected repo field: `high_quality_reproduction_repos`
- Common distractor: `recommenders-team/recommenders`

### Current Full-Benchmark Result

- Current top-3: `chenxijun1029/deepfm_with_pytorch`, `rmanluo/mamdr`, `mtsang/interaction_interpretability`
- Expected repo in top-k: no
- Expected repo rank: not recalled in final top-3
- Provider status: GitHub provider succeeded; paper-code identity returned no match.
- Failure cause: `expected_repo_not_recalled`

### Target Classification

- Best label: `domain_library_implementation`
- Secondary label: `recommender-system framework`
- Not an official paper repo: the benchmark does not list `official_repos`, and the expected repo is a broader CTR/deep-learning recommendation library containing DeepFM support.
- More framework-like than `benfred/implicit`: `DeepCTR` covers multiple CTR models rather than only the DeepFM paper target.

### Why It Misses

- The expected repo slug `DeepCTR` does not match the paper slug `DeepFM`.
- The query favors DeepFM-specific repositories, while the benchmark target is a broader domain library that implements DeepFM among other models.
- This is primarily a paper-to-domain-library identity gap, not a general ranking problem.
- The benchmark label is intentionally narrow: it rewards a mature library implementation rather than arbitrary DeepFM-specific repositories.

### External Evidence

- The `shenweichen/DeepCTR` project is publicly presented as a deep-learning CTR prediction package that includes model implementations such as DeepFM.
- Its project documentation and repository connect it to CTR model implementations, supporting the benchmark label as a high-quality domain-library implementation rather than an official paper repository.
- Evidence source: `https://github.com/shenweichen/DeepCTR`

### Design Judgment

- Recommended approach: curated reproduction/library identity.
- Do not use existing `official_repos` mapping semantics.
- Do not solve by boosting all `DeepCTR`/CTR or all recommender framework matches; that could promote broad frameworks over paper-specific targets.
- A recommender-domain retrieval profile can be considered later, but only after curated identities establish safe target semantics.

## Recommended Approach

| Option | Fit | Reason |
|---|---|---|
| Curated reproduction identity | best | Precisely bridges paper identity to benchmark-labeled reproduction/library repos without changing scorer behavior. |
| Recommender-domain retrieval profile | later | Could help broader recommender cases, but it is less precise and may promote framework distractors. |
| Benchmark policy adjustment | optional | The benchmark may want to explicitly separate official repos from high-quality reproduction/domain-library targets. |
| Temporarily leave unfixed | acceptable | Global Top-3 is already `0.9623`; these misses are not official recall failures. |

## Proposed `identity_type`

Add an explicit type field before adding these mappings:

- `official`: paper-author or project-official repository; existing curated identity behavior.
- `high_quality_reproduction`: evidence-backed reproduction target listed by the benchmark.
- `domain_library_implementation`: mature library/framework repo that implements the paper method but is not a paper-official repo.

For these two cases:

| Case | Repo | Suggested `identity_type` | Confidence |
|---|---|---|---|
| `implicit_mf_2008` | `benfred/implicit` | `domain_library_implementation` | `medium` |
| `deepfm_2017` | `shenweichen/DeepCTR` | `domain_library_implementation` | `medium-high` |

## Minimal Next-Round Implementation Plan

1. Extend curated identity schema with optional `identity_type`, keeping existing entries defaulted to `official`.
2. Add a separate `target_repos` or `repos` field for non-official identity targets, instead of overloading `official_repos`.
3. Let `search_paper_repos` inject these candidates through the existing GitHub enrichment/scoring path, as identity candidates with explicit evidence and type metadata.
4. Retain them into top-k only when they match benchmark `high_quality_reproduction_repos`, not as official hits.
5. Add targeted tests for `implicit_mf_2008` and `deepfm_2017`, plus a guard that arbitrary third-party reproduction repos are not treated as official.

## Directions Not Recommended

- Do not mark `benfred/implicit` or `shenweichen/DeepCTR` as official repositories.
- Do not add broad aliases such as `implicit`, `DeepCTR`, `CTR`, or `recommender` to the general retrieval profile without a case-level evidence bridge.
- Do not tune scorer weights for this stage; the expected repos are not in top-3, so this is a recall/identity-target problem.
- Do not add Papers with Code solely for these two cases; a small curated reproduction identity layer is simpler and more auditable.

## Risk Notes

- The main risk is semantic drift: arbitrary reproductions should not receive the same trust or output explanation as official paper repositories.
- `domain_library_implementation` should be presented as a benchmark-supported implementation target, not as an author-official release.
- Evidence should be stored per mapping and should explain why the repo implements or supports the paper method.
- Evaluation should separately report official recall and reproduction/library recall so Official Top-3 remains interpretable.

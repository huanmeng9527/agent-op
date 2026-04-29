# Architecture

This MVP follows a small but extensible MCP server layout.

```text
app/main.py
  -> app/server.py
    -> app/tools/paper_tools.py
      -> app/core/service.py
        -> app/providers/paper_code_identity.py
        -> app/providers/github.py
        -> app/ranking/scorer.py
        -> app/core/query_analyzer.py
```

## Main Flow

1. MCP host calls `search_paper_repos`, `inspect_paper_repo`, or `compare_paper_repos`.
2. Tool wrappers create Pydantic input models.
3. Service resolves lightweight paper metadata from arXiv, then analyzes the user query into paper title, venue/year, task, framework, and artifact hints.
4. Paper-code identity overrides map a small number of known paper identities to canonical repos or benchmark reproduction/library targets, carrying source, confidence, evidence, and `identity_type`.
5. GitHub provider direct-fetches identity repos, enriches them with the same README/root-tree path used by search candidates, and then normal scoring handles them. Non-official identity types are injected as reproduction/library candidates, not official paper repos.
6. Retrieval profiles expand the query into exact-title, official-code, paper-code, reproduction, framework, venue, and year GitHub searches.
7. GitHub provider fetches repository metadata, README, root tree, recursive tree paths, and selected config files for inspection.
8. Deep inspection extracts training/evaluation entries, dataset config references, lockfiles, checkpoint links, reproduction instructions, and paper links.
9. Inspection converts raw signals into readiness judgements: training, evaluation, environment reproducibility, and paper identity confidence.
10. Ranking scorer detects reproducibility assets, classifies repo role, applies risk penalties and score caps, then returns explainable evidence.
11. Service deduplicates, optionally filters unofficial reproductions, retains high-confidence identity candidates at the top-k boundary, and returns structured output with safety notes.
12. Compare turns inspection signals into action-oriented choices for direct reproduction, method reference, baseline use, and repositories to avoid.

## Extension Points

- Add providers under `app/providers/`, declare their capabilities, then register them in `ProviderRegistry`.
- Use `ProviderRegistry.for_capability(...)` when a future source supports search but not repository inspection.
- Add a Papers with Code identity provider by returning the same `repo`, `source`, `confidence`, `evidence`, and `identity_type` shape as `PaperCodeIdentityMatch`.
- Add more paper/task vocabularies in `app/core/query_analyzer.py`.
- Add retrieval strategies in `app/core/retrieval_profiles.py`.
- Add deeper file inspection in `app/core/inspection.py` and `GitHubProvider`.
- Add paper metadata sources under `app/providers/`.
- Replace or augment heuristic scoring in `app/ranking/scorer.py`.
- Expand benchmark coverage under `benchmarks/`.

## Reports

- `scripts/evaluate_benchmark.py` validates the benchmark set and writes live retrieval metrics to `reports/benchmark_report.md`.
- The same script supports targeted development runs with `--case-ids`, repeated `--case-id`, `--case-ids-file`, or `--identity-overrides`; targeted reports default to `reports/targeted_benchmark_report.*`.
- Full benchmark reports are for stage-level quality evaluation. Targeted reports are for changed-case regression checks and should not be treated as replacement full-benchmark metrics.
- `scripts/generate_case_studies.py` runs the search-inspect-compare workflow for five representative papers and writes `reports/case_studies.md`.

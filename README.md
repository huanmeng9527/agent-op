# Paper Reproduction Intelligence MCP Server

An MCP server for discovering, inspecting, and comparing public research-paper implementation and reproduction repositories.

It is designed for:

- finding paper code candidates on GitHub
- checking whether a repository has reproduction assets such as training, evaluation, configs, datasets, checkpoints, and environment files
- comparing multiple implementations before starting a clean-room reproduction
- returning structured, explainable outputs for MCP hosts

## Highlights

- Paper-aware GitHub retrieval expands a query into exact-title, official-code, paper-code, reproduction, framework, venue, and year variants.
- arXiv metadata lookup can resolve paper identity before GitHub retrieval.
- Curated paper-code identity overrides bridge known paper titles to canonical repository slugs when GitHub search cannot infer the project name, including explicit `identity_type` metadata for official repos versus reproduction/domain-library targets.
- Candidate enrichment reads README and root-tree signals before reranking.
- Deep inspection checks recursive tree entries, config samples, environment lockfiles, checkpoint links, reproduction instructions, and arXiv/DOI/BibTeX hints.
- Inspection now summarizes reproduction readiness as `training_readiness`, `evaluation_readiness`, `environment_reproducibility`, and `paper_identity_confidence`.
- Ranking uses explainable evidence, repository role classification, risk notes, reference utility, and score caps.
- Results are diversified by repository owner so one organization does not crowd out all top results.
- Compare outputs include direct-reproduction, method-reference, baseline, not-recommended decisions, plus a concise recommendation summary.
- Recommended workflow is `search_paper_repos -> inspect_paper_repo -> compare_paper_repos`.

## Safety Boundary

This project is for research planning and reproducibility assessment only. It should not be used to copy code, misrepresent experiment claims, or submit someone else's work as an original reproduction.

## Tools

`search_paper_repos`

- Searches GitHub repositories for paper implementations and reproductions
- Returns score, value level, confidence, repo role, tech stack, reproduction signals, reference utility, evidence, score-cap reason, risk note, and external identity source/confidence/type when available

`inspect_paper_repo`

- Inspects one GitHub repository in `owner/name` form
- Reads README, root tree, recursive tree paths, and a small config-file sample
- Detects training/evaluation/config/dataset/checkpoint/environment/paper-metadata signals
- Returns readiness judgements with levels, reasons, and evidence for reproduction planning

`compare_paper_repos`

- Compares 2 to 5 candidate repositories
- Ranks by paper fit, reproduction assets, and risk level
- Returns best overall candidate, weaknesses, decision fields, `decision_reasons`, and `recommendation_summary`

## Benchmark

The repository includes a starter benchmark at `benchmarks/paper_repro_benchmark.json` with 50+ labeled paper-code retrieval cases.

Validate the benchmark schema:

```bash
python scripts/evaluate_benchmark.py --validate-only
```

Run a live top-k retrieval benchmark:

```bash
python scripts/evaluate_benchmark.py --limit 10 --top-k 3
```

The script writes a readable markdown report to `reports/benchmark_report.md`. If `GITHUB_TOKEN` is missing, live evaluation is skipped with a clear prompt while `--validate-only` still works.

This repo also includes `data/paper_code_identity_overrides.json`, a deliberately small mapping for paper identity bridging. These curated entries are not ranking answers; they let the service direct-fetch externally identified repos, then pass those repos through the same GitHub enrichment and scoring path. Mappings without `identity_type` default to `official`; non-official mappings such as `domain_library_implementation` are treated as reproduction/library targets and must not be presented as official paper repos.

Run a targeted benchmark for changed cases instead of the full live set:

```bash
python scripts/evaluate_benchmark.py --case-ids stable_diffusion_2022,ddpm_2020,instant_ngp_2022,gaussian_splatting_2023,llava_2023 --top-k 3 --report-prefix identity
```

Or select all cases covered by the curated identity override file:

```bash
python scripts/evaluate_benchmark.py --identity-overrides --top-k 3 --report-prefix identity
```

Targeted reports default to `reports/targeted_benchmark_report.json` and `reports/targeted_benchmark_report.md`; `--report-prefix smoke_identity` writes `reports/smoke_identity_benchmark_report.json` and `.md`. Use targeted results for development regression checks only. They are not a replacement for the full benchmark metrics used for stage-level evaluation.

For the full benchmark, set `GITHUB_TOKEN` in the repository-root `.env` to avoid unauthenticated GitHub rate limits:

```powershell
Copy-Item .env.example .env
notepad .env
```

Or set it for the current PowerShell session:

```powershell
$env:GITHUB_TOKEN="ghp_your_token_here"
```

If you use `setx`, open a new PowerShell window before running Python; `setx` does not update already-running shells.

Generate five workflow case studies:

```powershell
.\.venv\Scripts\python.exe scripts\generate_case_studies.py
```

The case-study report is written to `reports/case_studies.md`.

## Quick Start

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -e .
```

Run with stdio:

```bash
python -m app.main --transport stdio
```

Run with Streamable HTTP:

```bash
python -m app.main --transport http --host 127.0.0.1 --port 8000 --mount-path /mcp
```

## Example Requests

Output snippets with the readiness and compare decision fields are in `examples/sample-output-snippets.json`.

`search_paper_repos`

```json
{
  "query": "Segment Anything paper code pytorch",
  "paper_title": "Segment Anything",
  "top_k": 5
}
```

`inspect_paper_repo`

```json
{
  "repo": "facebookresearch/segment-anything",
  "query": "Segment Anything paper code pytorch",
  "include_readme": true,
  "include_tree": true
}
```

`compare_paper_repos`

```json
{
  "repos": [
    "facebookresearch/segment-anything",
    "IDEA-Research/GroundingDINO"
  ],
  "query": "vision foundation model reproduction",
  "criteria": ["training code", "evaluation code", "environment reproducibility", "dataset/checkpoint guidance"]
}
```

## Architecture

```text
app/main.py
  -> app/server.py
    -> app/tools/
      -> app/core/
        -> app/providers/
        -> app/ranking/
        -> app/utils/
```

The design mirrors a vertical intelligence MCP server:

- `server`: registers MCP tools
- `tools`: wraps raw tool parameters into Pydantic models
- `core`: analyzes queries and orchestrates workflows
- `providers`: fetches GitHub data
- `providers/paper_code_identity.py`: resolves curated paper-to-code identity mappings before GitHub enrichment
- `ranking`: scores candidates with explainable rules
- `schemas`: keeps input and output contracts stable

Provider classes advertise capabilities such as `repository_search` and `repository_inspection`, so future providers can be added without assuming every source can inspect GitHub repositories.

## Current Limitations

- GitHub is the only provider in the MVP
- arXiv is used for lightweight paper identity metadata, not as a complete scholarly search backend
- Paper-code identity currently uses a small curated override file; a live Papers with Code provider can implement the same repo/source/confidence/evidence/identity_type contract later
- Scoring is heuristic and should be validated with your own benchmark set for your paper domains
- Deep inspection samples only a small number of config files; full repository parsing can be added later
- Paper identity matching is rule-based, not semantic
- Search can still be affected by GitHub API rate limits; set `GITHUB_TOKEN` for better reliability

# Paper Reproduction Retrieval Benchmark

This is a starter benchmark for measuring whether `search_paper_repos` retrieves useful paper-code candidates.

Each entry labels:

- `official_repos`: paper-author or canonical implementation repositories
- `high_quality_reproduction_repos`: strong third-party reproductions or widely used reimplementations
- `common_distractor_repos`: likely false positives, derivative projects, collections, or related libraries
- `expected_assets`: coarse labels for training/evaluation code expectations

Run a live benchmark:

```powershell
.\.venv\Scripts\python.exe scripts\evaluate_benchmark.py --limit 10 --top-k 3
```

The script reports top-1/top-3 hit rate, official top-1 hit rate, distractor-ranked-#1 rate, per-task summaries, and failure examples. It also writes `reports/benchmark_report.md`.

Set `GITHUB_TOKEN` in `.env` before running the full file to avoid GitHub API rate limits. Without a token, live evaluation is skipped by default; `--validate-only` still validates the benchmark locally.

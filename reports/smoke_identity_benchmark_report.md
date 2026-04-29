# Paper Reproduction Benchmark Report

- Benchmark file: `benchmarks\paper_repro_benchmark.json`
- Top-k: `3`
- Total cases: `2`
- Selected cases: `2`
- Attempted live cases: `2`
- Evaluated cases: `2`
- Unprocessed cases: `0`
- Failed cases: `0`
- Provider failed cases: `0`
- Rate limited cases: `0`

## Summary

- Top-1 hit rate: `1.0`
- Top-3 hit rate: `1.0`
- Official repo top-1 hit rate: `1.0`
- Official repo top-3 hit rate: `1.0`
- Distractor ranked #1 rate: `0.0`
- Stopped early: `False`
- Stop reason: `none`

## By Task

| Task | Cases | Top-1 | Top-3 | Distractor #1 |
|---|---:|---:|---:|---:|
| computer_vision | 2 | 1.0 | 1.0 | 0.0 |

## Per-Case Results

| Case | Top-1 | Top-3 | Official Top-1 | Official Top-3 | Distractor #1 | Cause | Retrieved |
|---|---:|---:|---:|---:|---:|---|---|
| `stable_diffusion_2022` | `True` | `True` | `True` | `True` | `False` | `success` | `compvis/latent-diffusion`, `compvis/stable-diffusion`, `abdur75648/utrnet-high-resolution-urdu-text-recognition` |
| `ddpm_2020` | `True` | `True` | `True` | `True` | `False` | `success` | `hojonathanho/diffusion`, `sak-h/pytorch-denoising-diffusion-probabilistic-models`, `musawir124/denoising-diffusion-probabilistic-models` |

## Failure Summary By Cause

- No failures or non-ideal rankings grouped by cause.

## Failure Summary By Task

- No provider failures or top-3 misses grouped by task.

## Failure Examples

- No failures or top-3 misses in this run.

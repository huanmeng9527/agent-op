# Paper Reproduction Benchmark Report

- Benchmark file: `benchmarks\paper_repro_benchmark.json`
- Top-k: `3`
- Total cases: `5`
- Selected cases: `5`
- Attempted live cases: `5`
- Evaluated cases: `5`
- Unprocessed cases: `0`
- Failed cases: `0`
- Provider failed cases: `0`
- Rate limited cases: `0`

## Summary

- Top-1 hit rate: `0.8`
- Top-3 hit rate: `1.0`
- Official repo top-1 hit rate: `0.4`
- Official repo top-3 hit rate: `0.6`
- Distractor ranked #1 rate: `0.0`
- Stopped early: `False`
- Stop reason: `none`

## By Task

| Task | Cases | Top-1 | Top-3 | Distractor #1 |
|---|---:|---:|---:|---:|
| computer_vision | 2 | 0.5 | 1.0 | 0.0 |
| nlp | 1 | 1.0 | 1.0 | 0.0 |
| recommender | 2 | 1.0 | 1.0 | 0.0 |

## Per-Case Results

| Case | Top-1 | Top-3 | Official Top-1 | Official Top-3 | Distractor #1 | Cause | Retrieved |
|---|---:|---:|---:|---:|---:|---|---|
| `vit_2020` | `False` | `True` | `False` | `True` | `False` | `official_recalled_not_top1` | `yunkun-zhang/cite`, `google-research/vision_transformer`, `purdue-m2/ai-face-fairnessbench` |
| `t5_2019` | `True` | `True` | `True` | `True` | `False` | `success` | `google-research/text-to-text-transfer-transformer`, `thu-ml/motus`, `yurakuratov/t5-experiments` |
| `stable_diffusion_2022` | `True` | `True` | `True` | `True` | `False` | `success` | `compvis/latent-diffusion`, `compvis/stable-diffusion`, `abdur75648/utrnet-high-resolution-urdu-text-recognition` |
| `implicit_mf_2008` | `True` | `True` | `False` | `False` | `False` | `success` | `benfred/implicit`, `federicovaona99/collaborative_filtering_for_implicit_feedback_datasets`, `piyushpathak03/recommendation-systems` |
| `deepfm_2017` | `True` | `True` | `False` | `False` | `False` | `success` | `shenweichen/deepctr`, `chenxijun1029/deepfm_with_pytorch`, `batch-norm/xdeepfm` |

## Failure Summary By Cause

- `official_recalled_not_top1`: 1 cases; examples: `vit_2020`

## Failure Summary By Task

- `computer_vision`: 1 cases; examples: `vit_2020`

## Failure Examples

- `vit_2020` An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale: official_recalled_not_top1; retrieved: yunkun-zhang/cite, google-research/vision_transformer, purdue-m2/ai-face-fairnessbench

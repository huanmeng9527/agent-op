# Paper Reproduction Benchmark Report

- Benchmark file: `benchmarks\paper_repro_benchmark.json`
- Top-k: `3`
- Total cases: `6`
- Selected cases: `6`
- Attempted live cases: `6`
- Evaluated cases: `6`
- Unprocessed cases: `0`
- Failed cases: `0`
- Provider failed cases: `0`
- Rate limited cases: `0`

## Summary

- Top-1 hit rate: `0.8333`
- Top-3 hit rate: `0.8333`
- Official repo top-1 hit rate: `0.5`
- Official repo top-3 hit rate: `0.5`
- Distractor ranked #1 rate: `0.0`
- Stopped early: `False`
- Stop reason: `none`

## By Task

| Task | Cases | Top-1 | Top-3 | Distractor #1 |
|---|---:|---:|---:|---:|
| computer_vision | 3 | 0.6667 | 0.6667 | 0.0 |
| nlp | 1 | 1.0 | 1.0 | 0.0 |
| recommender | 2 | 1.0 | 1.0 | 0.0 |

## Per-Case Results

| Case | Top-1 | Top-3 | Official Top-1 | Official Top-3 | Distractor #1 | Cause | Retrieved |
|---|---:|---:|---:|---:|---:|---|---|
| `dino_2021` | `False` | `False` | `False` | `False` | `False` | `official_repo_not_recalled` | `facebookresearch/dinov3`, `idea-research/dino`, `jiawei-yang/denoising-vit` |
| `vit_2020` | `True` | `True` | `True` | `True` | `False` | `success` | `google-research/vision_transformer`, `purdue-m2/ai-face-fairnessbench`, `brianpulfer/papersreimplementations` |
| `t5_2019` | `True` | `True` | `True` | `True` | `False` | `success` | `google-research/text-to-text-transfer-transformer`, `thu-ml/motus`, `yurakuratov/t5-experiments` |
| `stable_diffusion_2022` | `True` | `True` | `True` | `True` | `False` | `success` | `compvis/latent-diffusion`, `compvis/stable-diffusion`, `abdur75648/utrnet-high-resolution-urdu-text-recognition` |
| `implicit_mf_2008` | `True` | `True` | `False` | `False` | `False` | `success` | `benfred/implicit`, `federicovaona99/collaborative_filtering_for_implicit_feedback_datasets`, `piyushpathak03/recommendation-systems` |
| `deepfm_2017` | `True` | `True` | `False` | `False` | `False` | `success` | `shenweichen/deepctr`, `chenxijun1029/deepfm_with_pytorch`, `rmanluo/mamdr` |

## Failure Summary By Cause

- `official_repo_not_recalled`: 1 cases; examples: `dino_2021`

## Failure Summary By Task

- `computer_vision`: 1 cases; examples: `dino_2021`

## Failure Examples

- `dino_2021` Emerging Properties in Self-Supervised Vision Transformers: official_repo_not_recalled; retrieved: facebookresearch/dinov3, idea-research/dino, jiawei-yang/denoising-vit

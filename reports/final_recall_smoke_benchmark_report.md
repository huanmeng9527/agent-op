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

- Top-1 hit rate: `0.6667`
- Top-3 hit rate: `0.8333`
- Official repo top-1 hit rate: `0.3333`
- Official repo top-3 hit rate: `0.5`
- Distractor ranked #1 rate: `0.0`
- Stopped early: `False`
- Stop reason: `none`

## By Task

| Task | Cases | Top-1 | Top-3 | Distractor #1 |
|---|---:|---:|---:|---:|
| computer_vision | 3 | 0.6667 | 0.6667 | 0.0 |
| nlp | 1 | 0.0 | 1.0 | 0.0 |
| recommender | 2 | 1.0 | 1.0 | 0.0 |

## Per-Case Results

| Case | Top-1 | Top-3 | Official Top-1 | Official Top-3 | Distractor #1 | Cause | Retrieved |
|---|---:|---:|---:|---:|---:|---|---|
| `yolov7_2022` | `True` | `True` | `True` | `True` | `False` | `success` | `wongkinyiu/yolov7`, `dataxujing/yolov7`, `rizwanmunawar/yolov7-segmentation` |
| `dino_2021` | `True` | `True` | `True` | `True` | `False` | `success` | `facebookresearch/dino`, `idea-research/dino`, `ustc-time-series/timedart` |
| `bert_2018` | `False` | `True` | `False` | `True` | `False` | `official_recalled_not_top1` | `ymcui/chinese-bert-wwm`, `google-research/bert`, `jessevig/bertviz` |
| `mask2former_2021` | `False` | `False` | `False` | `False` | `False` | `official_repo_not_recalled` | `nazirnayal8/rba`, `luckydog-lhy/tensorrt_mask2former`, `yarrowqiao/semask-mask2former` |
| `implicit_mf_2008` | `True` | `True` | `False` | `False` | `False` | `success` | `benfred/implicit`, `federicovaona99/collaborative_filtering_for_implicit_feedback_datasets`, `piyushpathak03/recommendation-systems` |
| `deepfm_2017` | `True` | `True` | `False` | `False` | `False` | `success` | `shenweichen/deepctr`, `chenxijun1029/deepfm_with_pytorch`, `rmanluo/mamdr` |

## Failure Summary By Cause

- `official_recalled_not_top1`: 1 cases; examples: `bert_2018`
- `official_repo_not_recalled`: 1 cases; examples: `mask2former_2021`

## Failure Summary By Task

- `computer_vision`: 1 cases; examples: `mask2former_2021`
- `nlp`: 1 cases; examples: `bert_2018`

## Failure Examples

- `bert_2018` BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding: official_recalled_not_top1; retrieved: ymcui/chinese-bert-wwm, google-research/bert, jessevig/bertviz
- `mask2former_2021` Masked-attention Mask Transformer for Universal Image Segmentation: official_repo_not_recalled; retrieved: nazirnayal8/rba, luckydog-lhy/tensorrt_mask2former, yarrowqiao/semask-mask2former

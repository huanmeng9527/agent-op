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

- Top-1 hit rate: `0.2`
- Top-3 hit rate: `1.0`
- Official repo top-1 hit rate: `0.2`
- Official repo top-3 hit rate: `1.0`
- Distractor ranked #1 rate: `0.0`
- Stopped early: `False`
- Stop reason: `none`

## By Task

| Task | Cases | Top-1 | Top-3 | Distractor #1 |
|---|---:|---:|---:|---:|
| computer_vision | 3 | 0.0 | 1.0 | 0.0 |
| recommender | 1 | 0.0 | 1.0 | 0.0 |
| speech | 1 | 1.0 | 1.0 | 0.0 |

## Per-Case Results

| Case | Top-1 | Top-3 | Official Top-1 | Official Top-3 | Distractor #1 | Cause | Retrieved |
|---|---:|---:|---:|---:|---:|---|---|
| `vit_2020` | `False` | `True` | `False` | `True` | `False` | `official_recalled_not_top1` | `yunkun-zhang/cite`, `google-research/vision_transformer`, `purdue-m2/ai-face-fairnessbench` |
| `colmap_2016` | `False` | `True` | `False` | `True` | `False` | `official_recalled_not_top1` | `fangjinhuawang/patchmatchnet`, `colmap/colmap`, `xiaobaiiiiii/colmap-pcd` |
| `lightgcn_2020` | `False` | `True` | `False` | `True` | `False` | `official_recalled_not_top1` | `lucapantea/lightgcn`, `gusye1234/lightgcn-pytorch`, `geonwooko/mule` |
| `ultralytics_yolov8_2023` | `False` | `True` | `False` | `True` | `False` | `official_recalled_not_top1` | `bubbliiiing/yolov8-pytorch`, `dataxujing/yolov8`, `ultralytics/ultralytics` |
| `deepspeech2_2015` | `True` | `True` | `True` | `True` | `False` | `success` | `paddlepaddle/paddlespeech`, `fd873630/deep_speech_2_korean`, `lizhaokun/autosub-with-baidu-deepspeech2` |

## Failure Summary By Cause

- `official_recalled_not_top1`: 4 cases; examples: `vit_2020`, `colmap_2016`, `lightgcn_2020`, `ultralytics_yolov8_2023`

## Failure Summary By Task

- `computer_vision`: 3 cases; examples: `vit_2020`, `colmap_2016`, `ultralytics_yolov8_2023`
- `recommender`: 1 cases; examples: `lightgcn_2020`

## Failure Examples

- `vit_2020` An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale: official_recalled_not_top1; retrieved: yunkun-zhang/cite, google-research/vision_transformer, purdue-m2/ai-face-fairnessbench
- `colmap_2016` Structure-from-Motion Revisited: official_recalled_not_top1; retrieved: fangjinhuawang/patchmatchnet, colmap/colmap, xiaobaiiiiii/colmap-pcd
- `lightgcn_2020` LightGCN: Simplifying and Powering Graph Convolution Network for Recommendation: official_recalled_not_top1; retrieved: lucapantea/lightgcn, gusye1234/lightgcn-pytorch, geonwooko/mule
- `ultralytics_yolov8_2023` YOLOv8: official_recalled_not_top1; retrieved: bubbliiiing/yolov8-pytorch, dataxujing/yolov8, ultralytics/ultralytics

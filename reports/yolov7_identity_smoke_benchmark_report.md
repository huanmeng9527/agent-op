# Paper Reproduction Benchmark Report

- Benchmark file: `benchmarks\paper_repro_benchmark.json`
- Top-k: `3`
- Total cases: `1`
- Selected cases: `1`
- Attempted live cases: `1`
- Evaluated cases: `1`
- Unprocessed cases: `0`
- Failed cases: `0`
- Provider failed cases: `0`
- Rate limited cases: `0`

## Summary

- Top-1 hit rate: `0.0`
- Top-3 hit rate: `1.0`
- Official repo top-1 hit rate: `0.0`
- Official repo top-3 hit rate: `1.0`
- Distractor ranked #1 rate: `0.0`
- Stopped early: `False`
- Stop reason: `none`

## By Task

| Task | Cases | Top-1 | Top-3 | Distractor #1 |
|---|---:|---:|---:|---:|
| computer_vision | 1 | 0.0 | 1.0 | 0.0 |

## Per-Case Results

| Case | Top-1 | Top-3 | Official Top-1 | Official Top-3 | Distractor #1 | Cause | Retrieved |
|---|---:|---:|---:|---:|---:|---|---|
| `yolov7_2022` | `False` | `True` | `False` | `True` | `False` | `official_recalled_not_top1` | `dataxujing/yolov7`, `wongkinyiu/yolov7`, `bubbliiiing/yolov7-pytorch` |

## Failure Summary By Cause

- `official_recalled_not_top1`: 1 cases; examples: `yolov7_2022`

## Failure Summary By Task

- `computer_vision`: 1 cases; examples: `yolov7_2022`

## Failure Examples

- `yolov7_2022` YOLOv7: Trainable bag-of-freebies sets new state-of-the-art for real-time object detectors: official_recalled_not_top1; retrieved: dataxujing/yolov7, wongkinyiu/yolov7, bubbliiiing/yolov7-pytorch

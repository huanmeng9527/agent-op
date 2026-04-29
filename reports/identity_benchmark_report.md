# Paper Reproduction Benchmark Report

- Benchmark file: `C:\Users\ouyang\AppData\Local\Temp\paper_identity_subset.json`
- Top-k: `3`
- Total cases: `5`
- Attempted live cases: `5`
- Evaluated cases: `5`
- Unprocessed cases: `0`
- Failed cases: `0`
- Provider failed cases: `0`
- Rate limited cases: `0`

## Summary

- Top-1 hit rate: `0.6`
- Top-3 hit rate: `1.0`
- Official repo top-1 hit rate: `0.6`
- Official repo top-3 hit rate: `1.0`
- Distractor ranked #1 rate: `0.0`
- Stopped early: `False`
- Stop reason: `none`

## By Task

| Task | Cases | Top-1 | Top-3 | Distractor #1 |
|---|---:|---:|---:|---:|
| computer_vision | 5 | 0.6 | 1.0 | 0.0 |

## Failure Summary By Cause

- `official_recalled_not_top1`: 2 cases; examples: `instant_ngp_2022`, `llava_2023`

## Failure Summary By Task

- `computer_vision`: 2 cases; examples: `instant_ngp_2022`, `llava_2023`

## Failure Examples

- `instant_ngp_2022` Instant Neural Graphics Primitives with a Multiresolution Hash Encoding: official_recalled_not_top1; retrieved: liam6699/ts-nerf, nvlabs/instant-ngp, qsong2001/nerfprotector-code
- `llava_2023` Visual Instruction Tuning: official_recalled_not_top1; retrieved: microsoft/llava-med, pku-yuangroup/llava-cot, haotian-liu/llava

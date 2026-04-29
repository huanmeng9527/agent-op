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

- Top-1 hit rate: `0.4`
- Top-3 hit rate: `1.0`
- Official repo top-1 hit rate: `0.4`
- Official repo top-3 hit rate: `1.0`
- Distractor ranked #1 rate: `0.0`
- Stopped early: `False`
- Stop reason: `none`

## By Task

| Task | Cases | Top-1 | Top-3 | Distractor #1 |
|---|---:|---:|---:|---:|
| computer_vision | 2 | 0.5 | 1.0 | 0.0 |
| nlp | 1 | 1.0 | 1.0 | 0.0 |
| speech | 2 | 0.0 | 1.0 | 0.0 |

## Per-Case Results

| Case | Top-1 | Top-3 | Official Top-1 | Official Top-3 | Distractor #1 | Cause | Retrieved |
|---|---:|---:|---:|---:|---:|---|---|
| `t5_2019` | `True` | `True` | `True` | `True` | `False` | `success` | `google-research/text-to-text-transfer-transformer`, `thu-ml/motus`, `yurakuratov/t5-experiments` |
| `guided_diffusion_2021` | `False` | `True` | `False` | `True` | `False` | `official_recalled_not_top1` | `mchong6/gansnroses`, `openai/guided-diffusion`, `tkarras/progressive_growing_of_gans` |
| `midas_2020` | `True` | `True` | `True` | `True` | `False` | `success` | `isl-org/midas`, `mq-zhang1/hoidiffusion`, `kopperx/adv-diffusion` |
| `wav2vec2_2020` | `False` | `True` | `False` | `True` | `False` | `official_recalled_not_top1` | `ranchlai/wav2vec-2.0`, `speech-lab-iitm/ccc-wav2vec-2.0`, `facebookresearch/fairseq` |
| `hubert_2021` | `False` | `True` | `False` | `True` | `False` | `official_recalled_not_top1` | `wolfgitpr/hubertfa`, `ryota-komatsu/speaker_disentangled_hubert`, `facebookresearch/fairseq` |

## Failure Summary By Cause

- `official_recalled_not_top1`: 3 cases; examples: `guided_diffusion_2021`, `wav2vec2_2020`, `hubert_2021`

## Failure Summary By Task

- `computer_vision`: 1 cases; examples: `guided_diffusion_2021`
- `speech`: 2 cases; examples: `wav2vec2_2020`, `hubert_2021`

## Failure Examples

- `guided_diffusion_2021` Diffusion Models Beat GANs on Image Synthesis: official_recalled_not_top1; retrieved: mchong6/gansnroses, openai/guided-diffusion, tkarras/progressive_growing_of_gans
- `wav2vec2_2020` wav2vec 2.0: A Framework for Self-Supervised Learning of Speech Representations: official_recalled_not_top1; retrieved: ranchlai/wav2vec-2.0, speech-lab-iitm/ccc-wav2vec-2.0, facebookresearch/fairseq
- `hubert_2021` HuBERT: Self-Supervised Speech Representation Learning by Masked Prediction of Hidden Units: official_recalled_not_top1; retrieved: wolfgitpr/hubertfa, ryota-komatsu/speaker_disentangled_hubert, facebookresearch/fairseq

# Benchmark Error Analysis

## Run Status

- Source report: `reports/benchmark_report.json`
- Total benchmark entries: `53`
- Attempted live cases: `53`
- Evaluated live cases: `53`
- Unprocessed cases: `0`
- Provider failed cases: `0`
- Rate limited cases: `0`
- Top-1 hit rate: `0.4528`
- Top-3 hit rate: `0.5660`
- Official repo top-1 hit rate: `0.3774`
- Official repo top-3 hit rate: `0.4906`
- Distractor ranked #1 rate: `0.0000`

## Second-Round Fix Summary

- Added versioned/project alias extraction for names such as `SAM 2`, `Whisper`, `Graphormer`, `OpenCLIP`, `MMDetection`, and colon-prefixed project papers.
- Added a small canonical owner expansion for established research/project organizations such as `google-deepmind`, `huggingface`, `allenai`, `open-mmlab`, `mlfoundations`, `compvis`, and `paddlepaddle`.
- Split canonical research-org ranking boost into exact alias match and weaker prefix match, reducing the `sam2_2024` distractor side effect.

## Metric Change From Previous Live Run

| Metric | Previous | Current | Delta |
|---|---:|---:|---:|
| Top-1 hit rate | `0.2830` | `0.4528` | `+0.1698` |
| Top-3 hit rate | `0.4151` | `0.5660` | `+0.1509` |
| Official repo top-1 hit rate | `0.2264` | `0.3774` | `+0.1510` |
| Official repo top-3 hit rate | `0.3585` | `0.4906` | `+0.1321` |
| `official_repo_not_recalled` | `27` | `21` | `-6` |
| Distractor ranked #1 rate | `0.0189` | `0.0000` | `-0.0189` |

## Failure Summary By Cause

- `official_repo_not_recalled`: `21` cases; examples: `moco_2020`, `dino_2021`, `instant_ngp_2022`, `stylegan2_ada_2020`, `bert_2018`, `t5_2019`, `stable_diffusion_2022`, `ddpm_2020`
- `official_recalled_not_top1`: `6` cases; examples: `mae_2021`, `nerf_2020`, `grounding_dino_2023`, `monodepth2_2019`, `orb_slam3_2020`, `colmap_2016`
- `expected_repo_not_recalled`: `2` cases; examples: `implicit_mf_2008`, `deepfm_2017`
- `expected_recalled_not_top1`: `1` case; example: `simclr_2020`

## Remaining Official Repo Misses

| Category | Count | Examples | Likely issue |
|---|---:|---|---|
| Direct owner + alias exists, but ranking/top-k still misses | `8` | `moco_2020`, `dino_2021`, `stylegan2_ada_2020`, `bert_2018`, `mask2former_2021`, `fairseq_2019`, `transformers_2020`, `mmdetection_2019` | Official repo is discoverable by owner/name, but asset/popularity/search signals still let forks or adjacent projects occupy top-3. |
| Canonical owner covered, but alias/repo-name mismatch | `7` | `instant_ngp_2022`, `t5_2019`, `stable_diffusion_2022`, `guided_diffusion_2021`, `deepspeech2_2015`, `wav2vec2_2020`, `hubert_2021` | Paper title or query alias does not map cleanly to the official repo slug, often requiring project pages or Papers with Code metadata. |
| Requires external project-page/provider or benchmark-specific mapping | `4` | `ddpm_2020`, `gaussian_splatting_2023`, `lightgcn_2020`, `ultralytics_yolov8_2023` | GitHub search alone does not expose the benchmark-preferred repo without an external identity source or curated mapping. |
| Alias exists, but owner is outside canonical fetch list | `2` | `midas_2020`, `llava_2023` | Owner is a lab or individual account not safe to add broadly without stronger external identity evidence. |

## Distractor Ranked #1 Analysis

- Previous distractor case: `sam2_2024`
- Cause: `Segment Anything` phrase aliases placed `facebookresearch/segment-anything` ahead of the newer `facebookresearch/sam2` repo.
- Current result: no benchmark entry has a labeled distractor ranked #1.
- Interpretation: versioned acronym aliases fixed the concrete side effect without adding a broad distractor penalty.

## Representative Remaining Failures

| Case | Cause | Retrieved top candidates | Expected repos | Likely next action |
|---|---|---|---|---|
| `moco_2020` | `official_repo_not_recalled` | `bl0/moco`, `leftthomas/moco`, `linusericsson/ssl-transfer` | `facebookresearch/moco` | Investigate scoring/caps for direct-fetched official repos versus popular reproductions. |
| `dino_2021` | `official_repo_not_recalled` | `facebookresearch/dinov3`, `idea-research/dino`, `jiawei-yang/denoising-vit` | `facebookresearch/dino` | Prefer exact repo alias over newer same-owner prefix matches more strongly. |
| `stylegan2_ada_2020` | `official_repo_not_recalled` | `nvlabs/stylegan2-ada`, `nihalsid/stylegan2-ada-3d-texture`, `woctezuma/steam-stylegan2-ada` | `nvlabs/stylegan2-ada-pytorch` | Inspect why exact direct fetch does not survive top-3; likely asset/cap or archived metadata interaction. |
| `stable_diffusion_2022` | `official_repo_not_recalled` | high-resolution image repos unrelated to `latent-diffusion` | `compvis/latent-diffusion`, `compvis/stable-diffusion` | Needs paper metadata/project-page mapping from `Latent Diffusion Models` to `stable-diffusion`. |
| `llava_2023` | `official_repo_not_recalled` | `microsoft/llava-med`, `pku-yuangroup/llava-cot`, `llava-vl/llava-plus-codebase` | `haotian-liu/llava` | Needs external identity evidence before adding individual-owner direct fetches. |

## Recommended Next Round

1. Audit candidate-level scores for the 8 “direct owner + alias exists” cases before changing weights again.
2. Add an external paper-code identity source such as Papers with Code or project-page extraction for alias/repo-name mismatch cases.
3. Avoid broad individual-owner expansions until external evidence confirms the owner-paper relationship.

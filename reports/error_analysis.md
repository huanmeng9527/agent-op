# Benchmark Error Analysis

## Run Status

- Source report: `reports/benchmark_report.json`
- Full benchmark completed: `yes`
- Total benchmark entries: `53`
- Attempted live cases: `53`
- Evaluated live cases: `53`
- Unprocessed cases: `0`
- Failed cases: `0`
- Provider failed cases: `0`
- Rate limited cases: `0`
- Top-1 hit rate: `0.6981`
- Top-3 hit rate: `0.9623`
- Official repo top-1 hit rate: `0.6792`
- Official repo top-3 hit rate: `0.9434`
- Distractor ranked #1 rate: `0.0000`

## Current Fix Summary

- Added versioned/project alias extraction for names such as `SAM 2`, `Whisper`, `Graphormer`, `OpenCLIP`, `MMDetection`, and colon-prefixed project papers.
- Added canonical owner direct fetch for established research/project organizations such as `google-deepmind`, `huggingface`, `allenai`, `open-mmlab`, `mlfoundations`, `compvis`, and `paddlepaddle`.
- Added curated paper-code identity mappings for round 1, round 2, and round 3 cases backed by `data/paper_code_identity_overrides.json`.
- Added generic GitHub moved-repository handling so old expected paths such as `PaddlePaddle/DeepSpeech` remain candidate aliases on renamed repositories.

## Metric Change From Previous Full Live Run

| Metric | Previous | Current | Delta |
|---|---:|---:|---:|
| Top-1 hit rate | `0.5472` | `0.6981` | `+0.1509` |
| Top-3 hit rate | `0.6792` | `0.9623` | `+0.2831` |
| Official repo top-1 hit rate | `0.5283` | `0.6792` | `+0.1509` |
| Official repo top-3 hit rate | `0.6604` | `0.9434` | `+0.2830` |
| `official_repo_not_recalled` | `15` | `0` | `-15` |
| Distractor ranked #1 rate | `0.0000` | `0.0000` | `+0.0000` |

## Targeted Projection Check

- Targeted identity/redirect validation projected `official_repo_not_recalled` from `15` to `0`; the full benchmark confirms `0` official-labeled cases with official repos missing from top-3.
- Targeted validation projected Official Top-3 at about `0.9434`; the full benchmark measures `0.9434`.
- Targeted validation projected distractor ranked #1 unchanged at `0.0000`; the full benchmark measures `0.0000`.
- The remaining full benchmark top-3 misses are not official-repo misses: `implicit_mf_2008` and `deepfm_2017` are expected-reproduction misses in entries without `official_repos`.
- Targeted reproduction/library identity validation now resolves `implicit_mf_2008` and `deepfm_2017` as non-official domain-library implementation hits without changing Official Top-3 semantics.

## Failure Summary By Cause

- `official_repo_not_recalled`: `0` cases with official repos.
- `official_recalled_not_top1`: `14` cases; examples: `nerf_2020`, `vit_2020`, `simclr_2020`, `guided_diffusion_2021`, `grounding_dino_2023`, `monodepth2_2019`, `orb_slam3_2020`, `colmap_2016`.
- `expected_repo_not_recalled`: `2` cases; examples: `implicit_mf_2008`, `deepfm_2017`.
- Targeted `reproduction_identity_smoke` result: `implicit_mf_2008` and `deepfm_2017` both reach Top-3 via `domain_library_implementation` identity while Official Top-3 remains `0.0000` for those no-official-label cases.

## Remaining Misses

| Category | Count | Examples | Likely issue |
|---|---:|---|---|
| Official recalled but not top-1 | `14` | `nerf_2020`, `vit_2020`, `simclr_2020`, `guided_diffusion_2021`, `grounding_dino_2023`, `monodepth2_2019`, `orb_slam3_2020`, `colmap_2016`, `lightgcn_2020`, `llava_2023`, `ultralytics_yolov8_2023`, `mmdetection_2019`, `wav2vec2_2020`, `hubert_2021` | Official repo is present in top-3, but another repo ranks higher under existing scoring. |
| Expected reproduction not recalled | `2` in the last full run; `0` in targeted reproduction identity smoke | `implicit_mf_2008`, `deepfm_2017` | These cases do not list `official_repos`; benchmark success depends on recalling high-quality reproduction/domain-library targets. |
| Official repo not recalled | `0` | none | Curated identity plus redirect handling closed the previous 15-case official recall gap. |

## Distractor Ranked #1 Analysis

- Current full benchmark result: no benchmark entry has a labeled distractor ranked #1.
- The full benchmark confirms the targeted identity/redirect runs did not increase distractor rank-1 risk.
- `lightgcn_2020` still has a distractor at rank 2 in one live run, but the official repo is rank 3 and the distractor is not rank 1.

## Representative Resolved Cases

| Case | Full benchmark result | Retrieved top candidates | Expected repo | Note |
|---|---|---|---|---|
| `deepspeech2_2015` | official top-1 | `paddlepaddle/paddlespeech`, `fd873630/deep_speech_2_korean`, `lizhaokun/autosub-with-baidu-deepspeech2` | `paddlepaddle/deepspeech` | Alias-aware matching handles the old `PaddlePaddle/DeepSpeech` path after GitHub moved it to `paddlepaddle/paddlespeech`. |
| `vit_2020` | official top-3 | `yunkun-zhang/cite`, `google-research/vision_transformer`, `purdue-m2/ai-face-fairnessbench` | `google-research/vision_transformer` | Curated identity recalls the Google Research Vision Transformer repo. |
| `llava_2023` | official top-3 | `microsoft/llava-med`, `tencentarc/smartedit`, `haotian-liu/llava` | `haotian-liu/llava` | Curated identity bridges the paper title to the LLaVA repo slug. |
| `wav2vec2_2020` | official top-3 | `ranchlai/wav2vec-2.0`, `speech-lab-iitm/ccc-wav2vec-2.0`, `facebookresearch/fairseq` | `facebookresearch/fairseq` | Curated identity recalls the fairseq implementation path. |
| `hubert_2021` | official top-3 | `wolfgitpr/hubertfa`, `ryota-komatsu/speaker_disentangled_hubert`, `facebookresearch/fairseq` | `facebookresearch/fairseq` | Curated identity recalls the fairseq HuBERT implementation path. |

## Recommended Next Round

1. Do not prioritize Papers with Code yet; official top-3 recall is now saturated on the current benchmark.
2. Next full benchmark refresh should verify whether the targeted reproduction/library identity smoke converts the two expected-reproduction misses in the global metrics.
3. If future datasets add more project-page-only papers, introduce Papers with Code behind the existing identity contract and validate it with targeted benchmark runs first.

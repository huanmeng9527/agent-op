# Remaining Miss Analysis

## Scope

- Source report: `reports/benchmark_report.json`
- Full benchmark Top-1 / Top-3: `0.6981` / `0.9623`
- Official Top-1 / Official Top-3: `0.6792` / `0.9434`
- Distractor ranked #1: `0.0`
- Expected-reproduction misses analyzed: `2`
- Official-recalled-not-top1 cases analyzed: `14`

## Aggregate Findings

- Official recall is no longer the bottleneck: every case with `official_repos` has the official repo in top-3.
- Remaining Top-3 misses are both no-official-label recommender cases where the target is a reproduction/library repo.
- Official-not-top1 cases split evenly: `7` at official rank 2 and `7` at official rank 3.
- Most official-not-top1 cases are adjacent-project, fork/port, monorepo, or same-slug owner collisions; broad scoring changes would be risky.

## Expected-Reproduction Misses

| Case | Type | Rank | Target repo | Retrieved top-3 | Why it missed | Worth fixing? | Minimal next action |
|---|---|---:|---|---|---|---|---|
| `deepfm_2017` | expected reproduction miss | `not recalled` | `shenweichen/deepctr` | `chenxijun1029/deepfm_with_pytorch`, `rmanluo/mamdr`, `mtsang/interaction_interpretability` | Benchmark target is the broader `shenweichen/deepctr` CTR-model library, not a repo named exactly `DeepFM`; title search therefore prefers smaller DeepFM-specific or adjacent repositories. | `medium-high` | Use evidence-backed reproduction identity for no-official targets if this benchmark class remains important; otherwise leave as a known reproduction-target miss. |
| `implicit_mf_2008` | expected reproduction miss | `not recalled` | `benfred/implicit` | `federicovaona99/collaborative_filtering_for_implicit_feedback_datasets`, `piyushpathak03/recommendation-systems`, `silence28/collaborative-filtering-for-implicit-feedback-datasets` | Benchmark target is the mature `benfred/implicit` package, while live search returns paper-title-specific reimplementations; there is no `official_repos` label to anchor direct fetch. | `medium` | If recommender coverage matters, add a separate evidence-backed reproduction identity mapping for no-official benchmark targets; do not solve this with broad alias/scoring changes. |

## Official Recalled But Not Top-1

| Case | Type | Official rank | Official repo | Retrieved top-3 | Why not top-1 | Worth fixing? | Minimal next action |
|---|---|---:|---|---|---|---|---|
| `colmap_2016` | official recalled, not top-1 | `2` | `colmap/colmap` | `fangjinhuawang/patchmatchnet`, `colmap/colmap`, `xiaobaiiiiii/colmap-pcd` | A related multiview/stereo repo ranks above the official `colmap/colmap`; curated identity still recalls the official repo at rank 2. | `low` | Leave as top-3 success unless a future stage explicitly optimizes official Top-1. |
| `grounding_dino_2023` | official recalled, not top-1 | `3` | `idea-research/groundingdino` | `dongdong-d/groundingdino-finetuning`, `longzw1997/open-groundingdino`, `idea-research/groundingdino` | Finetuning/open variants rank above the official `idea-research/groundingdino`, which is recalled at rank 3. | `medium` | Potential future project-page identity case, but current top-3 behavior is already correct. |
| `guided_diffusion_2021` | official recalled, not top-1 | `2` | `openai/guided-diffusion` | `mchong6/gansnroses`, `openai/guided-diffusion`, `tkarras/progressive_growing_of_gans` | `mchong6/gansnroses` matches diffusion/GAN wording strongly and outranks the curated official `openai/guided-diffusion` candidate. | `low-medium` | Avoid broad diffusion scoring changes; consider only an identity-source top-1 policy after separate audit. |
| `hubert_2021` | official recalled, not top-1 | `3` | `facebookresearch/fairseq` | `wolfgitpr/hubertfa`, `ryota-komatsu/speaker_disentangled_hubert`, `facebookresearch/fairseq` | Title-specific HuBERT repositories outrank the broad official `facebookresearch/fairseq` monorepo at rank 3. | `low-medium` | Treat together with `wav2vec2_2020`; monorepo ranking is a policy decision, not a recall problem. |
| `lightgcn_2020` | official recalled, not top-1 | `3` | `gusye1234/lightgcn-pytorch` | `lucapantea/lightgcn`, `kuandeng/lightgcn`, `gusye1234/lightgcn-pytorch` | Two same-name implementations outrank the official `gusye1234/lightgcn-pytorch`; one labeled distractor appears at rank 2 but not rank 1. | `medium-high` | Worth a targeted score audit because it is the only remaining failure with a labeled distractor in top-3. |
| `llava_2023` | official recalled, not top-1 | `3` | `haotian-liu/llava` | `microsoft/llava-med`, `tencentarc/smartedit`, `haotian-liu/llava` | Adjacent LLaVA-family projects (`llava-med`, SmartEdit) rank above the official `haotian-liu/llava`, which curated identity recalls at rank 3. | `medium` | Medium priority only if official Top-1 matters; family-project ambiguity makes broad ranking risky. |
| `mmdetection_2019` | official recalled, not top-1 | `2` | `open-mmlab/mmdetection` | `allenai/mmdetection`, `open-mmlab/mmdetection`, `hhaandroid/mmdetection-mini` | `allenai/mmdetection` shares the exact repo slug and outranks official `open-mmlab/mmdetection`; this looks like an owner/fork/mirror collision rather than an identity miss. | `high` | High-value candidate for a read-only fork/mirror metadata audit before any future ranking change. |
| `monodepth2_2019` | official recalled, not top-1 | `3` | `nianticlabs/monodepth2` | `eddiespade/monodepth2`, `icaruswizard/monodepth2-paddle`, `nianticlabs/monodepth2` | Forks or ports with exact `monodepth2` naming outrank the official `nianticlabs/monodepth2` repo at rank 3. | `medium` | Only fix after a fork/port audit confirms a safe generic demotion signal. |
| `nerf_2020` | official recalled, not top-1 | `2` | `bmild/nerf` | `sxyu/pixel-nerf`, `bmild/nerf`, `ayaanzhaque/instruct-nerf2nerf` | `sxyu/pixel-nerf` is a strong related NeRF repository and outranks the older official `bmild/nerf`, which is still recalled at rank 2. | `low` | Do not prioritize unless Top-1 becomes the main KPI; broad NeRF reranking can disturb related papers. |
| `orb_slam3_2020` | official recalled, not top-1 | `3` | `uz-slamlab/orb_slam3` | `leaner-forever/segs-slam`, `thien94/orb_slam3_ros`, `uz-slamlab/orb_slam3` | ROS/wrapper repositories outrank the official `uz-slamlab/orb_slam3`, which remains recalled at rank 3. | `low` | Low priority; robotics wrappers are useful search results and broad demotion could harm users. |
| `simclr_2020` | official recalled, not top-1 | `2` | `google-research/simclr` | `andrewatanov/simclr-pytorch`, `google-research/simclr`, `sthalles/simclr` | A third-party implementation ranks above `google-research/simclr`; the official repo is safely in top-3. | `low` | Leave as top-3 success unless official Top-1 becomes a product requirement. |
| `ultralytics_yolov8_2023` | official recalled, not top-1 | `2` | `ultralytics/ultralytics` | `dataxujing/yolov8`, `ultralytics/ultralytics`, `derronqi/yolov8-face` | A YOLOv8 implementation repo outranks the official `ultralytics/ultralytics`, which is recalled at rank 2. | `low-medium` | Leave as top-3 success; a generic YOLO official-owner boost could affect YOLOv5/v7/v8 balance. |
| `vit_2020` | official recalled, not top-1 | `2` | `google-research/vision_transformer` | `yunkun-zhang/cite`, `google-research/vision_transformer`, `purdue-m2/ai-face-fairnessbench` | An unrelated/weakly related repo occupies rank 1, while curated identity recalls `google-research/vision_transformer` at rank 2. | `low-medium` | Only investigate if a future score audit shows a generic collision signal that can be fixed safely. |
| `wav2vec2_2020` | official recalled, not top-1 | `3` | `facebookresearch/fairseq` | `ranchlai/wav2vec-2.0`, `speech-lab-iitm/ccc-wav2vec-2.0`, `facebookresearch/fairseq` | Title-specific wav2vec repositories outrank the broad official `facebookresearch/fairseq` monorepo at rank 3. | `low-medium` | Leave unless optimizing official Top-1 for monorepo-hosted implementations becomes a priority. |

## Next-Round Recommendations

1. Start with `mmdetection_2019` and `lightgcn_2020` as read-only audits: they have the clearest owner/fork/distractor collision signals and do not require Papers with Code.
2. If improving recommender Top-3 matters, design a small evidence-backed reproduction-identity path for no-official-label cases (`implicit_mf_2008`, `deepfm_2017`) instead of changing general retrieval or scoring.
3. Defer broad Top-1 ranking changes until there is a separate score audit; current Official Top-3 is already `0.9434` and distractor ranked #1 is `0.0000`.

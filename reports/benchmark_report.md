# Paper Reproduction Benchmark Report

- Benchmark file: `benchmarks\paper_repro_benchmark.json`
- Top-k: `3`
- Total cases: `53`
- Attempted live cases: `53`
- Evaluated cases: `53`
- Unprocessed cases: `0`
- Failed cases: `0`
- Provider failed cases: `0`
- Rate limited cases: `0`

## Summary

- Top-1 hit rate: `0.6981`
- Top-3 hit rate: `0.9623`
- Official repo top-1 hit rate: `0.6792`
- Official repo top-3 hit rate: `0.9434`
- Distractor ranked #1 rate: `0.0`
- Stopped early: `False`
- Stop reason: `none`

## By Task

| Task | Cases | Top-1 | Top-3 | Distractor #1 |
|---|---:|---:|---:|---:|
| biology | 1 | 1.0 | 1.0 | 0.0 |
| computer_vision | 36 | 0.7222 | 1.0 | 0.0 |
| graph_learning | 1 | 1.0 | 1.0 | 0.0 |
| nlp | 6 | 1.0 | 1.0 | 0.0 |
| recommender | 3 | 0.0 | 0.3333 | 0.0 |
| robotics | 1 | 0.0 | 1.0 | 0.0 |
| speech | 5 | 0.6 | 1.0 | 0.0 |

## Failure Summary By Cause

- `expected_repo_not_recalled`: 2 cases; examples: `implicit_mf_2008`, `deepfm_2017`
- `official_recalled_not_top1`: 14 cases; examples: `nerf_2020`, `vit_2020`, `simclr_2020`, `guided_diffusion_2021`, `grounding_dino_2023`, `monodepth2_2019`, `orb_slam3_2020`, `colmap_2016`

## Failure Summary By Task

- `computer_vision`: 10 cases; examples: `nerf_2020`, `vit_2020`, `simclr_2020`, `guided_diffusion_2021`, `grounding_dino_2023`
- `recommender`: 3 cases; examples: `lightgcn_2020`, `implicit_mf_2008`, `deepfm_2017`
- `robotics`: 1 cases; examples: `orb_slam3_2020`
- `speech`: 2 cases; examples: `wav2vec2_2020`, `hubert_2021`

## Failure Examples

- `nerf_2020` NeRF: Representing Scenes as Neural Radiance Fields for View Synthesis: official_recalled_not_top1; retrieved: sxyu/pixel-nerf, bmild/nerf, ayaanzhaque/instruct-nerf2nerf
- `vit_2020` An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale: official_recalled_not_top1; retrieved: yunkun-zhang/cite, google-research/vision_transformer, purdue-m2/ai-face-fairnessbench
- `simclr_2020` A Simple Framework for Contrastive Learning of Visual Representations: official_recalled_not_top1; retrieved: andrewatanov/simclr-pytorch, google-research/simclr, sthalles/simclr
- `guided_diffusion_2021` Diffusion Models Beat GANs on Image Synthesis: official_recalled_not_top1; retrieved: mchong6/gansnroses, openai/guided-diffusion, tkarras/progressive_growing_of_gans
- `grounding_dino_2023` Grounding DINO: Marrying DINO with Grounded Pre-Training for Open-Set Object Detection: official_recalled_not_top1; retrieved: dongdong-d/groundingdino-finetuning, longzw1997/open-groundingdino, idea-research/groundingdino
- `monodepth2_2019` Digging Into Self-Supervised Monocular Depth Estimation: official_recalled_not_top1; retrieved: eddiespade/monodepth2, icaruswizard/monodepth2-paddle, nianticlabs/monodepth2
- `orb_slam3_2020` ORB-SLAM3: An Accurate Open-Source Library for Visual, Visual-Inertial and Multi-Map SLAM: official_recalled_not_top1; retrieved: leaner-forever/segs-slam, thien94/orb_slam3_ros, uz-slamlab/orb_slam3
- `colmap_2016` Structure-from-Motion Revisited: official_recalled_not_top1; retrieved: fangjinhuawang/patchmatchnet, colmap/colmap, xiaobaiiiiii/colmap-pcd
- `lightgcn_2020` LightGCN: Simplifying and Powering Graph Convolution Network for Recommendation: official_recalled_not_top1; retrieved: lucapantea/lightgcn, kuandeng/lightgcn, gusye1234/lightgcn-pytorch
- `llava_2023` Visual Instruction Tuning: official_recalled_not_top1; retrieved: microsoft/llava-med, tencentarc/smartedit, haotian-liu/llava
- `ultralytics_yolov8_2023` YOLOv8: official_recalled_not_top1; retrieved: dataxujing/yolov8, ultralytics/ultralytics, derronqi/yolov8-face
- `mmdetection_2019` MMDetection: Open MMLab Detection Toolbox and Benchmark: official_recalled_not_top1; retrieved: allenai/mmdetection, open-mmlab/mmdetection, hhaandroid/mmdetection-mini

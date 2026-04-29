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
- Top-3 hit rate: `0.9057`
- Official repo top-1 hit rate: `0.6415`
- Official repo top-3 hit rate: `0.8491`
- Distractor ranked #1 rate: `0.0`
- Stopped early: `False`
- Stop reason: `none`

## By Task

| Task | Cases | Top-1 | Top-3 | Distractor #1 |
|---|---:|---:|---:|---:|
| biology | 1 | 0.0 | 0.0 | 0.0 |
| computer_vision | 36 | 0.7222 | 0.8889 | 0.0 |
| graph_learning | 1 | 1.0 | 1.0 | 0.0 |
| nlp | 6 | 0.8333 | 1.0 | 0.0 |
| recommender | 3 | 0.6667 | 1.0 | 0.0 |
| robotics | 1 | 0.0 | 1.0 | 0.0 |
| speech | 5 | 0.6 | 1.0 | 0.0 |

## Failure Summary By Cause

- `official_recalled_not_top1`: 11 cases; examples: `bert_2018`, `ddpm_2020`, `guided_diffusion_2021`, `grounding_dino_2023`, `orb_slam3_2020`, `colmap_2016`, `lightgcn_2020`, `llava_2023`
- `official_repo_not_recalled`: 5 cases; examples: `nerf_2020`, `simclr_2020`, `alphafold_2021`, `raft_2020`, `monodepth2_2019`

## Failure Summary By Task

- `biology`: 1 cases; examples: `alphafold_2021`
- `computer_vision`: 10 cases; examples: `nerf_2020`, `simclr_2020`, `ddpm_2020`, `guided_diffusion_2021`, `grounding_dino_2023`
- `nlp`: 1 cases; examples: `bert_2018`
- `recommender`: 1 cases; examples: `lightgcn_2020`
- `robotics`: 1 cases; examples: `orb_slam3_2020`
- `speech`: 2 cases; examples: `wav2vec2_2020`, `hubert_2021`

## Failure Examples

- `nerf_2020` NeRF: Representing Scenes as Neural Radiance Fields for View Synthesis: official_repo_not_recalled; retrieved: quan-meng/gnerf, nvlabs/nvdiffrec, jia-lab-research/efficientnerf
- `simclr_2020` A Simple Framework for Contrastive Learning of Visual Representations: official_repo_not_recalled; retrieved: spijkervet/simclr, leftthomas/simclr, sayakpaul/simclr-in-tensorflow-2
- `alphafold_2021` Highly accurate protein structure prediction with AlphaFold: official_repo_not_recalled; retrieved: model3dbio/alphafold3-conda-install, lucidrains/itransformer, hanziwww/alphafold3-gui
- `bert_2018` BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding: official_recalled_not_top1; retrieved: ymcui/chinese-bert-wwm, google-research/bert, bojone/bert4keras
- `ddpm_2020` Denoising Diffusion Probabilistic Models: official_recalled_not_top1; retrieved: sak-h/pytorch-denoising-diffusion-probabilistic-models, hojonathanho/diffusion, musawir124/denoising-diffusion-probabilistic-models
- `guided_diffusion_2021` Diffusion Models Beat GANs on Image Synthesis: official_recalled_not_top1; retrieved: mchong6/gansnroses, tkarras/progressive_growing_of_gans, openai/guided-diffusion
- `grounding_dino_2023` Grounding DINO: Marrying DINO with Grounded Pre-Training for Open-Set Object Detection: official_recalled_not_top1; retrieved: dongdong-d/groundingdino-finetuning, idea-research/groundingdino, longzw1997/open-groundingdino
- `raft_2020` RAFT: Recurrent All-Pairs Field Transforms for Optical Flow: official_repo_not_recalled; retrieved: mcg-nku/amt, yafeng19/hap-vr, depixels/tinyalign
- `monodepth2_2019` Digging Into Self-Supervised Monocular Depth Estimation: official_repo_not_recalled; retrieved: icaruswizard/monodepth2-paddle, xxxvincent/monodepth2, fangget/tf-monodepth2
- `orb_slam3_2020` ORB-SLAM3: An Accurate Open-Source Library for Visual, Visual-Inertial and Multi-Map SLAM: official_recalled_not_top1; retrieved: leaner-forever/segs-slam, thien94/orb_slam3_ros, uz-slamlab/orb_slam3
- `colmap_2016` Structure-from-Motion Revisited: official_recalled_not_top1; retrieved: fangjinhuawang/patchmatchnet, colmap/colmap, xiaobaiiiiii/colmap-pcd
- `lightgcn_2020` LightGCN: Simplifying and Powering Graph Convolution Network for Recommendation: official_recalled_not_top1; retrieved: lucapantea/lightgcn, kuandeng/lightgcn, gusye1234/lightgcn-pytorch

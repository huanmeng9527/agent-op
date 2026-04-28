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

- Top-1 hit rate: `0.5472`
- Top-3 hit rate: `0.6792`
- Official repo top-1 hit rate: `0.5283`
- Official repo top-3 hit rate: `0.6604`
- Distractor ranked #1 rate: `0.0`
- Stopped early: `False`
- Stop reason: `none`

## By Task

| Task | Cases | Top-1 | Top-3 | Distractor #1 |
|---|---:|---:|---:|---:|
| biology | 1 | 1.0 | 1.0 | 0.0 |
| computer_vision | 36 | 0.5556 | 0.7222 | 0.0 |
| graph_learning | 1 | 1.0 | 1.0 | 0.0 |
| nlp | 6 | 0.8333 | 0.8333 | 0.0 |
| recommender | 3 | 0.0 | 0.0 | 0.0 |
| robotics | 1 | 0.0 | 1.0 | 0.0 |
| speech | 5 | 0.4 | 0.4 | 0.0 |

## Failure Summary By Cause

- `expected_repo_not_recalled`: 2 cases; examples: `implicit_mf_2008`, `deepfm_2017`
- `official_recalled_not_top1`: 7 cases; examples: `moco_2020`, `nerf_2020`, `simclr_2020`, `grounding_dino_2023`, `monodepth2_2019`, `orb_slam3_2020`, `mmdetection_2019`
- `official_repo_not_recalled`: 15 cases; examples: `instant_ngp_2022`, `vit_2020`, `t5_2019`, `stable_diffusion_2022`, `ddpm_2020`, `guided_diffusion_2021`, `midas_2020`, `colmap_2016`

## Failure Summary By Task

- `computer_vision`: 16 cases; examples: `moco_2020`, `nerf_2020`, `instant_ngp_2022`, `vit_2020`, `simclr_2020`
- `nlp`: 1 cases; examples: `t5_2019`
- `recommender`: 3 cases; examples: `lightgcn_2020`, `implicit_mf_2008`, `deepfm_2017`
- `robotics`: 1 cases; examples: `orb_slam3_2020`
- `speech`: 3 cases; examples: `deepspeech2_2015`, `wav2vec2_2020`, `hubert_2021`

## Failure Examples

- `moco_2020` Momentum Contrast for Unsupervised Visual Representation Learning: official_recalled_not_top1; retrieved: bl0/moco, leftthomas/moco, facebookresearch/moco
- `nerf_2020` NeRF: Representing Scenes as Neural Radiance Fields for View Synthesis: official_recalled_not_top1; retrieved: sxyu/pixel-nerf, bmild/nerf, ayaanzhaque/instruct-nerf2nerf
- `instant_ngp_2022` Instant Neural Graphics Primitives with a Multiresolution Hash Encoding: official_repo_not_recalled; retrieved: nvlabs/tiny-cuda-nn, niklasschmitz/sdf_jax, ailon-island/tiny-cuda-nn-old
- `vit_2020` An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale: official_repo_not_recalled; retrieved: yunkun-zhang/cite, purdue-m2/ai-face-fairnessbench, brianpulfer/papersreimplementations
- `simclr_2020` A Simple Framework for Contrastive Learning of Visual Representations: official_recalled_not_top1; retrieved: andrewatanov/simclr-pytorch, google-research/simclr, sthalles/simclr
- `t5_2019` Exploring the Limits of Transfer Learning with a Unified Text-to-Text Transformer: official_repo_not_recalled; retrieved: thu-ml/motus, yurakuratov/t5-experiments, google-research/t5x
- `stable_diffusion_2022` High-Resolution Image Synthesis with Latent Diffusion Models: official_repo_not_recalled; retrieved: abdur75648/utrnet-high-resolution-urdu-text-recognition, leoxiaobin/deep-high-resolution-net.pytorch, wangyx240/high-resolution-image-inpainting-gan
- `ddpm_2020` Denoising Diffusion Probabilistic Models: official_repo_not_recalled; retrieved: sak-h/pytorch-denoising-diffusion-probabilistic-models, musawir124/denoising-diffusion-probabilistic-models, nicob15/trajectory-generation-control-and-safety-with-denoising-diffusion-probabilistic-models
- `guided_diffusion_2021` Diffusion Models Beat GANs on Image Synthesis: official_repo_not_recalled; retrieved: mchong6/gansnroses, tkarras/progressive_growing_of_gans, xingangpan/draggan
- `grounding_dino_2023` Grounding DINO: Marrying DINO with Grounded Pre-Training for Open-Set Object Detection: official_recalled_not_top1; retrieved: dongdong-d/groundingdino-finetuning, longzw1997/open-groundingdino, idea-research/groundingdino
- `monodepth2_2019` Digging Into Self-Supervised Monocular Depth Estimation: official_recalled_not_top1; retrieved: eddiespade/monodepth2, icaruswizard/monodepth2-paddle, nianticlabs/monodepth2
- `midas_2020` Towards Robust Monocular Depth Estimation: Mixing Datasets for Zero-shot Cross-dataset Transfer: official_repo_not_recalled; retrieved: kopperx/adv-diffusion, mq-zhang1/hoidiffusion, pollardlab/midas

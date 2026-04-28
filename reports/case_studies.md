# Paper Reproduction Case Studies

Live workflow was skipped: GITHUB_TOKEN is not configured. Use --allow-unauthenticated for a small risky smoke run, or set GITHUB_TOKEN in .env.

## Segment Anything

- Case ID: `sam_2023`
- Query: `Segment Anything paper code pytorch CVPR 2023`
- Task: `computer_vision`
- Labeled official repos: `facebookresearch/segment-anything`
- Labeled high-quality reproductions: None
- Labeled distractors: `IDEA-Research/Grounded-Segment-Anything`, `luca-medeiros/lang-segment-anything`, `Hedlen/awesome-segment-anything`
- Top candidates: unavailable until live search runs.
- Deep inspection: unavailable until live inspect runs.
- Compare recommendation: unavailable until live compare runs.

## End-to-End Object Detection with Transformers

- Case ID: `detr_2020`
- Query: `DETR End-to-End Object Detection with Transformers paper code pytorch ECCV 2020`
- Task: `computer_vision`
- Labeled official repos: `facebookresearch/detr`
- Labeled high-quality reproductions: `fundamentalvision/Deformable-DETR`
- Labeled distractors: `IDEA-Research/detrex`
- Top candidates: unavailable until live search runs.
- Deep inspection: unavailable until live inspect runs.
- Compare recommendation: unavailable until live compare runs.

## NeRF: Representing Scenes as Neural Radiance Fields for View Synthesis

- Case ID: `nerf_2020`
- Query: `NeRF Representing Scenes as Neural Radiance Fields paper code`
- Task: `computer_vision`
- Labeled official repos: `bmild/nerf`
- Labeled high-quality reproductions: `yenchenlin/nerf-pytorch`
- Labeled distractors: `NVlabs/instant-ngp`
- Top candidates: unavailable until live search runs.
- Deep inspection: unavailable until live inspect runs.
- Compare recommendation: unavailable until live compare runs.

## DreamBooth: Fine Tuning Text-to-Image Diffusion Models for Subject-Driven Generation

- Case ID: `dreambooth_2022`
- Query: `DreamBooth Fine Tuning Text-to-Image Diffusion Models Subject-Driven Generation code`
- Task: `computer_vision`
- Labeled official repos: None
- Labeled high-quality reproductions: `XavierXiao/Dreambooth-Stable-Diffusion`
- Labeled distractors: `huggingface/diffusers`
- Top candidates: unavailable until live search runs.
- Deep inspection: unavailable until live inspect runs.
- Compare recommendation: unavailable until live compare runs.

## Highly accurate protein structure prediction with AlphaFold

- Case ID: `alphafold_2021`
- Query: `AlphaFold Highly accurate protein structure prediction paper code`
- Task: `biology`
- Labeled official repos: `google-deepmind/alphafold`
- Labeled high-quality reproductions: `aqlaboratory/openfold`
- Labeled distractors: `google-deepmind/alphafold3`
- Top candidates: unavailable until live search runs.
- Deep inspection: unavailable until live inspect runs.
- Compare recommendation: unavailable until live compare runs.

Run with a GitHub token:

```powershell
.\.venv\Scripts\python.exe scripts\generate_case_studies.py
```

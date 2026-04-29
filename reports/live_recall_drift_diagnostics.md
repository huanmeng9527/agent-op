# Live Recall Drift Diagnostics

This targeted diagnostic report replays only the five current `official_repo_not_recalled` / `expected_repo_not_recalled` cases. It does not modify scorer, retrieval, provider, identity, or benchmark logic.

## Scope

- Target cases: `nerf_2020`, `simclr_2020`, `alphafold_2021`, `raft_2020`, `monodepth2_2019`
- Source full benchmark: Top-1 `0.6981`, Top-3 `0.9057`, Official Top-3 `0.8491`
- Provider failed / rate limited in source report: `0` / `0`

## Classification Summary

- `live_search_drift`: `5`

## Case Summary

| Case | Expected official | Full top-3 | Direct fetch | Raw query hit | Provider pool | Scored rank | Current service top-3 | Classification |
|---|---|---|---|---|---|---|---|---|
| `nerf_2020` | `bmild/nerf` | `quan-meng/gnerf`, `nvlabs/nvdiffrec`, `jia-lab-research/efficientnerf` | yes | yes | yes | `{'bmild/nerf': 2}` | `sxyu/pixel-nerf`, `bmild/nerf`, `ayaanzhaque/instruct-nerf2nerf` | `live_search_drift` |
| `simclr_2020` | `google-research/simclr` | `spijkervet/simclr`, `leftthomas/simclr`, `sayakpaul/simclr-in-tensorflow-2` | yes | no | yes | `{'google-research/simclr': 2}` | `andrewatanov/simclr-pytorch`, `google-research/simclr`, `sthalles/simclr` | `live_search_drift` |
| `alphafold_2021` | `google-deepmind/alphafold` | `model3dbio/alphafold3-conda-install`, `lucidrains/itransformer`, `hanziwww/alphafold3-gui` | yes | yes | yes | `{'google-deepmind/alphafold': 1}` | `google-deepmind/alphafold`, `lucidrains/alphafold3-pytorch`, `urinx/alphafold_pytorch` | `live_search_drift` |
| `raft_2020` | `princeton-vl/raft` | `mcg-nku/amt`, `yafeng19/hap-vr`, `depixels/tinyalign` | yes | yes | yes | `{'princeton-vl/raft': 1}` | `princeton-vl/raft`, `dangeng/flowmag`, `david-zhao-1997/high-frequency-stereo-matching-network` | `live_search_drift` |
| `monodepth2_2019` | `nianticlabs/monodepth2` | `icaruswizard/monodepth2-paddle`, `xxxvincent/monodepth2`, `fangget/tf-monodepth2` | yes | yes | yes | `{'nianticlabs/monodepth2': 3}` | `eddiespade/monodepth2`, `icaruswizard/monodepth2-paddle`, `nianticlabs/monodepth2` | `live_search_drift` |

## Case Details

### `nerf_2020`

- Paper title: NeRF: Representing Scenes as Neural Radiance Fields for View Synthesis
- Expected official repo: `bmild/nerf`
- Full benchmark top-3: `quan-meng/gnerf`, `nvlabs/nvdiffrec`, `jia-lab-research/efficientnerf`
- Search queries: `nerf in:name archived:false`, `nerf "official code" in:name,description,readme archived:false`, `ne_rf in:name archived:false`, `ne_rf "official code" in:name,description,readme archived:false`, `ne-rf in:name archived:false`, `ne-rf "official code" in:name,description,readme archived:false`, `"NeRF: Representing Scenes as Neural Radiance Fields for View Synthesis" in:name archived:false`, `nerf:-representing-scenes-as-neural-radiance-fields-for-view-synthesis in:name archived:false`, `nerf:_representing_scenes_as_neural_radiance_fields_for_view_synthesis in:name archived:false`, `nerf:representingscenesasneuralradiancefieldsforviewsynthesis in:name archived:false`, `"NeRF: Representing Scenes as Neural Radiance Fields for View Synthesis" "paper code" in:name,description,readme archived:false`, `"NeRF: Representing Scenes as Neural Radiance Fields for View Synthesis" "official implementation" in:name,description,readme archived:false`
- Generated aliases: `nerf`, `ne_rf`, `ne-rf`
- Identity matches: none
- Official appears in raw GitHub query results: `yes` (q1 rank 1)
- Official in provider-considered pool: `yes`; sources: `{'bmild/nerf': 'search_query_1'}`
- Official scored ranks in replayed provider pool: `{'bmild/nerf': 2}`
- Direct official fetch score: `0.7340` raw=`0.7340` role=`official_implementation` cap=`incomplete_execution_cap`
- Current targeted service top-3: `sxyu/pixel-nerf`, `bmild/nerf`, `ayaanzhaque/instruct-nerf2nerf`
- Classification: `live_search_drift`; labels: `live_search_drift`
- Next minimal step: Rerun targeted validation and compare raw query positions; this may not need a logic change.

Provider-considered raw candidates:

| Rank | Source | Repo | Stars | Archived | Description |
|---:|---|---|---:|---|---|
| 1 | `search_query_1` | `bmild/nerf` | 10864 | no | Code release for NeRF (Neural Radiance Fields) |
| 2 | `search_query_1` | `nerfstudio-project/nerfstudio` | 11503 | no | A collaboration friendly studio for NeRFs |
| 3 | `search_query_1` | `awesome-nerf/awesome-nerf` | 6771 | no | A curated list of awesome neural radiance fields papers |
| 4 | `search_query_1` | `yenchenlin/nerf-pytorch` | 6025 | no | A PyTorch implementation of NeRF (Neural Radiance Fields) that reproduces the results. |
| 5 | `search_query_1` | `nerfies/nerfies.github.io` | 4136 | no |  |
| 6 | `search_query_1` | `kwea123/nerf_pl` | 2805 | no | NeRF (Neural Radiance Fields) and NeRF in the Wild using pytorch-lightning |
| 7 | `search_query_1` | `ayaanzhaque/instruct-nerf2nerf` | 850 | no | Instruct-NeRF2NeRF: Editing 3D Scenes with Instructions (ICCV 2023) |
| 8 | `search_query_1` | `ashawkey/nerf2mesh` | 960 | no | [ICCV2023] Delicate Textured Mesh Recovery from NeRF via Adaptive Surface Refinement |
| 9 | `search_query_1` | `sxyu/pixel-nerf` | 1465 | no | PixelNeRF Official Repository |
| 10 | `search_query_1` | `nerfstudio-project/nerfacc` | 1458 | no | A General NeRF Acceleration Toolbox in PyTorch. |
| 11 | `search_query_2` | `yerfor/geneface` | 2664 | no | GeneFace: Generalized and High-Fidelity 3D Talking Face Synthesis; ICLR 2023; Official code |
| 12 | `search_query_2` | `yerfor/genefaceplusplus` | 1812 | no | GeneFace++: Generalized and Stable Real-Time 3D Talking Face Generation; Official Code |

Replayed scored provider-pool top-10:

| Rank | Repo | Score | Raw | Role | Cap | Stars | Archived | Signals |
|---:|---|---:|---:|---|---|---:|---|---|
| 1 | `sxyu/pixel-nerf` | `0.7762` | `0.7762` | `official_implementation` | `none` | 1465 | no | has training code; has eval code; has config |
| 2 | `bmild/nerf` | `0.7340` | `0.7340` | `official_implementation` | `incomplete_execution_cap` | 10864 | no | repository text mentions the requested paper title; has config; has requirements |
| 3 | `ayaanzhaque/instruct-nerf2nerf` | `0.6526` | `0.6526` | `official_implementation` | `incomplete_execution_cap` | 850 | no | repository text matches task: computer_vision; has requirements; has dataset doc |
| 4 | `yerfor/geneface` | `0.6146` | `0.6146` | `official_implementation` | `incomplete_execution_cap` | 2664 | no | has requirements; has dataset doc; has checkpoint hint |
| 5 | `yerfor/genefaceplusplus` | `0.5745` | `0.5745` | `official_implementation` | `incomplete_execution_cap` | 1812 | no | has dataset doc; has checkpoint hint; detects tech stack: pytorch, python, docker |
| 6 | `ashawkey/nerf2mesh` | `0.5736` | `0.5736` | `official_implementation` | `incomplete_execution_cap` | 960 | no | has requirements; has dataset doc; detects tech stack: pytorch, huggingface, cuda, python, r |
| 7 | `yenchenlin/nerf-pytorch` | `0.5535` | `0.5535` | `unknown` | `incomplete_execution_cap` | 6025 | no | has config; has requirements; has dataset doc |
| 8 | `nerfstudio-project/nerfstudio` | `0.5351` | `0.5351` | `demo_only` | `demo_only_cap` | 11503 | no | repository text matches task: computer_vision; has config; has requirements |
| 9 | `yashbhalgat/hashnerf-pytorch` | `0.5195` | `0.5195` | `official_implementation` | `weak_assets_cap` | 1035 | no | repository text matches task: computer_vision; detects tech stack: pytorch, python; classified as official_implementation |
| 10 | `nvlabs/nvdiffrec` | `0.4776` | `0.4776` | `official_implementation` | `weak_assets_cap` | 2282 | no | detects tech stack: pytorch, python; classified as official_implementation |

### `simclr_2020`

- Paper title: A Simple Framework for Contrastive Learning of Visual Representations
- Expected official repo: `google-research/simclr`
- Full benchmark top-3: `spijkervet/simclr`, `leftthomas/simclr`, `sayakpaul/simclr-in-tensorflow-2`
- Search queries: `simclr in:name archived:false`, `simclr "official code" in:name,description,readme archived:false`, `sim_clr in:name archived:false`, `sim_clr "official code" in:name,description,readme archived:false`, `sim-clr in:name archived:false`, `sim-clr "official code" in:name,description,readme archived:false`, `"A Simple Framework for Contrastive Learning of Visual Representations" in:name archived:false`, `a-simple-framework-for-contrastive-learning-of-visual-representations in:name archived:false`, `a_simple_framework_for_contrastive_learning_of_visual_representations in:name archived:false`, `asimpleframeworkforcontrastivelearningofvisualrepresentations in:name archived:false`, `"A Simple Framework for Contrastive Learning of Visual Representations" "paper code" in:name,description,readme archived:false`, `"A Simple Framework for Contrastive Learning of Visual Representations" "official implementation" in:name,description,readme archived:false`
- Generated aliases: `simclr`, `sim_clr`, `sim-clr`
- Identity matches: none
- Official appears in raw GitHub query results: `no` (none)
- Official in provider-considered pool: `yes`; sources: `{'google-research/simclr': 'canonical_direct_fetch'}`
- Official scored ranks in replayed provider pool: `{'google-research/simclr': 2}`
- Direct official fetch score: `0.7657` raw=`0.7657` role=`official_implementation` cap=`archived_cap`
- Current targeted service top-3: `andrewatanov/simclr-pytorch`, `google-research/simclr`, `sthalles/simclr`
- Classification: `live_search_drift`; labels: `live_search_drift`
- Next minimal step: Rerun targeted validation and compare raw query positions; this may not need a logic change.

Provider-considered raw candidates:

| Rank | Source | Repo | Stars | Archived | Description |
|---:|---|---|---:|---|---|
| 1 | `canonical_direct_fetch` | `google-research/simclr` | 4486 | yes | SimCLRv2 - Big Self-Supervised Models are Strong Semi-Supervised Learners |
| 2 | `search_query_1` | `sthalles/simclr` | 2492 | no | PyTorch implementation of SimCLR: A Simple Framework for Contrastive Learning of Visual Representations |
| 3 | `search_query_1` | `spijkervet/simclr` | 818 | no | PyTorch implementation of SimCLR: A Simple Framework for Contrastive Learning of Visual Representations by T. Chen et al. |
| 4 | `search_query_1` | `leftthomas/simclr` | 573 | no | A PyTorch implementation of SimCLR based on ICML 2020 paper "A Simple Framework for Contrastive Learning of Visual Representations" |
| 5 | `search_query_1` | `mdiephuis/simclr` | 82 | no | Pytorch implementation of "A Simple Framework for Contrastive Learning of Visual Representations" |
| 6 | `search_query_1` | `the-ai-summer/simclr` | 31 | no | An education step by step implementation of SimCLR that accompanies the blogpost |
| 7 | `search_query_1` | `thunderinfy/simclr` | 22 | no | This repo contains code for SimCLR : A Simple Framework for Contrastive Learning of Visual Representations |
| 8 | `search_query_1` | `andrewatanov/simclr-pytorch` | 211 | no | PyTorch implementation of SimCLR: supports multi-GPU training and closely reproduces results |
| 9 | `search_query_1` | `pietz/simclr` | 18 | no | Unofficial PyTorch implementation of SimCLR by Chen et al. |
| 10 | `search_query_1` | `mwdhont/simclrv1-keras-tensorflow` | 110 | no | Tensorflow-Keras implementation of SimCLR: Simple Framework for Contrastive Learning of Visual Representations by Chen et al. (2020) |
| 11 | `search_query_1` | `dmolony3/simclr` | 8 | no | Tensorflow implementation of SimCLR |
| 12 | `search_query_2` | `linusericsson/ssl-transfer` | 186 | no | Official code for the CVPR 2021 paper "How Well Do Self-Supervised Models Transfer?" |

Replayed scored provider-pool top-10:

| Rank | Repo | Score | Raw | Role | Cap | Stars | Archived | Signals |
|---:|---|---:|---:|---|---|---:|---|---|
| 1 | `andrewatanov/simclr-pytorch` | `0.8282` | `0.8282` | `reproduction` | `none` | 211 | no | repository text mentions the requested paper title; has training code; has config |
| 2 | `google-research/simclr` | `0.7657` | `0.7657` | `official_implementation` | `archived_cap` | 4486 | yes | canonical research-org repository exactly matches a short paper alias; repository text mentions the requested paper title; repository text matches task: computer_vision |
| 3 | `sthalles/simclr` | `0.7549` | `0.7549` | `official_implementation` | `incomplete_execution_cap` | 2492 | no | repository text mentions the requested paper title; has config; has requirements |
| 4 | `spijkervet/simclr` | `0.7228` | `0.7228` | `model_zoo` | `model_zoo_cap` | 818 | no | repository text mentions the requested paper title; has config; has requirements |
| 5 | `leftthomas/simclr` | `0.6880` | `0.6880` | `official_implementation` | `incomplete_execution_cap` | 573 | no | repository text mentions the requested paper title; has dataset doc; has results |
| 6 | `mwdhont/simclrv1-keras-tensorflow` | `0.5951` | `0.5951` | `official_implementation` | `incomplete_execution_cap` | 110 | no | has requirements; has dataset doc; has results |
| 7 | `linusericsson/ssl-transfer` | `0.5498` | `0.5498` | `official_implementation` | `incomplete_execution_cap` | 186 | no | has dataset doc; has checkpoint hint; detects tech stack: pytorch, tensorflow, jax, python |
| 8 | `mdiephuis/simclr` | `0.5496` | `0.5496` | `unknown` | `incomplete_execution_cap` | 82 | no | repository text mentions the requested paper title; has requirements; has dataset doc |
| 9 | `thunderinfy/simclr` | `0.5470` | `0.5470` | `unknown` | `incomplete_execution_cap` | 22 | no | repository text mentions the requested paper title; has config; has results |
| 10 | `pietz/simclr` | `0.5433` | `0.5433` | `reproduction` | `incomplete_execution_cap` | 18 | no | repository text mentions the requested paper title; has results; has notebook |

### `alphafold_2021`

- Paper title: Highly accurate protein structure prediction with AlphaFold
- Expected official repo: `google-deepmind/alphafold`
- Full benchmark top-3: `model3dbio/alphafold3-conda-install`, `lucidrains/itransformer`, `hanziwww/alphafold3-gui`
- Search queries: `alphafold in:name archived:false`, `alphafold "official code" in:name,description,readme archived:false`, `alpha_fold in:name archived:false`, `alpha_fold "official code" in:name,description,readme archived:false`, `alpha-fold in:name archived:false`, `alpha-fold "official code" in:name,description,readme archived:false`, `"Highly accurate protein structure prediction with AlphaFold" in:name archived:false`, `highly-accurate-protein-structure-prediction-with-alphafold in:name archived:false`, `highly_accurate_protein_structure_prediction_with_alphafold in:name archived:false`, `highlyaccurateproteinstructurepredictionwithalphafold in:name archived:false`, `"Highly accurate protein structure prediction with AlphaFold" "paper code" in:name,description,readme archived:false`, `"Highly accurate protein structure prediction with AlphaFold" "official implementation" in:name,description,readme archived:false`
- Generated aliases: `alphafold`, `alpha_fold`, `alpha-fold`
- Identity matches: none
- Official appears in raw GitHub query results: `yes` (q1 rank 1)
- Official in provider-considered pool: `yes`; sources: `{'google-deepmind/alphafold': 'canonical_direct_fetch'}`
- Official scored ranks in replayed provider pool: `{'google-deepmind/alphafold': 1}`
- Direct official fetch score: `0.7500` raw=`0.6647` role=`official_implementation` cap=`incomplete_execution_cap`
- Current targeted service top-3: `google-deepmind/alphafold`, `lucidrains/alphafold3-pytorch`, `urinx/alphafold_pytorch`
- Classification: `live_search_drift`; labels: `live_search_drift`
- Next minimal step: Rerun targeted validation and compare raw query positions; this may not need a logic change.

Provider-considered raw candidates:

| Rank | Source | Repo | Stars | Archived | Description |
|---:|---|---|---:|---|---|
| 1 | `canonical_direct_fetch` | `google-deepmind/alphafold` | 14540 | no | Open source code for AlphaFold 2. |
| 2 | `search_query_1` | `google-deepmind/alphafold3` | 7920 | no | AlphaFold 3 inference pipeline. |
| 3 | `search_query_1` | `kuixu/alphafold` | 103 | no | Install alphafold on the local machine, get out of docker. |
| 4 | `search_query_1` | `lucidrains/alphafold2` | 1632 | no | To eventually become an unofficial Pytorch implementation / replication of Alphafold2, as details of the architecture get released |
| 5 | `search_query_1` | `lucidrains/alphafold3-pytorch` | 1653 | no | Implementation of Alphafold 3 from Google Deepmind in Pytorch |
| 6 | `search_query_1` | `ligo-biosciences/alphafold3` | 1070 | no | Open source implementation of AlphaFold3 |
| 7 | `search_query_1` | `kalininalab/alphafold_non_docker` | 378 | no | AlphaFold2 non-docker setup |
| 8 | `search_query_1` | `urinx/alphafold_pytorch` | 402 | no | An implementation of the DeepMind's AlphaFold based on PyTorch for research |
| 9 | `search_query_1` | `phbradley/alphafold_finetune` | 173 | no | Python code for fine-tuning AlphaFold to perform protein-peptide binding predictions |
| 10 | `search_query_1` | `kilianmandon/alphafold-decoded` | 114 | no | Hands-on AlphaFold implementation for educational purposes. |
| 11 | `search_query_2` | `lucidrains/invariant-point-attention` | 171 | no | Implementation of Invariant Point Attention, used for coordinate refinement in the structure module of Alphafold2, as a standalone Pytorch module |
| 12 | `search_query_2` | `jozhang97/ambient-proteins` | 33 | no | Official code release for Ambient Protein Diffusion |

Replayed scored provider-pool top-10:

| Rank | Repo | Score | Raw | Role | Cap | Stars | Archived | Signals |
|---:|---|---:|---:|---|---|---:|---|---|
| 1 | `google-deepmind/alphafold` | `0.7500` | `0.6647` | `official_implementation` | `incomplete_execution_cap` | 14540 | no | canonical research-org repository exactly matches a short paper alias; has requirements; has notebook |
| 2 | `lucidrains/alphafold3-pytorch` | `0.6245` | `0.6245` | `official_implementation` | `incomplete_execution_cap` | 1653 | no | has config; has requirements; has dataset doc |
| 3 | `google-deepmind/alphafold3` | `0.5905` | `0.5905` | `official_implementation` | `weak_assets_cap` | 7920 | no | canonical research-org repository nearly matches a short paper alias; has requirements; detects tech stack: python, r, docker |
| 4 | `urinx/alphafold_pytorch` | `0.5521` | `0.5521` | `official_implementation` | `incomplete_execution_cap` | 402 | no | has checkpoint hint; has results; detects tech stack: pytorch, tensorflow, python, r |
| 5 | `ligo-biosciences/alphafold3` | `0.5504` | `0.5504` | `official_implementation` | `incomplete_execution_cap` | 1070 | no | has config; has requirements; has notebook |
| 6 | `kuixu/alphafold` | `0.5434` | `0.5434` | `official_implementation` | `incomplete_execution_cap` | 103 | no | has requirements; has results; detects tech stack: jax, cuda, python, r, docker |
| 7 | `jozhang97/ambient-proteins` | `0.5373` | `0.5373` | `official_implementation` | `incomplete_execution_cap` | 33 | no | has requirements; has dataset doc; detects tech stack: pytorch, huggingface, lightning, python |
| 8 | `kalininalab/alphafold_non_docker` | `0.5275` | `0.5275` | `official_implementation` | `weak_assets_cap` | 378 | no | has requirements; detects tech stack: tensorflow, jax, cuda, python, docker; classified as official_implementation |
| 9 | `model3dbio/alphafold3-conda-install` | `0.5192` | `0.5192` | `official_implementation` | `weak_assets_cap` | 46 | no | repository text matches task: biology; detects tech stack: cuda, python, conda; classified as official_implementation |
| 10 | `lucidrains/invariant-point-attention` | `0.4856` | `0.4856` | `official_implementation` | `weak_assets_cap` | 171 | no | has requirements; detects tech stack: pytorch, python; classified as official_implementation |

### `raft_2020`

- Paper title: RAFT: Recurrent All-Pairs Field Transforms for Optical Flow
- Expected official repo: `princeton-vl/raft`
- Full benchmark top-3: `mcg-nku/amt`, `yafeng19/hap-vr`, `depixels/tinyalign`
- Search queries: `raft in:name archived:false`, `raft "official code" in:name,description,readme archived:false`, `all-pairs in:name archived:false`, `all-pairs "official code" in:name,description,readme archived:false`, `all_pairs in:name archived:false`, `all_pairs "official code" in:name,description,readme archived:false`, `allpairs in:name archived:false`, `allpairs "official code" in:name,description,readme archived:false`, `"RAFT: Recurrent All-Pairs Field Transforms for Optical Flow" in:name archived:false`, `raft:-recurrent-all-pairs-field-transforms-for-optical-flow in:name archived:false`, `raft:_recurrent_all-pairs_field_transforms_for_optical_flow in:name archived:false`, `raft:recurrentall-pairsfieldtransformsforopticalflow in:name archived:false`
- Generated aliases: `raft`, `all-pairs`, `all_pairs`, `allpairs`
- Identity matches: none
- Official appears in raw GitHub query results: `yes` (q1 rank 2)
- Official in provider-considered pool: `yes`; sources: `{'princeton-vl/raft': 'search_query_1'}`
- Official scored ranks in replayed provider pool: `{'princeton-vl/raft': 1}`
- Direct official fetch score: `0.8171` raw=`0.8171` role=`official_implementation` cap=`none`
- Current targeted service top-3: `princeton-vl/raft`, `dangeng/flowmag`, `david-zhao-1997/high-frequency-stereo-matching-network`
- Classification: `live_search_drift`; labels: `live_search_drift`
- Next minimal step: Rerun targeted validation and compare raw query positions; this may not need a logic change.

Provider-considered raw candidates:

| Rank | Source | Repo | Stars | Archived | Description |
|---:|---|---|---:|---|---|
| 1 | `search_query_1` | `hashicorp/raft` | 9002 | no | Golang implementation of the Raft consensus protocol |
| 2 | `search_query_1` | `princeton-vl/raft` | 4025 | no |  |
| 3 | `search_query_1` | `willemt/raft` | 1164 | no | C implementation of the Raft Consensus protocol, BSD licensed |
| 4 | `search_query_1` | `etcd-io/raft` | 1020 | no | Raft library for maintaining a replicated state machine |
| 5 | `search_query_1` | `eliben/raft` | 1368 | no | :rowboat: Raft implementation in Go |
| 6 | `search_query_1` | `rapidsai/raft` | 1002 | no | RAFT contains fundamental widely-used algorithms and primitives for machine learning and information retrieval. The algorithms are CUDA-accelerated and form building blocks for more easily writing high performance appli... |
| 7 | `search_query_1` | `hangsz/raft` | 147 | no | 非拜占庭节点的分布式共识算法Raft的python实现，欢迎fork和star。 |
| 8 | `search_query_1` | `elixir-toniq/raft` | 431 | no | An Elixir implementation of the raft consensus protocol |
| 9 | `search_query_1` | `tiglabs/raft` | 158 | no | an implementation of raft in Go |
| 10 | `search_query_1` | `lumpenspace/raft` | 174 | no | RAFT, or Retrieval-Augmented Fine-Tuning, is a method comprising of a fine-tuning and a RAG-based retrieval phase. It is particularly suited for the creation of agents that realistically emulate a specific human target. |
| 11 | `search_query_2` | `david-zhao-1997/high-frequency-stereo-matching-network` | 123 | no | [CVPR 2023 Highlight] The Official Code for High-Frequency Stereo Matching Network |
| 12 | `search_query_2` | `dangeng/flowmag` | 42 | no | Official code for NeurIPS 2023 paper "Self-Supervised Motion Magnification by Backpropagating Through Optical Flow" |

Replayed scored provider-pool top-10:

| Rank | Repo | Score | Raw | Role | Cap | Stars | Archived | Signals |
|---:|---|---:|---:|---|---|---:|---|---|
| 1 | `princeton-vl/raft` | `0.8171` | `0.8171` | `official_implementation` | `none` | 4025 | no | repository text mentions the requested paper title; has training code; has eval code |
| 2 | `dangeng/flowmag` | `0.7012` | `0.7012` | `official_implementation` | `none` | 42 | no | has training code; has eval code; has config |
| 3 | `david-zhao-1997/high-frequency-stereo-matching-network` | `0.5897` | `0.5897` | `official_implementation` | `incomplete_execution_cap` | 123 | no | repository text matches task: computer_vision; has checkpoint hint; has results |
| 4 | `rapidsai/raft` | `0.4680` | `0.4680` | `unknown` | `incomplete_execution_cap` | 1002 | no | has config; has requirements; detects tech stack: cuda, python, conda |
| 5 | `abdo-eldesokey/raft-ncup` | `0.4337` | `0.4337` | `official_implementation` | `weak_assets_cap` | 39 | no | detects tech stack: pytorch, python; classified as official_implementation |
| 6 | `mcg-nku/amt` | `0.4210` | `0.4210` | `official_implementation` | `weak_assets_cap` | 266 | no | detects tech stack: python; classified as official_implementation |
| 7 | `jinlab-imvr/deform3dgs` | `0.4093` | `0.4093` | `official_implementation` | `weak_assets_cap` | 90 | no | detects tech stack: python; classified as official_implementation |
| 8 | `mulns/pervfi` | `0.4079` | `0.4079` | `official_implementation` | `weak_assets_cap` | 79 | no | detects tech stack: python; classified as official_implementation |
| 9 | `etcd-io/raft` | `0.4016` | `0.4016` | `unknown` | `incomplete_execution_cap` | 1020 | no | has config; has requirements; detects tech stack: docker |
| 10 | `mulns/accflow` | `0.3965` | `0.3965` | `official_implementation` | `weak_assets_cap` | 27 | no | detects tech stack: python; classified as official_implementation |

### `monodepth2_2019`

- Paper title: Digging Into Self-Supervised Monocular Depth Estimation
- Expected official repo: `nianticlabs/monodepth2`
- Full benchmark top-3: `icaruswizard/monodepth2-paddle`, `xxxvincent/monodepth2`, `fangget/tf-monodepth2`
- Search queries: `monodepth2 in:name archived:false`, `monodepth2 "official code" in:name,description,readme archived:false`, `monodepth_2 in:name archived:false`, `monodepth_2 "official code" in:name,description,readme archived:false`, `monodepth-2 in:name archived:false`, `monodepth-2 "official code" in:name,description,readme archived:false`, `self-supervised in:name archived:false`, `self-supervised "official code" in:name,description,readme archived:false`, `self_supervised in:name archived:false`, `self_supervised "official code" in:name,description,readme archived:false`, `"Digging Into Self-Supervised Monocular Depth Estimation" in:name archived:false`, `digging-into-self-supervised-monocular-depth-estimation in:name archived:false`
- Generated aliases: `monodepth2`, `monodepth_2`, `monodepth-2`, `self-supervised`, `self_supervised`, `selfsupervised`
- Identity matches: none
- Official appears in raw GitHub query results: `yes` (q1 rank 1; q3 rank 1; q5 rank 1)
- Official in provider-considered pool: `yes`; sources: `{'nianticlabs/monodepth2': 'search_query_1'}`
- Official scored ranks in replayed provider pool: `{'nianticlabs/monodepth2': 3}`
- Direct official fetch score: `0.6657` raw=`0.6657` role=`implementation` cap=`incomplete_execution_cap`
- Current targeted service top-3: `eddiespade/monodepth2`, `icaruswizard/monodepth2-paddle`, `nianticlabs/monodepth2`
- Classification: `live_search_drift`; labels: `live_search_drift`
- Next minimal step: Rerun targeted validation and compare raw query positions; this may not need a logic change.

Provider-considered raw candidates:

| Rank | Source | Repo | Stars | Archived | Description |
|---:|---|---|---:|---|---|
| 1 | `search_query_1` | `nianticlabs/monodepth2` | 4479 | no | [ICCV 2019] Monocular depth estimation from a single image |
| 2 | `search_query_1` | `xxxvincent/monodepth2` | 21 | no | Mono depth on nuscenes dataset |
| 3 | `search_query_1` | `eddiespade/monodepth2` | 21 | no | 自写注释 |
| 4 | `search_query_1` | `fangget/tf-monodepth2` | 82 | no | Tensorflow implementation(unofficial) of "Digging into Self-Supervised Monocular Depth Prediction" |
| 5 | `search_query_1` | `tengfeihan0/monodepth2.cpp` | 19 | no | This is a pure C++ implementation of a very popular depth estimation network named monodepth2. This entire project is totally based on Libtorch. |
| 6 | `search_query_1` | `chansoopark98/deep-visual-slam-monodepth2` | 14 | no | Deep based Visual SLAM Project(Depth estimation, Optical flow, Visual inertial odometry) |
| 7 | `search_query_1` | `pxl-th/monodepth2.jl` | 13 | no | Self-supervised monocular depth estimation |
| 8 | `search_query_1` | `dacoim/monodepth2` | 3 | no |  |
| 9 | `search_query_1` | `sohamtamba/monodepth2` | 3 | no | DL project: Find monocular depth from videos |
| 10 | `search_query_1` | `icaruswizard/monodepth2-paddle` | 5 | no | PaddlePaddle Implementation of Monodepth2 |
| 11 | `search_query_2` | `naufalso/adversarial-manhole` | 3 | no | Official code for "Adversarial Manholes: Challenging Monocular Depth Estimation and Semantic Segmentation with Physical Attacks" |
| 12 | `search_query_2` | `ecalpal/iterdepth` | 9 | no | The official code of IterDepth: Iterative Residual Refinement for Outdoor Self-Supervised Multi-Frame Monocular Depth Estimation |

Replayed scored provider-pool top-10:

| Rank | Repo | Score | Raw | Role | Cap | Stars | Archived | Signals |
|---:|---|---:|---:|---|---|---:|---|---|
| 1 | `eddiespade/monodepth2` | `0.7260` | `0.7260` | `implementation` | `none` | 21 | no | repository text matches task: computer_vision; has training code; has eval code |
| 2 | `icaruswizard/monodepth2-paddle` | `0.7118` | `0.7118` | `reproduction` | `none` | 5 | no | repository text mentions the requested paper title; has training code; has eval code |
| 3 | `nianticlabs/monodepth2` | `0.6657` | `0.6657` | `implementation` | `incomplete_execution_cap` | 4479 | no | repository text matches task: computer_vision; has training code; has requirements |
| 4 | `xxxvincent/monodepth2` | `0.6080` | `0.6080` | `implementation` | `incomplete_execution_cap` | 21 | no | repository text matches task: computer_vision; has training code; has requirements |
| 5 | `fangget/tf-monodepth2` | `0.6074` | `0.6074` | `reproduction` | `incomplete_execution_cap` | 82 | no | repository text matches task: computer_vision; has config; has requirements |
| 6 | `ecalpal/iterdepth` | `0.5747` | `0.5747` | `official_implementation` | `none` | 9 | no | has training code; has dataset doc; has checkpoint hint |
| 7 | `tengfeihan0/monodepth2.cpp` | `0.5715` | `0.5715` | `official_implementation` | `incomplete_execution_cap` | 19 | no | has config; has requirements; has dataset doc |
| 8 | `dacoim/monodepth2` | `0.5695` | `0.5695` | `implementation` | `incomplete_execution_cap` | 3 | no | repository text matches task: computer_vision; has training code; has requirements |
| 9 | `sohamtamba/monodepth2` | `0.5695` | `0.5695` | `implementation` | `incomplete_execution_cap` | 3 | no | repository text matches task: computer_vision; has training code; has requirements |
| 10 | `chansoopark98/deep-visual-slam-monodepth2` | `0.5284` | `0.5284` | `official_implementation` | `incomplete_execution_cap` | 14 | no | has requirements; has dataset doc; detects tech stack: pytorch, cuda, opencv, python |

## Recommended Next Round

- Do not change scorer first: the current failures are primarily recall/pool drift until a case is proven to be scored but ranked below Top-3.
- Do not enter Papers with Code yet: all five expected official repos are concrete GitHub repos; first decide whether direct-fetch identity injection is sufficient for each provider recall miss.
- If a case has direct fetch success but no raw query hit, the narrowest repair is an evidence-backed curated official identity for that specific paper/repo, not a broad retrieval-profile expansion.

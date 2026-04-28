# Candidate Score Audit

This report audits only the eight benchmark cases where a direct owner/name-style signal appears plausible but the labeled official repository is still absent from final top-3.

## Scope

- Main retrieval, provider, and scorer logic were not changed.
- The audit script replays GitHub candidate collection, enriches the same search-stage metadata, and computes score components with existing scorer helpers.
- If an official repo is absent from the replayed raw pool, its score is reported as `score_if_added` from a separate fetch for diagnosis only.

## Aggregate Classification

- `retrieval_pool: direct fetch attempted but did not return the labeled official repo`: `6` cases
- `retrieval_pool: canonical alias does not exactly generate the labeled official repo`: `1` cases
- `scorer_cap: official repo is present but capped below competitors`: `1` cases

## Case Summary

| Case | Official repo | Report top-3 | Official in raw pool | Direct pair | Direct fetched | Official score | Classification |
|---|---|---|---|---|---|---:|---|
| `moco_2020` | `facebookresearch/moco` | `bl0/moco`, `leftthomas/moco`, `facebookresearch/moco` | `yes` | `yes` | `yes` | `0.7500` | `scorer_cap: official repo is present but capped below competitors` |
| `dino_2021` | `facebookresearch/dino` | `facebookresearch/dino`, `idea-research/dino`, `jiawei-yang/denoising-vit` | `no` | `yes` | `no` | `0.0000` | `retrieval_pool: direct fetch attempted but did not return the labeled official repo` |
| `stylegan2_ada_2020` | `nvlabs/stylegan2-ada-pytorch` | `nvlabs/stylegan2-ada-pytorch`, `woctezuma/steam-stylegan2-ada`, `jeffheaton/docker-stylegan2-ada` | `no` | `no` | `no` | `0.0000` | `retrieval_pool: canonical alias does not exactly generate the labeled official repo` |
| `bert_2018` | `google-research/bert` | `google-research/bert`, `ymcui/chinese-bert-wwm`, `bojone/bert4keras` | `no` | `yes` | `no` | `0.0000` | `retrieval_pool: direct fetch attempted but did not return the labeled official repo` |
| `mask2former_2021` | `facebookresearch/mask2former` | `facebookresearch/mask2former`, `luckydog-lhy/tensorrt_mask2former`, `yarrowqiao/semask-mask2former` | `no` | `yes` | `no` | `0.0000` | `retrieval_pool: direct fetch attempted but did not return the labeled official repo` |
| `fairseq_2019` | `facebookresearch/fairseq` | `facebookresearch/fairseq`, `kanyun-inc/fairseq-gec`, `martiansideofthemoon/style-transfer-paraphrase` | `no` | `yes` | `no` | `0.0000` | `retrieval_pool: direct fetch attempted but did not return the labeled official repo` |
| `transformers_2020` | `huggingface/transformers` | `huggingface/transformers`, `mlfoundations/transformers`, `compvis/taming-transformers` | `no` | `yes` | `no` | `0.0000` | `retrieval_pool: direct fetch attempted but did not return the labeled official repo` |
| `mmdetection_2019` | `open-mmlab/mmdetection` | `allenai/mmdetection`, `open-mmlab/mmdetection`, `hhaandroid/mmdetection-mini` | `no` | `yes` | `no` | `0.0000` | `retrieval_pool: direct fetch attempted but did not return the labeled official repo` |

## Case Details

### `moco_2020`

- Paper: Momentum Contrast for Unsupervised Visual Representation Learning
- Expected official repo: `facebookresearch/moco`
- Current benchmark top-3: `bl0/moco`, `leftthomas/moco`, `facebookresearch/moco`
- Replayed provider top-3: `facebookresearch/moco`, `bl0/moco`, `leftthomas/moco`
- Aliases: `moco`, `mo_co`, `mo-co`, `moco-pytorch`, `mo_co-pytorch`, `mo-co-pytorch`
- Official in raw candidate pool: `yes`; raw rank: `1`; source: `direct_fetch`
- Official direct pair attempted: `yes`; direct fetched: `yes`
- Official fetch error: `none`
- Official score: `0.7500`; raw score: `0.5941`; cap: `weak_assets_cap`; role: `official_implementation`
- Official reference utility: primary source for paper-author implementation claims
- Official README/root signals: readme=`no`, root_paths=`0`
- Official loses on: `query/paper identity match`, `tech stack match`, `score cap: weak_assets_cap`, `README missing from search-stage enrichment`, `root tree missing from search-stage enrichment`
- Diagnosis: `scorer_cap: official repo is present but capped below competitors`

Current benchmark top candidate scores:

| Repo | Score | Raw | Role | Cap | Assets | Readme/root | Reference utility |
|---|---:|---:|---|---|---|---|---|
| `bl0/moco` | `0.5751` | `0.5751` | `reproduction` | `weak_assets_cap` | none | no/0 | cross-check reference for independent reproduction attempts |
| `leftthomas/moco` | `0.5348` | `0.5348` | `unknown` | `weak_assets_cap` | none | no/0 | none |
| `facebookresearch/moco` | `0.7500` | `0.5941` | `official_implementation` | `weak_assets_cap` | none | no/0 | primary source for paper-author implementation claims |

Replayed provider top candidate scores:

| Repo | Score | Raw | Role | Cap | Assets | Readme/root | Reference utility |
|---|---:|---:|---|---|---|---|---|
| `facebookresearch/moco` | `0.7500` | `0.5941` | `official_implementation` | `weak_assets_cap` | none | no/0 | primary source for paper-author implementation claims |
| `bl0/moco` | `0.5751` | `0.5751` | `reproduction` | `weak_assets_cap` | none | no/0 | cross-check reference for independent reproduction attempts |
| `leftthomas/moco` | `0.5348` | `0.5348` | `unknown` | `weak_assets_cap` | none | no/0 | none |

Official score components:

| Query | Assets | Freshness | Popularity | Tech | Role bonus | Risk penalty | Cap reason |
|---:|---:|---:|---:|---:|---:|---:|---|
| `0.4000` | `0.2000` | `1.0000` | `0.9275` | `0.3333` | `0.2200` | `0.0600` | `weak_assets_cap` |

### `dino_2021`

- Paper: Emerging Properties in Self-Supervised Vision Transformers
- Expected official repo: `facebookresearch/dino`
- Current benchmark top-3: `facebookresearch/dino`, `idea-research/dino`, `jiawei-yang/denoising-vit`
- Replayed provider top-3: none
- Aliases: `dino`, `self-supervised`, `self_supervised`, `selfsupervised`, `dino-pytorch`, `self-supervised-pytorch`, `self_supervised-pytorch`, `selfsupervised-pytorch`
- Official in raw candidate pool: `no`; raw rank: `n/a`; source: `n/a`
- Official direct pair attempted: `yes`; direct fetched: `no`
- Official fetch error: `network error: ConnectError`
- Official score: `0.0000`; raw score: `0.0000`; cap: `fetch_failed`; role: `unknown`
- Official reference utility: none
- Official README/root signals: readme=`no`, root_paths=`0`
- Official loses on: none
- Diagnosis: `retrieval_pool: direct fetch attempted but did not return the labeled official repo`

Current benchmark top candidate scores:

| Repo | Score | Raw | Role | Cap | Assets | Readme/root | Reference utility |
|---|---:|---:|---|---|---|---|---|

Replayed provider top candidate scores:

| Repo | Score | Raw | Role | Cap | Assets | Readme/root | Reference utility |
|---|---:|---:|---|---|---|---|---|

Official score components:

| Query | Assets | Freshness | Popularity | Tech | Role bonus | Risk penalty | Cap reason |
|---:|---:|---:|---:|---:|---:|---:|---|
| `0.0000` | `0.0000` | `0.0000` | `0.0000` | `0.0000` | `0.0000` | `0.0000` | `fetch_failed` |

### `stylegan2_ada_2020`

- Paper: Training Generative Adversarial Networks with Limited Data
- Expected official repo: `nvlabs/stylegan2-ada-pytorch`
- Current benchmark top-3: `nvlabs/stylegan2-ada-pytorch`, `woctezuma/steam-stylegan2-ada`, `jeffheaton/docker-stylegan2-ada`
- Replayed provider top-3: none
- Aliases: `stylegan2-ada`, `stylegan2_ada`, `stylegan2ada`, `stylegan_2_ada`, `stylegan-2-ada`, `stylegan2-ada-pytorch`, `stylegan2`, `style_gan_2`
- Official in raw candidate pool: `no`; raw rank: `n/a`; source: `n/a`
- Official direct pair attempted: `no`; direct fetched: `no`
- Official fetch error: `network error: ConnectError`
- Official score: `0.0000`; raw score: `0.0000`; cap: `fetch_failed`; role: `unknown`
- Official reference utility: none
- Official README/root signals: readme=`no`, root_paths=`0`
- Official loses on: none
- Diagnosis: `retrieval_pool: canonical alias does not exactly generate the labeled official repo`

Current benchmark top candidate scores:

| Repo | Score | Raw | Role | Cap | Assets | Readme/root | Reference utility |
|---|---:|---:|---|---|---|---|---|

Replayed provider top candidate scores:

| Repo | Score | Raw | Role | Cap | Assets | Readme/root | Reference utility |
|---|---:|---:|---|---|---|---|---|

Official score components:

| Query | Assets | Freshness | Popularity | Tech | Role bonus | Risk penalty | Cap reason |
|---:|---:|---:|---:|---:|---:|---:|---|
| `0.0000` | `0.0000` | `0.0000` | `0.0000` | `0.0000` | `0.0000` | `0.0000` | `fetch_failed` |

### `bert_2018`

- Paper: BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding
- Expected official repo: `google-research/bert`
- Current benchmark top-3: `google-research/bert`, `ymcui/chinese-bert-wwm`, `bojone/bert4keras`
- Replayed provider top-3: none
- Aliases: `bert`
- Official in raw candidate pool: `no`; raw rank: `n/a`; source: `n/a`
- Official direct pair attempted: `yes`; direct fetched: `no`
- Official fetch error: `network error: ConnectError`
- Official score: `0.0000`; raw score: `0.0000`; cap: `fetch_failed`; role: `unknown`
- Official reference utility: none
- Official README/root signals: readme=`no`, root_paths=`0`
- Official loses on: none
- Diagnosis: `retrieval_pool: direct fetch attempted but did not return the labeled official repo`

Current benchmark top candidate scores:

| Repo | Score | Raw | Role | Cap | Assets | Readme/root | Reference utility |
|---|---:|---:|---|---|---|---|---|

Replayed provider top candidate scores:

| Repo | Score | Raw | Role | Cap | Assets | Readme/root | Reference utility |
|---|---:|---:|---|---|---|---|---|

Official score components:

| Query | Assets | Freshness | Popularity | Tech | Role bonus | Risk penalty | Cap reason |
|---:|---:|---:|---:|---:|---:|---:|---|
| `0.0000` | `0.0000` | `0.0000` | `0.0000` | `0.0000` | `0.0000` | `0.0000` | `fetch_failed` |

### `mask2former_2021`

- Paper: Masked-attention Mask Transformer for Universal Image Segmentation
- Expected official repo: `facebookresearch/mask2former`
- Current benchmark top-3: `facebookresearch/mask2former`, `luckydog-lhy/tensorrt_mask2former`, `yarrowqiao/semask-mask2former`
- Replayed provider top-3: none
- Aliases: `mask2former`, `mask_2_former`, `mask-2-former`
- Official in raw candidate pool: `no`; raw rank: `n/a`; source: `n/a`
- Official direct pair attempted: `yes`; direct fetched: `no`
- Official fetch error: `network error: ConnectError`
- Official score: `0.0000`; raw score: `0.0000`; cap: `fetch_failed`; role: `unknown`
- Official reference utility: none
- Official README/root signals: readme=`no`, root_paths=`0`
- Official loses on: none
- Diagnosis: `retrieval_pool: direct fetch attempted but did not return the labeled official repo`

Current benchmark top candidate scores:

| Repo | Score | Raw | Role | Cap | Assets | Readme/root | Reference utility |
|---|---:|---:|---|---|---|---|---|

Replayed provider top candidate scores:

| Repo | Score | Raw | Role | Cap | Assets | Readme/root | Reference utility |
|---|---:|---:|---|---|---|---|---|

Official score components:

| Query | Assets | Freshness | Popularity | Tech | Role bonus | Risk penalty | Cap reason |
|---:|---:|---:|---:|---:|---:|---:|---|
| `0.0000` | `0.0000` | `0.0000` | `0.0000` | `0.0000` | `0.0000` | `0.0000` | `fetch_failed` |

### `fairseq_2019`

- Paper: fairseq: A Fast, Extensible Toolkit for Sequence Modeling
- Expected official repo: `facebookresearch/fairseq`
- Current benchmark top-3: `facebookresearch/fairseq`, `kanyun-inc/fairseq-gec`, `martiansideofthemoon/style-transfer-paraphrase`
- Replayed provider top-3: none
- Aliases: `fairseq`
- Official in raw candidate pool: `no`; raw rank: `n/a`; source: `n/a`
- Official direct pair attempted: `yes`; direct fetched: `no`
- Official fetch error: `network error: ConnectError`
- Official score: `0.0000`; raw score: `0.0000`; cap: `fetch_failed`; role: `unknown`
- Official reference utility: none
- Official README/root signals: readme=`no`, root_paths=`0`
- Official loses on: none
- Diagnosis: `retrieval_pool: direct fetch attempted but did not return the labeled official repo`

Current benchmark top candidate scores:

| Repo | Score | Raw | Role | Cap | Assets | Readme/root | Reference utility |
|---|---:|---:|---|---|---|---|---|

Replayed provider top candidate scores:

| Repo | Score | Raw | Role | Cap | Assets | Readme/root | Reference utility |
|---|---:|---:|---|---|---|---|---|

Official score components:

| Query | Assets | Freshness | Popularity | Tech | Role bonus | Risk penalty | Cap reason |
|---:|---:|---:|---:|---:|---:|---:|---|
| `0.0000` | `0.0000` | `0.0000` | `0.0000` | `0.0000` | `0.0000` | `0.0000` | `fetch_failed` |

### `transformers_2020`

- Paper: Transformers: State-of-the-Art Natural Language Processing
- Expected official repo: `huggingface/transformers`
- Current benchmark top-3: `huggingface/transformers`, `mlfoundations/transformers`, `compvis/taming-transformers`
- Replayed provider top-3: none
- Aliases: `transformers`, `state-of-the-art`, `state_of_the_art`, `stateoftheart`
- Official in raw candidate pool: `no`; raw rank: `n/a`; source: `n/a`
- Official direct pair attempted: `yes`; direct fetched: `no`
- Official fetch error: `network error: ConnectError`
- Official score: `0.0000`; raw score: `0.0000`; cap: `fetch_failed`; role: `unknown`
- Official reference utility: none
- Official README/root signals: readme=`no`, root_paths=`0`
- Official loses on: none
- Diagnosis: `retrieval_pool: direct fetch attempted but did not return the labeled official repo`

Current benchmark top candidate scores:

| Repo | Score | Raw | Role | Cap | Assets | Readme/root | Reference utility |
|---|---:|---:|---|---|---|---|---|

Replayed provider top candidate scores:

| Repo | Score | Raw | Role | Cap | Assets | Readme/root | Reference utility |
|---|---:|---:|---|---|---|---|---|

Official score components:

| Query | Assets | Freshness | Popularity | Tech | Role bonus | Risk penalty | Cap reason |
|---:|---:|---:|---:|---:|---:|---:|---|
| `0.0000` | `0.0000` | `0.0000` | `0.0000` | `0.0000` | `0.0000` | `0.0000` | `fetch_failed` |

### `mmdetection_2019`

- Paper: MMDetection: Open MMLab Detection Toolbox and Benchmark
- Expected official repo: `open-mmlab/mmdetection`
- Current benchmark top-3: `allenai/mmdetection`, `open-mmlab/mmdetection`, `hhaandroid/mmdetection-mini`
- Replayed provider top-3: none
- Aliases: `mmdetection`, `mm_detection`, `mm-detection`, `mmlab`, `mm_lab`, `mm-lab`
- Official in raw candidate pool: `no`; raw rank: `n/a`; source: `n/a`
- Official direct pair attempted: `yes`; direct fetched: `no`
- Official fetch error: `network error: ConnectError`
- Official score: `0.0000`; raw score: `0.0000`; cap: `fetch_failed`; role: `unknown`
- Official reference utility: none
- Official README/root signals: readme=`no`, root_paths=`0`
- Official loses on: none
- Diagnosis: `retrieval_pool: direct fetch attempted but did not return the labeled official repo`

Current benchmark top candidate scores:

| Repo | Score | Raw | Role | Cap | Assets | Readme/root | Reference utility |
|---|---:|---:|---|---|---|---|---|

Replayed provider top candidate scores:

| Repo | Score | Raw | Role | Cap | Assets | Readme/root | Reference utility |
|---|---:|---:|---|---|---|---|---|

Official score components:

| Query | Assets | Freshness | Popularity | Tech | Role bonus | Risk penalty | Cap reason |
|---:|---:|---:|---:|---:|---:|---:|---|
| `0.0000` | `0.0000` | `0.0000` | `0.0000` | `0.0000` | `0.0000` | `0.0000` | `fetch_failed` |

## Evidence-Backed Next Directions

1. For cases where the official repo is absent before scoring, inspect canonical direct-fetch alias generation and raw candidate cutoff before touching score weights.
2. For cases where the official repo is present but loses, consider a narrowly scoped scorer/cap adjustment only after comparing candidate component scores and caps.

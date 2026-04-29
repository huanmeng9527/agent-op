# Official Recall Drift Diagnostics

This report diagnoses only the four full-benchmark cases where the labeled official repository is absent from top-3. It does not change scorer, retrieval, provider, or identity logic.

## Full Benchmark Context

- Total/evaluated: `53` / `53`
- Top-1 / Top-3: `0.6792` / `0.9245`
- Official Top-1 / Top-3: `0.566` / `0.7925`
- Distractor ranked #1: `0.0`
- Targeted cases: `dino_2021`, `bert_2018`, `mask2former_2021`, `transformers_2020`

## Root Cause Summary

- `scorer/cap regression candidate`: `2`
- `full-run drift; current replay recalls official`: `1`
- `identity_overmatching with alias/prefix collision`: `1`

## Case Summary

| Case | Expected official | Current top-3 | Raw pool | Direct fetch | Scored | Replay top-k dropped | Root cause |
|---|---|---|---|---|---|---|---|
| `dino_2021` | `facebookresearch/dino` | `facebookresearch/dinov3`, `idea-research/dino`, `google-research/vision_transformer` | yes | yes | yes | yes | `identity_overmatching with alias/prefix collision` |
| `bert_2018` | `google-research/bert` | `ymcui/chinese-bert-wwm`, `bojone/bert4keras`, `jessevig/bertviz` | yes | yes | yes | yes | `scorer/cap regression candidate` |
| `mask2former_2021` | `facebookresearch/mask2former` | `luckydog-lhy/tensorrt_mask2former`, `yarrowqiao/semask-mask2former`, `carti-97/dinov3-mask2former` | yes | yes | yes | yes | `scorer/cap regression candidate` |
| `transformers_2020` | `huggingface/transformers` | `mlfoundations/transformers`, `microsoft/huggingface-transformers`, `kyubyong/transformer` | yes | yes | yes | no | `full-run drift; current replay recalls official` |

## Case Details

### `dino_2021`

- Paper: Emerging Properties in Self-Supervised Vision Transformers
- Expected official repo: `facebookresearch/dino`
- Current top-3 candidates: `facebookresearch/dinov3`, `idea-research/dino`, `google-research/vision_transformer`
- Official repo in replayed raw candidate pool: `yes`; sources: `{'facebookresearch/dino': 'direct_fetch'}`
- Official repo direct pair attempted: `yes`; direct fetched: `yes`
- Official fetch/score if directly fetched: `0.6000` role=`official_implementation` cap=`archived_cap`
- Official fetch errors: none
- Official repo scored in replayed pool: `yes`; replay ranks: `{'facebookresearch/dino': 4}`
- Official absent from current full-report top-3: `yes`
- Official dropped by replayed top-k retention: `yes`
- Prefix/alias collision notes: facebookresearch/dinov3 prefix/contains official slug `dino`; idea-research/dino has the same slug as facebookresearch/dino
- Identity candidate overmatching: `google-research/vision_transformer`
- Cap/role notes: facebookresearch/dino cap=archived_cap
- Most likely root cause: `identity_overmatching with alias/prefix collision`
- Next minimal fix suggestion: Tighten curated identity matching so title-token overlap cannot attach an unrelated official identity unless paper_id/arXiv/exact title agrees.

Replayed raw-pool top-5 by current scorer:

| Rank | Repo | Score | Role | Cap | Stars | Archived |
|---:|---|---:|---|---|---:|---|
| 1 | `facebookresearch/dinov3` | `0.6800` | `official_implementation` | `incomplete_execution_cap` | 10251 | no |
| 2 | `idea-research/dino` | `0.6739` | `official_implementation` | `incomplete_execution_cap` | 2789 | no |
| 3 | `idea-research/groundingdino` | `0.6290` | `official_implementation` | `incomplete_execution_cap` | 10057 | no |
| 4 | `facebookresearch/dino` | `0.6000` | `official_implementation` | `archived_cap` | 7541 | yes |
| 5 | `facebookresearch/dinov2` | `0.5664` | `paper_collection` | `paper_collection_cap` | 12775 | no |

### `bert_2018`

- Paper: BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding
- Expected official repo: `google-research/bert`
- Current top-3 candidates: `ymcui/chinese-bert-wwm`, `bojone/bert4keras`, `jessevig/bertviz`
- Official repo in replayed raw candidate pool: `yes`; sources: `{'google-research/bert': 'direct_fetch'}`
- Official repo direct pair attempted: `yes`; direct fetched: `yes`
- Official fetch/score if directly fetched: `0.6000` role=`official_implementation` cap=`archived_cap`
- Official fetch errors: none
- Official repo scored in replayed pool: `yes`; replay ranks: `{'google-research/bert': 5}`
- Official absent from current full-report top-3: `yes`
- Official dropped by replayed top-k retention: `yes`
- Prefix/alias collision notes: ymcui/chinese-bert-wwm prefix/contains official slug `bert`; bojone/bert4keras prefix/contains official slug `bert`; jessevig/bertviz prefix/contains official slug `bert`
- Identity candidate overmatching: none
- Cap/role notes: google-research/bert cap=archived_cap
- Most likely root cause: `scorer/cap regression candidate`
- Next minimal fix suggestion: Design a very narrow archived-official collision check before changing anything: exact expected owner/name is present, same/prefix-slug competitors lead, and the official loses only because of archived_cap.

Replayed raw-pool top-5 by current scorer:

| Rank | Repo | Score | Role | Cap | Stars | Archived |
|---:|---|---:|---|---|---:|---|
| 1 | `ymcui/chinese-bert-wwm` | `0.7244` | `official_implementation` | `incomplete_execution_cap` | 10201 | no |
| 2 | `bojone/bert4keras` | `0.6674` | `official_implementation` | `incomplete_execution_cap` | 5420 | no |
| 3 | `jessevig/bertviz` | `0.6470` | `official_implementation` | `incomplete_execution_cap` | 8035 | no |
| 4 | `fishaudio/bert-vits2` | `0.6182` | `official_implementation` | `incomplete_execution_cap` | 8735 | no |
| 5 | `google-research/bert` | `0.6000` | `official_implementation` | `archived_cap` | 40003 | yes |

### `mask2former_2021`

- Paper: Masked-attention Mask Transformer for Universal Image Segmentation
- Expected official repo: `facebookresearch/mask2former`
- Current top-3 candidates: `luckydog-lhy/tensorrt_mask2former`, `yarrowqiao/semask-mask2former`, `carti-97/dinov3-mask2former`
- Official repo in replayed raw candidate pool: `yes`; sources: `{'facebookresearch/mask2former': 'direct_fetch'}`
- Official repo direct pair attempted: `yes`; direct fetched: `yes`
- Official fetch/score if directly fetched: `0.6000` role=`official_implementation` cap=`archived_cap`
- Official fetch errors: none
- Official repo scored in replayed pool: `yes`; replay ranks: `{'facebookresearch/mask2former': 4}`
- Official absent from current full-report top-3: `yes`
- Official dropped by replayed top-k retention: `yes`
- Prefix/alias collision notes: luckydog-lhy/tensorrt_mask2former prefix/contains official slug `mask2former`; yarrowqiao/semask-mask2former prefix/contains official slug `mask2former`; carti-97/dinov3-mask2former prefix/contains official slug `mask2former`
- Identity candidate overmatching: none
- Cap/role notes: facebookresearch/mask2former cap=archived_cap
- Most likely root cause: `scorer/cap regression candidate`
- Next minimal fix suggestion: Design a very narrow archived-official collision check before changing anything: exact expected owner/name is present, same/prefix-slug competitors lead, and the official loses only because of archived_cap.

Replayed raw-pool top-5 by current scorer:

| Rank | Repo | Score | Role | Cap | Stars | Archived |
|---:|---|---:|---|---|---:|---|
| 1 | `luckydog-lhy/tensorrt_mask2former` | `0.6530` | `official_implementation` | `incomplete_execution_cap` | 30 | no |
| 2 | `yarrowqiao/semask-mask2former` | `0.6364` | `implementation` | `none` | 10 | no |
| 3 | `carti-97/dinov3-mask2former` | `0.6031` | `official_implementation` | `incomplete_execution_cap` | 57 | no |
| 4 | `facebookresearch/mask2former` | `0.6000` | `official_implementation` | `archived_cap` | 3334 | yes |
| 5 | `lantudou/mask2former_trt` | `0.5948` | `official_implementation` | `incomplete_execution_cap` | 26 | no |

### `transformers_2020`

- Paper: Transformers: State-of-the-Art Natural Language Processing
- Expected official repo: `huggingface/transformers`
- Current top-3 candidates: `mlfoundations/transformers`, `microsoft/huggingface-transformers`, `kyubyong/transformer`
- Official repo in replayed raw candidate pool: `yes`; sources: `{'huggingface/transformers': 'direct_fetch'}`
- Official repo direct pair attempted: `yes`; direct fetched: `yes`
- Official fetch/score if directly fetched: `0.7994` role=`official_implementation` cap=`none`
- Official fetch errors: none
- Official repo scored in replayed pool: `yes`; replay ranks: `{'huggingface/transformers': 1}`
- Official absent from current full-report top-3: `yes`
- Official dropped by replayed top-k retention: `no`
- Prefix/alias collision notes: mlfoundations/transformers has the same slug as huggingface/transformers; microsoft/huggingface-transformers prefix/contains official slug `transformers`; kyubyong/transformer near-matches official slug `transformers`
- Identity candidate overmatching: none
- Cap/role notes: none
- Most likely root cause: `full-run drift; current replay recalls official`
- Next minimal fix suggestion: Audit exact expected-owner direct fetch retention for same-slug collisions such as huggingface/transformers vs mlfoundations/transformers.

Replayed raw-pool top-5 by current scorer:

| Rank | Repo | Score | Role | Cap | Stars | Archived |
|---:|---|---:|---|---|---:|---|
| 1 | `huggingface/transformers` | `0.7994` | `official_implementation` | `none` | 160077 | no |
| 2 | `mlfoundations/transformers` | `0.7500` | `official_implementation` | `none` | 0 | no |
| 3 | `huggingface/sentence-transformers` | `0.6440` | `official_implementation` | `incomplete_execution_cap` | 18608 | no |
| 4 | `compvis/taming-transformers` | `0.6086` | `official_implementation` | `incomplete_execution_cap` | 6482 | no |
| 5 | `huggingface/transformers.js` | `0.6080` | `official_implementation` | `weak_assets_cap` | 15936 | no |

## Recommendations

- First fix DINO-style identity overmatching with a narrow identity-match guard; it is the clearest non-scoring failure and has direct evidence in the current full report.
- Then inspect a very narrow archived-official collision policy for BERT and Mask2Former: exact official repo is present, but archived_cap leaves it behind prefix/same-slug variants.
- Treat Transformers as live-run drift before changing logic: the targeted replay places huggingface/transformers at rank 1, so rerun targeted validation after any narrow fix.
- Do not enter Papers with Code yet: these four failures are already about exact official GitHub identities drifting out of the candidate pool, not missing external project-page discovery.

# YOLOv7 Targeted Diagnostics

This report diagnoses only `yolov7_2022`. It does not modify scorer, retrieval, provider, identity, or benchmark logic.

## Benchmark Entry

- Paper title: YOLOv7: Trainable bag-of-freebies sets new state-of-the-art for real-time object detectors
- Query: `YOLOv7 Trainable bag-of-freebies real-time object detectors code`
- Official repos: `WongKinYiu/yolov7`
- High-quality reproduction repos: `ultralytics/yolov5`
- Common distractor repos: `ultralytics/ultralytics`
- Repo aliases generated from the current query: `yolov7`, `yol_ov_7`, `yol-ov-7`

## Current Full Benchmark Result

- Current top-3: `xinwei666/mmgenerativeir`, `wutianxu/archive_page`, `dbacea/yolo-tiny-hp-cse-d2s-rfb`
- Failure cause: `official_repo_not_recalled`
- Official rank: `None`
- Acceptable rank: `None`
- Provider status: `{'paper_code_identity': {'ok': True, 'result_count': 0, 'matched_repos': [], 'matched_identity_types': []}, 'github': {'ok': True, 'result_count': 3}}`

## Targeted Replay Findings

- Identity matches: none
- Provider canonical direct fetch attempted official owner/name: `no`
- Manual official direct fetch succeeded: `yes`
- Manual official fetch error: `none`
- Official score if fetched directly: `0.7667`; role=`official_implementation`; cap=`incomplete_execution_cap`; archived=`no`; fork=`no`
- Official repo in replayed raw candidate pool: `yes`
- Official raw source: `search_query_1`
- Official replay rank: `1`
- Raw candidate count: `27`
- Raw candidate sample: `wongkinyiu/yolov7`, `lucasjinreal/yolov7_d2`, `bubbliiiing/yolov7-pytorch`, `dataxujing/yolov7`, `rizwanmunawar/yolov7-object-tracking`, `jackwoo0831/yolov7-tracker`, `derronqi/yolov7-face`, `we0091234/yolov7_plate`, `rizwanmunawar/yolov7-segmentation`, `rizwanmunawar/yolov7-pose-estimation`, `coderonion/awesome-yolo-object-detection`, `rizwanmunawar/yolo-rx57-fps-comparision`, `xinwei666/mmgenerativeir`, `dbacea/yolo-tiny-hp-cse-d2s-rfb`, `circ-leaf/niom`
- Raw replay errors: none

## Current Full Top-3 Candidate Types

| Repo | Type | Score / Role / Cap | Fetch error |
|---|---|---|---|
| `xinwei666/mmgenerativeir` | reproduction | `0.7436`; role=`reproduction`; cap=`none`; archived=`no`; fork=`no` | none |
| `wutianxu/archive_page` | official_implementation, capped by incomplete_execution_cap | `0.6144`; role=`official_implementation`; cap=`incomplete_execution_cap`; archived=`no`; fork=`no` | none |
| `dbacea/yolo-tiny-hp-cse-d2s-rfb` | YOLO alias/variant | `0.6065`; role=`official_implementation`; cap=`incomplete_execution_cap`; archived=`no`; fork=`no` | none |

## Replayed Top-10 By Current Scorer

| Rank | Repo | Score | Role | Cap | Stars | Archived | Fork |
|---:|---|---:|---|---|---:|---|---|
| 1 | `wongkinyiu/yolov7` | `0.7667` | `official_implementation` | `incomplete_execution_cap` | 14103 | no | no |
| 2 | `dataxujing/yolov7` | `0.7277` | `official_implementation` | `incomplete_execution_cap` | 50 | no | no |
| 3 | `rizwanmunawar/yolov7-segmentation` | `0.5874` | `implementation` | `incomplete_execution_cap` | 344 | no | no |
| 4 | `we0091234/yolov7_plate` | `0.5674` | `implementation` | `incomplete_execution_cap` | 398 | no | no |
| 5 | `rizwanmunawar/yolov7-pose-estimation` | `0.5428` | `model_zoo` | `model_zoo_cap` | 374 | no | no |
| 6 | `bubbliiiing/yolov7-pytorch` | `0.5137` | `implementation` | `incomplete_execution_cap` | 910 | no | no |
| 7 | `lucasjinreal/yolov7_d2` | `0.4810` | `official_implementation` | `weak_assets_cap` | 3112 | no | no |
| 8 | `rizwanmunawar/yolov7-object-tracking` | `0.4477` | `unknown` | `weak_assets_cap` | 650 | no | no |
| 9 | `jackwoo0831/yolov7-tracker` | `0.4120` | `demo_only` | `weak_assets_cap` | 782 | no | no |
| 10 | `xinwei666/mmgenerativeir` | `0.3969` | `official_implementation` | `weak_assets_cap` | 28 | no | no |

## Alias / Owner Collision Notes

- Current generated aliases include `yolov7`, `yol_ov_7`, and `yol-ov-7`; the exact official slug is available.
- The official owner `WongKinYiu` is not in the provider canonical-owner direct-fetch list, so the normal provider path relies on GitHub search unless an external identity mapping supplies this exact repo.
- The full-run top-3 did not include the labeled distractor `ultralytics/ultralytics`; this miss is not a YOLOv8/Ultralytics rank-1 distractor issue.
- Manual fetch returns `WongKinYiu/yolov7` at the same path, so this is not a renamed/redirect problem.

## Root Cause

- Most likely root cause: `GitHub live search volatility; current replay recalls the official repo`.
- Scorer/cap is not the primary issue: direct official fetch scores high enough for Top-3.
- Benchmark label looks valid: the fetched official repository description directly names the YOLOv7 paper.

## Next Minimal Fix Suggestion

- Prefer a curated official identity mapping for `yolov7_2022 -> WongKinYiu/yolov7` with evidence from the repository description/source URL. This is narrower and safer than broadening YOLO retrieval or adding `WongKinYiu` as a global canonical owner.
- Do not enter Papers with Code yet; the exact GitHub repository is known and direct fetch succeeds.

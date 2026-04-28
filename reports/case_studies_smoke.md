# Paper Reproduction Case Studies

## Segment Anything

- Case ID: `sam_2023`
- Query: `Segment Anything paper code pytorch CVPR 2023`

### Top Candidates

- `yatengLG/ISAT_with_segment_anything` role=`official_implementation` score=`0.7611` cap=`incomplete_execution_cap` evidence=repository name contains all requested paper-title tokens; repository text mentions the requested paper title; repository text matches task: computer_vision
- `z-x-yang/Segment-and-Track-Anything` role=`official_implementation` score=`0.7552` cap=`incomplete_execution_cap` evidence=repository name contains all requested paper-title tokens; repository text mentions the requested paper title; mentions target year 2023
- `Pointcept/SegmentAnything3D` role=`official_implementation` score=`0.7493` cap=`incomplete_execution_cap` evidence=repository name partially matches the requested paper title; repository text mentions the requested paper title; matches requested tech keyword: pytorch

### Deep Inspection

- Inspected repo: `yatenglg/isat_with_segment_anything` role=`official_implementation` score=`0.9447`
- Training readiness: partial: Training code is visible, but dataset/config/run evidence is incomplete. evidence=['ISAT/segment_any/sam3/train', 'ISAT/segment_any/sam3/train/__init__.py', 'ISAT/segment_any/sam3/train/data'] entries=['ISAT/segment_any/sam3/train', 'ISAT/segment_any/sam3/train/__init__.py', 'ISAT/segment_any/sam3/train/data', 'ISAT/segment_any/sam3/train/data/__init__.py']
- Evaluation readiness: ready: Evaluation entry points are present with metric/result, dataset, or run-instruction evidence. evidence=['ISAT/segment_any/sam3/eval/hota_eval_toolkit/trackeval/eval.py', 'ISAT/segment_any/sam3/eval/teta_eval_toolkit/eval.py'] entries=['ISAT/segment_any/sam3/eval/hota_eval_toolkit/trackeval/eval.py', 'ISAT/segment_any/sam3/eval/teta_eval_toolkit/eval.py']
- Environment reproducibility: documented: Environment files are present, but dependencies are not fully pinned. evidence=['docker', 'docker/Dockerfile', 'docker/entrypoint.sh']
- Paper identity confidence: low: No arXiv, DOI, or BibTeX identity evidence was detected.
- Checkpoint links: []

### Compare Decision

- Best overall: `z-x-yang/segment-and-track-anything`
- Direct reproduction: `z-x-yang/segment-and-track-anything`
- Method reference: `z-x-yang/segment-and-track-anything`
- Baseline: `z-x-yang/segment-and-track-anything`
- Not recommended: ['facebookresearch/segment-anything: evaluation script not detected, score capped by incomplete_execution_cap', 'pointcept/segmentanything3d: evaluation script not detected, score capped by incomplete_execution_cap']
- Summary: Use z-x-yang/segment-and-track-anything for direct reproduction, z-x-yang/segment-and-track-anything for implementation details, and z-x-yang/segment-and-track-anything for baseline comparison; verify any flagged risks before running experiments.

## End-to-End Object Detection with Transformers

- Case ID: `detr_2020`
- Query: `DETR End-to-End Object Detection with Transformers paper code pytorch ECCV 2020`

### Top Candidates

- `SZU-AdvTech-2024/336-End-to-End-Object-Detection-with-Transformers` role=`reproduction` score=`0.785` cap=`None` evidence=repository name contains all requested paper-title tokens; repository text mentions the requested paper title; matches requested tech keyword: transformers
- `vinish-ai/DETR-End-to-End-object-detection-with-Transformers` role=`official_implementation` score=`0.6143` cap=`incomplete_execution_cap` evidence=repository name contains all requested paper-title tokens; repository text mentions the requested paper title; repository text matches task: computer_vision
- `ChristophReich1996/Cell-DETR` role=`official_implementation` score=`0.4907` cap=`weak_assets_cap` evidence=matches requested tech keyword: transformers; mentions target year 2020; detects tech stack: transformers, python

### Deep Inspection

- `szu-advtech-2024/336-end-to-end-object-detection-with-transformers` inspection failed: HTTP 403: API rate limit exceeded for 188.253.124.73. (But here's the good news: Authenticated requests get a higher rate limit. Check out the documentation for more details.); remaining=0; reset_epoch=1777220324; set GITHUB_TOKEN in .env for authenticated requests

### Compare Decision

- Best overall: `None`
- Direct reproduction: `None`
- Method reference: `None`
- Baseline: `None`
- Not recommended: []
- Summary: No comparable repositories were inspected successfully.

# Attribution And Changes

GPLv3 adaptation of KalyanM45's House-Price-Prediction, discovered exclusively through
https://github.com/KalyanM45/AI-Project-Gallery .

- Upstream: https://github.com/KalyanM45/House-Price-Prediction
- Pinned upstream commit: 61515c0c4e70fca380728d8752048d38e48eeefa
- Original source history and full GPLv3 license are retained.
- Adaptation by Sushant Nemade, 2026-10-27: replace legacy Flask/pickle entry point;
  add strict named research inputs, exclude B and LSTAT, train-only model selection,
  independent calibration/test sets, checked ONNX export, browser workbench, API,
  tests, isolated local load measurement, packaging, and verified-SHA deployment.
- Upstream models are not executed or trusted. Historical notebook/output files are
  source lineage only, not the active application or benchmark evidence.

Reusable bounded-asset loading and build-notice patterns are adapted from
https://github.com/Sushant-Nemade/airbnb-price-workbench (MIT).
Its complete notice is retained in frontend/legal/airbnb-workbench-MIT.txt.

Dataset: Harrison, D. and Rubinfeld, D.L., "Hedonic housing prices and the demand
for clean air", Journal of Environmental Economics and Management 5 (1978), 81-102.
Access: OpenML dataset 531 version 1. OpenML's literal license label is "Public";
this is not treated as an explicit CC/OSI license or legal/commercial clearance.
Raw data are fetched for reproducible historical research, not vendored in the
source/wheel/site. Published parity probes are authored synthetic inputs.

Photo: "Boston skyline from Longfellow Bridge September 2017 panorama 2.jpg",
King of Hearts, CC BY-SA 4.0. Wikimedia thumbnail resizing and responsive display
cropping; image/crop remains CC BY-SA 4.0. Photo is context, not training evidence.
Source: https://commons.wikimedia.org/wiki/File:Boston_skyline_from_Longfellow_Bridge_September_2017_panorama_2.jpg
License: https://creativecommons.org/licenses/by-sa/4.0/

Bundled runtime, parser, icons, and font license texts are preserved in generated
licenses.json, with exact package versions recorded from the production bundle.
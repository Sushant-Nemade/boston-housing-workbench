# Boston Housing Research Workbench

[![Verify](https://github.com/Sushant-Nemade/boston-housing-workbench/actions/workflows/verify.yml/badge.svg)](https://github.com/Sushant-Nemade/boston-housing-workbench/actions/workflows/verify.yml)

[Public browser demo](https://sushant-nemade.github.io/boston-housing-workbench/) |
[Releases](https://github.com/Sushant-Nemade/boston-housing-workbench/releases) |
[Model report](src/boston_housing/artifacts/report.json) |
[Security review](docs/SECURITY_REVIEW.md)

An end-to-end, reproducible **historical research benchmark**, adapted under GPLv3
from [KalyanM45/House-Price-Prediction](https://github.com/KalyanM45/House-Price-Prediction),
discovered through [AI-Project-Gallery](https://github.com/KalyanM45/AI-Project-Gallery).
Original source history and license remain intact. See [NOTICE.md](NOTICE.md).

**This is NOT a current Boston house-price calculator.** Each observation is a
historical census tract, not an individual home. It must not be used for buying,
selling, appraisal, lending, eligibility, or housing allocation.

## Working Features

- Actual ONNX/WASM inference in the browser, without an API key or private server.
- Eleven strictly named, finite, bounded inputs. B and LSTAT are excluded.
- Estimates and historical residual bands, model/baseline charts, full provenance.
- Up to 20 local saved input scenarios, recomputed with the current verified model.
- Bounded 1-100-row CSV batches, template and formula-safe result exports.
- Stateless FastAPI `/api/health`, `/api/report`, `/api/predict`; 4 KB request limit.
- Checksummed model/data, authored parity probes, independent reproduction,
  unit/integration/browser/security checks, local workload evidence, wheel and source packages.

## Evidence And Limitations

OpenML 531 version 1: 506 historical rows. Train **323**, calibration **81**, untouched
test **102**. Five-fold model selection occurs only within training. Ridge scaling
is inside the CV pipeline. Gradient boosting was selected by training CV MAE.

| Held-out measure | Actual result |
| :--- | ---: |
| Model MAE, historical USD | $2,000.09 |
| Training-median baseline MAE | $5,882.35 |
| RMSE | $3,296.65 |
| R-squared | 0.8518 |
| Nominal 90% residual-band test coverage | 96.08% |
| Mean historical band width | $9,785.04 |
| ONNX/sklearn maximum error | below $0.02 |

These are **random-row historical test results**, not modern/spatially independent
valuation accuracy. Neighbouring tracts may be dependent. MEDV is top-coded at
$50,000; estimates/bands are clipped to the observed 5-50 thousand-dollar range.
Excluding the engineered race variable and socioeconomic-status field does not
remove discriminatory proxies or establish fairness. The small river slice has
only six test rows. No causal, fairness or individual-coverage guarantee is claimed.

OpenML's literal license label is **"Public"**, not a specific CC/OSI license.
No stronger rights/commercial-use clearance is inferred. Raw data are fetched
from a fixed URL with SHA-256 verification, not vendored in the site or packages.
Published parity inputs are authored, synthetic scenarios.

## Reproduce And Run

Python 3.11+ and Node 24; `uv.lock` and `frontend/package-lock.json` are committed.

```bash
uv sync --frozen
uv run --frozen python -m boston_housing.train
uv run --frozen pytest -q
uv run --frozen ruff check src tests scripts
npm --prefix frontend ci --ignore-scripts
npm --prefix frontend run build
node frontend/node_modules/@playwright/test/cli.js install chromium --with-deps
node frontend/node_modules/@playwright/test/cli.js test --config frontend/playwright.config.ts
uv run --frozen python scripts/package_site.py
uv run --frozen boston-housing
```

The packaged app runs at `http://127.0.0.1:8897/`. Docker builds a non-root app on
port 8000. Optional production API hosting needs an HTTPS reverse proxy and
operator-configured rate limits/resource budgets. The public demo is static and
performs its own verified model inference locally.

```bash
uv run --frozen python -m boston_housing.loadcheck --users 1000 --concurrency 16
uv run --frozen python -m build
uv run --frozen python scripts/verify_release.py
```

The local load check measures **1,000 total synthetic journeys**, not 1,000
simultaneous humans or browsers. Each journey checks health, real ONNX prediction,
and denial of a legacy artifact: 3,000 observed requests, peak 16 active journeys,
zero failed journeys in the recorded Windows run. P95 1.59 s, P99 2.00 s with
tracing enabled. Python traced allocation peak excludes native ONNX memory.
See [artifacts/load-report.json](artifacts/load-report.json). No public endpoints
or third-party services are load-tested. Results are hardware/profile-specific.

## Release Operations

CI validates Linux Python 3.11/3.13 and Windows 3.13, real browser inference,
dependency audits, local workflows and independent training reproduction.
Pages deploys **only the exact successful owner push SHA** after all verify jobs
pass. PRs cannot obtain publishing permissions through that path. Restore a known
good source revision through a reviewed change and let the same gates redeploy.

Upstream notebooks/output images are historical lineage, not active code or new
evidence. Upstream pickle files are never executed or packaged. Bundled runtime,
parser, font, icon and photo notices ship with the public site. The contextual
Boston photograph by King of Hearts remains CC BY-SA 4.0; code remains GPLv3.


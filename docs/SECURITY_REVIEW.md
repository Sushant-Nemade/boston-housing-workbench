# Security Review And Residual Risks

Reviewed scope: active Python/TypeScript code, source/data/model boundaries,
static release, API input contracts, package contents, and deployment workflow.
This is a scoped engineering review, not a penetration-test certification.

| Finding | Resolution | Verification |
| --- | --- | --- |
| Import-time upstream pickle execution | Replaced the active entry point; no legacy artifact deserialization | AST regression observed RED then GREEN; tampered ONNX fails before session creation |
| Positional JSON inputs silently depend on key order | Canonical named eleven-feature contract | Reordered JSON unit test and actual browser/sklearn parity |
| Unknown/excluded fields silently ignored | Strict unknown-field rejection | Four tests observed RED then GREEN; B, LSTAT, target and prototype-like extras rejected |
| Unbounded API/data/model allocations | Streaming 4 KB request cap; pre-read data/model/report limits; fixed checksum download | Invalid/oversized request tests; modified data/model rejection |
| Historical rows could leak into parity fixtures | Replaced dataset-row probes with deterministic authored inputs | Fixture regeneration and sklearn/ONNX/browser parity |
| CSV/local storage untrusted | Size/row bounds, strict numeric schema, formula-safe CSV export, text-only rendering | Browser CSV rejection/persistence tests; no HTML rendering of stored/imported content |
| Legacy deployment bypassed verification | Removed machine-specific Netlify configuration; exact owner-push SHA Pages gate | Cross-platform verify workflow and deployment condition |

No runtime secrets, accounts, uploads to a server, third-party price API, telemetry,
raw observations, pickle-loading feature, or unrestricted outbound stress target.

Residual limitations:

- ONNX SHA-256 detects mismatch against the shipped report; it is not a signature
  against a maliciously replaced site/report. Trust GitHub/TLS and reviewed source.
- The optional API has no built-in distributed rate limiter; public operators must
  add edge rate limits, HTTPS, request timeouts, worker budgets and monitoring.
- Browser inference uses caller resources. The 1,000-journey test is a bounded
  local ASGI test, not network/CPU saturation, 1,000 browser processes or a capacity SLA.
- Data rights metadata are nonstandard. "Public" is reported literally; no CC or
  commercial clearance is inferred. A legal/data-rights review remains necessary
  before any use beyond historical education.
- Historic discrimination, geographic dependence, top-coded targets and lack of
  representative modern data preclude housing decisions and fairness claims.
- Dependency audits describe known published advisories at execution, not absence
  of vulnerabilities. Source changes and deployment need continued review.
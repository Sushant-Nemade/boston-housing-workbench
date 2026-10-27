import * as ort from "onnxruntime-web/wasm";
import { z } from "zod";

export const names = ["CRIM", "ZN", "INDUS", "CHAS", "NOX", "RM", "AGE", "DIS", "RAD", "TAX", "PTRATIO"] as const;
export type Scenario = Record<typeof names[number], number>;
const metric = z.object({ mae_kusd: z.number().finite(), rmse_kusd: z.number().finite(), r2: z.number().finite() });
const spec = z.object({ label: z.string().max(80), unit: z.string().max(90), min: z.number().finite(), max: z.number().finite(), default: z.number().finite() });
const reportSchema = z.object({
  schema_version: z.literal(1), purpose: z.literal("historical-education-only"), model: z.string().max(80),
  model_sha256: z.string().regex(/^[a-f0-9]{64}$/), feature_names: z.array(z.string()).length(11),
  features: z.record(z.string(), spec),
  evaluation: z.object({ test: metric, median_baseline: metric, interval_coverage: z.number().min(0).max(1),
    mean_interval_width_kusd: z.number().finite(), onnx_max_error_kusd: z.number().finite(), capped_test_rows: z.number().int() }),
  interval: z.object({ radius_kusd: z.number().positive().max(50), nominal_coverage: z.literal(0.9) }),
  splits: z.record(z.string(), z.object({ rows: z.number().int().positive(), sha256: z.string().length(64) })),
  limitations: z.array(z.string().max(800)).max(15),
});
export type Report = z.infer<typeof reportSchema>;
export interface Estimate { estimate_kusd: number; lower_kusd: number; upper_kusd: number; input: Scenario; model_sha256: string; }

async function bounded(name: string, limit: number): Promise<Uint8Array> {
  const response = await fetch(new URL(name, document.baseURI), { signal: AbortSignal.timeout(45000), cache: "no-cache" });
  if (!response.ok || !response.body) throw new Error(`Unable to load ${name}`);
  const reader = response.body.getReader(), chunks: Uint8Array[] = [];
  let length = 0;
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    length += value.length;
    if (length > limit) { await reader.cancel(); throw new Error("Asset size limit exceeded"); }
    chunks.push(value);
  }
  const result = new Uint8Array(length);
  let offset = 0;
  for (const chunk of chunks) { result.set(chunk, offset); offset += chunk.length; }
  return result;
}

export class Engine {
  readonly report: Report;
  private readonly session: ort.InferenceSession;
  private readonly schema: z.ZodType<Scenario>;

  private constructor(report: Report, session: ort.InferenceSession) {
    this.report = report; this.session = session;
    const shape = Object.fromEntries(names.map((name) => {
      const field = report.features[name];
      let validator = z.number().finite().min(field.min).max(field.max);
      if (name === "CHAS" || name === "RAD") validator = validator.int();
      return [name, validator];
    })) as Record<keyof Scenario, z.ZodNumber>;
    this.schema = z.strictObject(shape);
  }

  static async load(): Promise<Engine> {
    const report = reportSchema.parse(JSON.parse(new TextDecoder().decode(await bounded("report.json", 100000))));
    if (report.feature_names.join() !== names.join() || Object.keys(report.features).sort().join() !== [...names].sort().join()) throw new Error("Unsupported feature contract");
    const bytes = await bounded("model.onnx", 5000000);
    const digest = [...new Uint8Array(await crypto.subtle.digest("SHA-256", new Uint8Array(bytes).buffer))].map((value) => value.toString(16).padStart(2, "0")).join("");
    if (digest !== report.model_sha256) throw new Error("Model checksum failed. Inference is disabled.");
    ort.env.wasm.numThreads = 1;
    ort.env.wasm.proxy = false;
    const session = await ort.InferenceSession.create(bytes, { executionProviders: ["wasm"] });
    if (session.inputNames.length !== 1 || session.inputNames[0] !== "features") throw new Error("Invalid model input");
    return new Engine(report, session);
  }

  validate(input: unknown): Scenario { return this.schema.parse(input); }

  async predict(inputs: unknown[]): Promise<Estimate[]> {
    if (!inputs.length || inputs.length > 100) throw new Error("Batch must contain 1-100 scenarios");
    const valid = inputs.map((input) => this.validate(input));
    const tensor = new ort.Tensor("float32", Float32Array.from(valid.flatMap((input) => names.map((name) => input[name]))), [valid.length, 11]);
    const outputs = await this.session.run({ features: tensor });
    const result = outputs[this.session.outputNames[0]];
    try {
      const values = Array.from(result.data as Float32Array);
      if (values.length !== valid.length || values.some((value) => !Number.isFinite(value))) throw new Error("Invalid model output");
      return values.map((value, index) => {
        const estimate = Math.max(5, Math.min(50, value)), radius = this.report.interval.radius_kusd;
        return { estimate_kusd: estimate, lower_kusd: Math.max(5, estimate - radius), upper_kusd: Math.min(50, estimate + radius), input: valid[index], model_sha256: this.report.model_sha256 };
      });
    } finally { tensor.dispose(); result.dispose(); }
  }
}
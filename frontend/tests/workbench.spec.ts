import { test, expect } from "@playwright/test";
import { readFileSync } from "node:fs";

test("smoke: usable historical research workbench", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto("./");
  await expect(page.getByRole("heading", { name: "Boston Housing", exact: true })).toBeVisible({ timeout: 3000 });
  await expect(page.getByRole("button", { name: "Run estimate" })).toBeEnabled({ timeout: 45000 });
  await page.getByRole("button", { name: "Run estimate" }).click();
  await expect(page.locator("#estimate")).toHaveAttribute("data-value", /\d/);
  expect(errors).toEqual([]);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  expect(await page.locator(".panorama").evaluate((image: HTMLImageElement) => image.complete && image.naturalWidth > 100)).toBe(true);
  await page.screenshot({ path: `test-results/boston-${test.info().project.name}.png`, fullPage: true });
});

test("real browser model matches authored sklearn parity probes", async ({ page }) => {
  const probes = JSON.parse(readFileSync(new URL("../../src/boston_housing/artifacts/parity.json", import.meta.url), "utf8"));
  await page.goto("./");
  await expect(page.getByRole("button", { name: "Run estimate" })).toBeEnabled({ timeout: 45000 });
  for (const probe of probes) {
    for (const [name, value] of Object.entries(probe.input)) await page.locator(`#${name}`).fill(String(value));
    await page.getByRole("button", { name: "Run estimate" }).click();
    await expect.poll(async () => Number(await page.locator("#estimate").getAttribute("data-value"))).toBeCloseTo(probe.expected_kusd, 2);
  }
});

test("saved inputs, comparison, CSV validation and evidence tabs", async ({ page }) => {
  await page.goto("./");
  await expect(page.getByRole("button", { name: "Run estimate" })).toBeEnabled({ timeout: 45000 });
  await page.getByRole("button", { name: "Run estimate" }).click();
  await page.getByRole("button", { name: "Save scenario" }).click();
  await page.getByRole("tab", { name: "Scenarios" }).click();
  await expect(page.locator("#saved tbody tr")).toHaveCount(1);
  await page.reload();
  await page.getByRole("tab", { name: "Scenarios" }).click();
  await expect(page.locator("#saved tbody tr")).toHaveCount(1);
  await page.getByRole("tab", { name: "Evidence" }).click();
  await expect(page.locator("#test-mae")).toContainText("2,000");
  await page.getByRole("tab", { name: "Scope & provenance" }).click();
  await expect(page.locator("#scope-panel")).toContainText("NOT individual houses");
  await page.getByRole("tab", { name: "Estimate", exact: true }).click();
  await page.locator("#csv-file").setInputFiles({ name: "bad.csv", mimeType: "text/csv", buffer: Buffer.from("B,LSTAT\n1,2") });
  await expect(page.locator("#csv-status")).toContainText("exactly");
});

test("tampered model fails closed and can retry", async ({ page }) => {
  await page.route("**/model.onnx", (route) => route.fulfill({ status: 200, body: "tampered" }));
  await page.goto("./");
  await expect(page.locator("#status")).toContainText("checksum", { timeout: 45000 });
  await expect(page.getByRole("button", { name: "Run estimate" })).toBeDisabled();
  await page.unroute("**/model.onnx");
  await page.getByRole("button", { name: "Retry model" }).click();
  await expect(page.getByRole("button", { name: "Run estimate" })).toBeEnabled({ timeout: 45000 });
});
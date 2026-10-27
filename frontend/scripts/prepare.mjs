import { readFile, readdir, mkdir, writeFile, copyFile } from "node:fs/promises";
import { existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = fileURLToPath(new URL("../../", import.meta.url));
const frontend = path.join(root, "frontend");
const targets = [path.join(frontend, "public")];
if (existsSync(path.join(frontend, "dist"))) targets.push(path.join(frontend, "dist"));
for (const target of targets) {
  await mkdir(target, { recursive: true });
  for (const name of ["model.onnx", "report.json"])
    await copyFile(path.join(root, "src/boston_housing/artifacts", name), path.join(target, name));
  await copyFile(path.join(root, "LICENSE"), path.join(target, "LICENSE"));
}
const inventory = path.join(frontend, "dist/bundled-packages.json");
if (existsSync(inventory)) {
  const records = [];
  const bundled = JSON.parse(await readFile(inventory, "utf8"));
  for (const name of bundled) {
    if (typeof name !== "string" || !/^(?:@[\w.-]+\/)?[\w.-]+$/.test(name)) throw new Error("Invalid bundle inventory");
    const folder = path.join(frontend, "node_modules", name);
    const metadata = JSON.parse(await readFile(path.join(folder, "package.json"), "utf8"));
    let legal = folder;
    let files = (await readdir(folder)).filter((file) => /^(license|notice|copying|ofl|thirdpartynotices)([.-]|$)/i.test(file));
    if (!files.length && ["onnxruntime-web", "onnxruntime-common"].includes(name) && metadata.version === "1.30.0") {
      legal = path.join(frontend, "legal");
      files = ["onnxruntime-LICENSE.txt", "onnxruntime-ThirdPartyNotices.txt"];
    }
    if (!files.length) throw new Error(`Missing license notice for ${name}`);
    records.push({ name, version: metadata.version, license: metadata.license,
      notices: await Promise.all(files.map(async (file) => ({ file, text: await readFile(path.join(legal, file), "utf8") }))) });
  }
  records.push({ name: "Boston skyline from Longfellow Bridge September 2017 panorama 2.jpg", creator: "King of Hearts", license: "CC BY-SA 4.0", source: "https://commons.wikimedia.org/wiki/File:Boston_skyline_from_Longfellow_Bridge_September_2017_panorama_2.jpg", licenseURL: "https://creativecommons.org/licenses/by-sa/4.0/", modifications: "Wikimedia thumbnail resizing and responsive display cropping; image remains CC BY-SA 4.0." });
  for (const target of targets) await writeFile(path.join(target, "licenses.json"), JSON.stringify(records, null, 2));
  console.log(`Preserved ${records.length} bundled dependency/photo notice records.`);
}
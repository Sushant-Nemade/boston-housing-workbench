import { defineConfig } from "vite";

export default defineConfig({
  base: "./",
  build: { target: "es2022" },
  plugins: [{
    name: "bundle-notice-inventory",
    generateBundle(_options, bundle) {
      const packages = new Set(["@fontsource/ibm-plex-sans"]);
      for (const output of Object.values(bundle)) {
        if (output.type !== "chunk") continue;
        for (const id of Object.keys(output.modules)) {
          const match = id.replaceAll("\\", "/").match(/\/node_modules\/((?:@[^/]+\/)?[^/]+)/);
          if (match) packages.add(match[1]);
        }
      }
      this.emitFile({ type: "asset", fileName: "bundled-packages.json", source: JSON.stringify([...packages].sort()) });
    },
  }],
});
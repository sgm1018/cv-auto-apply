import { build, context } from "esbuild";
import { cp, mkdir } from "node:fs/promises";

const watch = process.argv.includes("--watch");

const common = {
  bundle: true,
  format: "esm",
  target: "chrome120",
  sourcemap: true,
  logLevel: "info",
};

const entries = [
  { entryPoints: ["src/background.ts"], outfile: "dist/background.js" },
  { entryPoints: ["src/content.ts"], outfile: "dist/content.js" },
  { entryPoints: ["src/content-iframe.ts"], outfile: "dist/content-iframe.js" },
];

async function copyStatic() {
  await mkdir("dist/icons", { recursive: true });
  await cp("public/icons", "dist/icons", { recursive: true });
  await cp("popup.html", "dist/popup.html");
  await cp("popup.js", "dist/popup.js");
  await cp("manifest.json", "dist/manifest.json");
}

if (watch) {
  const ctxs = await Promise.all(entries.map((e) => context({ ...common, ...e })));
  await Promise.all(ctxs.map((c) => c.watch()));
  await copyStatic();
  console.log("Watching for changes...");
} else {
  await Promise.all(entries.map((e) => build({ ...common, ...e })));
  await copyStatic();
  console.log("Build complete.");
}

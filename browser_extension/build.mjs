import { build, context } from "esbuild";
import { copyFile, mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const watch = process.argv.includes("--watch");

const outDir = resolve(__dirname, "dist");
await mkdir(outDir, { recursive: true });

const shared = {
  bundle: true,
  minify: !watch,
  sourcemap: watch ? "inline" : false,
  target: ["chrome114"],
  logLevel: "info",
  legalComments: "none",
  define: {
    "process.env.NODE_ENV": watch ? '"development"' : '"production"',
  },
};

const entries = [
  {
    label: "background",
    options: {
      ...shared,
      entryPoints: [resolve(__dirname, "src/background/sw.ts")],
      outfile: resolve(outDir, "background.js"),
      format: "esm",
      platform: "browser",
    },
  },
  {
    label: "sidepanel",
    options: {
      ...shared,
      entryPoints: [resolve(__dirname, "src/sidepanel/index.ts")],
      outfile: resolve(outDir, "sidepanel.js"),
      format: "esm",
      platform: "browser",
    },
  },
  {
    label: "content",
    options: {
      ...shared,
      entryPoints: [resolve(__dirname, "src/content/index.ts")],
      outfile: resolve(outDir, "content.js"),
      // MV3 forbids ES modules in content scripts → IIFE.
      format: "iife",
      platform: "browser",
    },
  },
];

async function copyStatic() {
  // Side panel HTML + CSS
  await copyFile(
    resolve(__dirname, "src/sidepanel/index.html"),
    resolve(outDir, "sidepanel.html"),
  );
  await copyFile(
    resolve(__dirname, "src/sidepanel/styles.css"),
    resolve(outDir, "sidepanel.css"),
  );
}

if (watch) {
  for (const { label, options } of entries) {
    const ctx = await context(options);
    await ctx.watch();
    console.log(`[watch] ${label}`);
  }
  await copyStatic();
  console.log("[watch] static assets copied; waiting for changes…");
} else {
  await Promise.all(entries.map(({ options }) => build(options)));
  await copyStatic();
  console.log("[build] complete → dist/");
}

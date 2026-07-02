import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTypescript from "eslint-config-next/typescript";

export default defineConfig([
  globalIgnores([
    ".next/**",
    "node_modules/**",
    "out/**",
    "build/**",
    "dist/**",
    "next.config.js",
    "postcss.config.js",
    "tailwind.config.js",
  ]),
  ...nextVitals,
  ...nextTypescript,
]);

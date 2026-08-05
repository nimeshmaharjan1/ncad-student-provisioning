/**
 * Copies the repo's docs/ markdown files into frontend/docs/ so the
 * /docs pages can read them at build time from inside the Next.js
 * project (Turbopack requires paths statically scoped to a subfolder).
 *
 * Runs automatically via the predev / prebuild npm hooks, so the copy
 * can never drift: docs/ remains the single source of truth.
 */
import { copyFileSync, mkdirSync, readdirSync } from "node:fs"
import { join, dirname } from "node:path"
import { fileURLToPath } from "node:url"

const scriptDir = dirname(fileURLToPath(import.meta.url))
const srcDir = join(scriptDir, "..", "..", "docs")
const destDir = join(scriptDir, "..", "docs")

mkdirSync(destDir, { recursive: true })

const files = readdirSync(srcDir).filter((file) => file.endsWith(".md"))
for (const file of files) {
  copyFileSync(join(srcDir, file), join(destDir, file))
}

console.log(`[sync-docs] Copied ${files.length} markdown files to frontend/docs/`)

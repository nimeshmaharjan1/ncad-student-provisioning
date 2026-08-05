import { readFileSync } from "node:fs"
import { join } from "node:path"
import { notFound } from "next/navigation"
import Link from "next/link"
import { ArrowLeft, FileText } from "lucide-react"
import { MarkdownContent } from "@/components/markdown-content"
import { DOCS, docBySlug } from "@/lib/docs"

export const dynamicParams = false

export function generateStaticParams() {
  return DOCS.map((doc) => ({ slug: doc.slug }))
}

function docsDir(): string {
  return join(process.cwd(), "docs")
}

function readDoc(file: string): string {
  return readFileSync(join(docsDir(), file), "utf8")
}

function splitTitle(markdown: string): { title: string | null; body: string } {
  const match = markdown.match(/^#\s+(.+?)\s*$/m)
  if (!match) return { title: null, body: markdown }
  const body = markdown
    .slice(0, match.index)
    .concat(markdown.slice((match.index ?? 0) + match[0].length))
    .replace(/^\s*\n/, "")
  return { title: match[1].trim(), body }
}

export default async function DocPage({
  params,
}: {
  params: Promise<{ slug: string }>
}) {
  const { slug } = await params
  const doc = docBySlug(slug)
  if (!doc) notFound()

  const markdown = readDoc(doc.file)
  const { title, body } = splitTitle(markdown)

  return (
    <div className="mx-auto max-w-5xl px-4 py-10">
      <Link
        href="/docs"
        className="inline-flex items-center gap-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground"
      >
        <ArrowLeft className="size-4" />
        All documentation
      </Link>

      <div className="mt-4 mb-8 border-b border-border pb-6">
        <div className="flex flex-wrap items-center gap-3">
          <h1 className="text-2xl font-bold tracking-tight">{title ?? doc.title}</h1>
          <span className="inline-flex items-center gap-1.5 rounded-md border border-border bg-muted/40 px-2 py-1 font-mono text-xs text-muted-foreground">
            <FileText className="size-3.5" />
            {doc.file}
          </span>
        </div>
      </div>

      <MarkdownContent markdown={body} />
    </div>
  )
}

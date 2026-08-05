import Link from "next/link"
import { BookOpen, FileText } from "lucide-react"
import { DOCS } from "@/lib/docs"

export const metadata = {
  title: "Documentation — NCAD Student Provisioning",
}

export default function DocsPage() {
  return (
    <div className="mx-auto max-w-5xl px-4 py-10">
      <div className="flex items-center gap-3">
        <BookOpen className="size-6 text-primary" />
        <h1 className="text-2xl font-bold tracking-tight">Documentation</h1>
      </div>
      <p className="mt-2 max-w-2xl text-sm leading-relaxed text-muted-foreground">
        Project documentation rendered from the repo&apos;s <code className="rounded bg-muted px-1.5 py-0.5 font-mono text-xs">docs/</code>{" "}
        folder. Use the searchable guides on the other pages for day-to-day use; this
        section covers the full manual, the roadmap, testing, and developer material.
      </p>

      <div className="mt-8 grid gap-4 sm:grid-cols-2">
        {DOCS.map((doc) => (
          <Link
            key={doc.slug}
            href={`/docs/${doc.slug}`}
            className="group flex flex-col gap-2 rounded-xl border bg-card p-5 shadow-xs transition-colors hover:bg-muted/40"
          >
            <div className="flex items-center gap-2 text-sm font-semibold">
              <FileText className="size-4 text-primary" />
              {doc.title}
              <span className="ml-auto font-mono text-xs font-normal text-muted-foreground">
                {doc.file}
              </span>
            </div>
            <p className="text-sm leading-relaxed text-muted-foreground">
              {doc.description}
            </p>
            <span className="text-xs font-medium text-primary opacity-0 transition-opacity group-hover:opacity-100">
              Read →
            </span>
          </Link>
        ))}
      </div>
    </div>
  )
}

"use client"

import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import Link from "next/link"
import { cn } from "@/lib/utils"
import { rewriteDocLink } from "@/lib/docs"

const tableCell = (className: string) =>
  function TableCell({
    children,
    ...props
  }: React.ComponentPropsWithoutRef<"td">) {
    return (
      <td className={cn("border-border px-3 py-2 align-top text-sm", className)} {...props}>
        {children}
      </td>
    )
  }

export function MarkdownContent({ markdown }: { markdown: string }) {
  return (
    <div className="max-w-none">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          h2: ({ children }) => (
            <h2 className="mt-10 mb-3 scroll-m-20 text-xl font-semibold tracking-tight first:mt-0">
              {children}
            </h2>
          ),
          h3: ({ children }) => (
            <h3 className="mt-6 mb-2 scroll-m-20 text-lg font-semibold tracking-tight">
              {children}
            </h3>
          ),
          h4: ({ children }) => (
            <h4 className="mt-5 mb-2 scroll-m-20 text-base font-semibold">{children}</h4>
          ),
          p: ({ children }) => <p className="my-3 leading-relaxed">{children}</p>,
          ul: ({ children }) => (
            <ul className="my-3 list-disc space-y-1 pl-6">{children}</ul>
          ),
          ol: ({ children }) => (
            <ol className="my-3 list-decimal space-y-1 pl-6">{children}</ol>
          ),
          li: ({ children }) => <li className="leading-relaxed">{children}</li>,
          strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
          hr: () => <hr className="my-8 border-border" />,
          blockquote: ({ children }) => (
            <blockquote className="my-4 rounded-r-lg border-l-4 border-primary/40 bg-muted/40 px-4 py-2 text-muted-foreground">
              {children}
            </blockquote>
          ),
          a: ({ href, children }) => {
            const rewritten = rewriteDocLink(href ?? "")
            const external = /^https?:\/\//i.test(href ?? "")
            if (external) {
              return (
                <a
                  href={rewritten}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="font-medium text-primary underline underline-offset-4 hover:text-primary/80"
                >
                  {children}
                </a>
              )
            }
            return (
              <Link
                href={rewritten}
                className="font-medium text-primary underline underline-offset-4 hover:text-primary/80"
              >
                {children}
              </Link>
            )
          },
          code: ({ className, children, ...props }) => {
            const isBlock = /language-/.test(className ?? "")
            if (isBlock) {
              return (
                <code className={cn("font-mono text-[0.9em]", className)} {...props}>
                  {children}
                </code>
              )
            }
            return (
              <code
                className="rounded bg-muted px-1.5 py-0.5 font-mono text-[0.85em]"
                {...props}
              >
                {children}
              </code>
            )
          },
          pre: ({ children }) => (
            <pre className="my-4 overflow-x-auto rounded-lg border border-border bg-muted/50 p-4 text-sm">
              {children}
            </pre>
          ),
          table: ({ children }) => (
            <div className="my-4 overflow-x-auto">
              <table className="w-full border-collapse">{children}</table>
            </div>
          ),
          thead: ({ children }) => (
            <thead className="bg-muted/50">{children}</thead>
          ),
          th: ({ children }) => (
            <th className="border border-border px-3 py-2 text-left text-sm font-semibold">
              {children}
            </th>
          ),
          tbody: ({ children }) => <tbody>{children}</tbody>,
          td: tableCell("border"),
        }}
      >
        {markdown}
      </ReactMarkdown>
    </div>
  )
}

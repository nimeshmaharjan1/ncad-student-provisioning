/*
 * Dashboard home — landing page.
 *
 * Three equal tool cards in a responsive grid:
 *   - Provisioning Pipeline (/quercus) — Quercus → LDAP → Canvas → Google
 *   - Library Export (/library) — standalone transformation
 *   - Staff Provisioning (/staff) — Canvas + Library staff rows
 */

"use client"

import { useEffect } from "react"
import Link from "next/link"
import { Database, BookOpen, Users, type LucideIcon } from "lucide-react"
import { usePipeline } from "@/lib/pipeline-context"
import { PrivacyNotice } from "@/components/privacy-notice"

interface ToolCard {
  href: string
  icon: LucideIcon
  title: string
  description: string
  cta: string
}

export default function HomePage() {
  const { step1Done } = usePipeline()

  useEffect(() => {
    document.title = "Home — NCAD Provisioning"
  }, [])

  const tools: ToolCard[] = [
    {
      href: "/quercus",
      icon: Database,
      title: "Provisioning Pipeline",
      description:
        "Upload Quercus CSV files, then generate LDAP, Canvas, and Google Workspace exports.",
      cta: step1Done ? "Resume pipeline" : "Start here",
    },
    {
      href: "/library",
      icon: BookOpen,
      title: "Library Export",
      description:
        "Standalone — upload Quercus Library export files directly. No dependency on the pipeline above.",
      cta: "Open Library",
    },
    {
      href: "/staff",
      icon: Users,
      title: "Staff Provisioning",
      description:
        "Generate Canvas SIS import rows and Library patron rows for staff accounts.",
      cta: "Open Staff",
    },
  ]

  return (
    <div className="mx-auto max-w-5xl px-4 py-10">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold">NCAD Provisioning</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Generate student system exports from Quercus data, plus staff
          provisioning for Canvas and Library accounts.
        </p>
      </div>

      <PrivacyNotice />

      <div className="grid gap-4 sm:grid-cols-2">
        {tools.map((tool) => {
          const Icon = tool.icon
          return (
            <Link
              key={tool.href}
              href={tool.href}
              className="flex flex-col gap-4 rounded-xl border bg-card p-5 transition-colors hover:bg-muted/40"
            >
              <div className="flex size-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
                <Icon className="size-5" />
              </div>
              <div className="flex flex-1 flex-col gap-1">
                <h3 className="font-semibold">{tool.title}</h3>
                <p className="text-sm text-muted-foreground">{tool.description}</p>
              </div>
              <span className="text-xs font-medium text-primary">{tool.cta}</span>
            </Link>
          )
        })}
      </div>
    </div>
  )
}
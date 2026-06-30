"use client"

import { PipelineProvider, usePipeline } from "@/lib/pipeline-context"
import { QuercusStep } from "@/components/quercus-step"
import { LdapStep } from "@/components/ldap-step"
import { CanvasStep } from "@/components/canvas-step"
import { GoogleStep } from "@/components/google-step"
import { LibraryStep } from "@/components/library-step"

function PageContent() {
  const { step1Done, reset } = usePipeline()

  return (
    <div className="mx-auto max-w-4xl px-4 py-8">
      <header className="mb-10">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold">NCAD Student Provisioning</h1>
            <p className="mt-1 text-sm text-muted-foreground">
              Upload Quercus student data, then generate downstream system exports.
            </p>
          </div>
          {step1Done && (
            <button
              onClick={reset}
              className="text-xs text-muted-foreground underline underline-offset-2 hover:text-foreground"
            >
              Start over
            </button>
          )}
        </div>
      </header>

      <section className="mb-12">
        <h2 className="mb-4 text-lg font-medium">Step 1 — Quercus</h2>
        <QuercusStep />
      </section>

      {step1Done && (
        <>
          <section className="mb-12">
            <h2 className="mb-4 text-lg font-medium">Step 2 — LDAP</h2>
            <LdapStep />
          </section>

          <section className="mb-12">
            <h2 className="mb-4 text-lg font-medium">Step 3 — Canvas</h2>
            <CanvasStep />
          </section>

          <section className="mb-12">
            <h2 className="mb-4 text-lg font-medium">Step 4 — Google Workspace</h2>
            <GoogleStep />
          </section>
        </>
      )}

      <hr className="my-12 border-t" />

      <section className="mb-12">
        <h2 className="mb-4 text-lg font-medium">Library Export</h2>
        <p className="mb-4 text-sm text-muted-foreground">
          Upload raw Quercus Library export files to generate a Library upload CSV. Independent from the Quercus pipeline above.
        </p>
        <LibraryStep />
      </section>
    </div>
  )
}

export default function Page() {
  return (
    <PipelineProvider>
      <PageContent />
    </PipelineProvider>
  )
}

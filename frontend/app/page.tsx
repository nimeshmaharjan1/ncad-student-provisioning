"use client"

import { PipelineProvider, usePipeline } from "@/lib/pipeline-context"
import { QuercusStep } from "@/components/quercus-step"
import { LdapStep } from "@/components/ldap-step"
import { GoogleStep } from "@/components/google-step"

function PageContent() {
  const { step1Done, reset } = usePipeline()

  return (
    <div className="mx-auto max-w-4xl px-4 py-8">
      <header className="mb-10">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold">NCAD Student Provisioning</h1>
            <p className="mt-1 text-sm text-muted-foreground">
              Upload Quercus student data, then generate LDAP and Google Workspace exports.
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
            <h2 className="mb-4 text-lg font-medium">Step 3 — Google Workspace</h2>
            <GoogleStep />
          </section>
        </>
      )}
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

/*
 * PipelineContext — shared state for the /quercus provisioning flow.
 *
 * Stores the cleaned Quercus CSV file (returned by POST /quercus/download)
 * so it can be reused by LDAP, Canvas, Google endpoints without forcing
 * the user to re-upload Quercus data for each pipeline.
 *
 * State:
 *   cleanedQuercusFile — the actual File object from /quercus/download,
 *     sent as the "quercus" field in downstream export requests.
 *   auditInfo — preprocessing row counts (raw, filtered, duplicates, etc.)
 *   sampleRows — first 10 cleaned rows for the DataTable preview.
 *   step1Done — derived boolean: true when cleanedQuercusFile is set.
 *
 * Persists across page navigation (mounted in root layout) so the user
 * can switch between /quercus and /library without losing Quercus state.
 *
 * NOT used by LibraryStep — Library is a standalone export that accepts
 * its own file inputs and sends them directly to POST /library/export.
 */

"use client"

import { createContext, useContext, useState, type ReactNode } from "react"
import type { AuditInfo } from "@/lib/api"

interface PipelineState {
  cleanedQuercusFile: File | null
  sampleRows: Record<string, unknown>[] | null
  auditInfo: AuditInfo | null
  step1Done: boolean
  setQuercusData: (data: {
    cleanedQuercusFile: File
    sampleRows: Record<string, unknown>[]
    auditInfo: AuditInfo
  }) => void
  reset: () => void
}

const PipelineContext = createContext<PipelineState | null>(null)

export function PipelineProvider({ children }: { children: ReactNode }) {
  const [cleanedQuercusFile, setCleanedQuercusFile] = useState<File | null>(null)
  const [sampleRows, setSampleRows] = useState<Record<string, unknown>[] | null>(null)
  const [auditInfo, setAuditInfo] = useState<AuditInfo | null>(null)

  const setQuercusData = (data: {
    cleanedQuercusFile: File
    sampleRows: Record<string, unknown>[]
    auditInfo: AuditInfo
  }) => {
    setCleanedQuercusFile(data.cleanedQuercusFile)
    setSampleRows(data.sampleRows)
    setAuditInfo(data.auditInfo)
  }

  const reset = () => {
    setCleanedQuercusFile(null)
    setSampleRows(null)
    setAuditInfo(null)
  }

  return (
    <PipelineContext.Provider
      value={{
        cleanedQuercusFile,
        sampleRows,
        auditInfo,
        step1Done: cleanedQuercusFile !== null,
        setQuercusData,
        reset,
      }}
    >
      {children}
    </PipelineContext.Provider>
  )
}

export function usePipeline(): PipelineState {
  const ctx = useContext(PipelineContext)
  if (!ctx) {
    throw new Error("usePipeline must be used within a PipelineProvider")
  }
  return ctx
}

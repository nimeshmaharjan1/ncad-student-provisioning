"use client"

import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from "react"
import type { AuditInfo } from "@/lib/api"
import { loadPipelineState, savePipelineState, clearPipelineState as clearStorage } from "@/lib/local-storage"

export type StepStatus = "pending" | "done" | "error"

interface PipelineState {
  cleanedQuercusFile: File | null
  sampleRows: Record<string, unknown>[] | null
  auditInfo: AuditInfo | null
  uploadedFileNames: string[]
  step1Done: boolean
  stepStatuses: Record<string, StepStatus>
  setStepStatus: (system: string, status: StepStatus) => void
  setQuercusData: (data: {
    cleanedQuercusFile: File
    sampleRows: Record<string, unknown>[]
    auditInfo: AuditInfo
    uploadedFileNames?: string[]
  }) => void
  reset: () => void
  resetCount: number
}

const PipelineContext = createContext<PipelineState | null>(null)

const STORED_SYSTEMS = ["ldap", "canvas", "google", "athens", "library"]

export function PipelineProvider({ children }: { children: ReactNode }) {
  const [cleanedQuercusFile, setCleanedQuercusFile] = useState<File | null>(null)
  const [sampleRows, setSampleRows] = useState<Record<string, unknown>[] | null>(null)
  const [auditInfo, setAuditInfo] = useState<AuditInfo | null>(null)
  const [uploadedFileNames, setUploadedFileNames] = useState<string[]>([])
  const [stepStatuses, setStepStatuses] = useState<Record<string, StepStatus>>({})
  const [resetCount, setResetCount] = useState(0)

  useEffect(() => {
    const saved = loadPipelineState()
    if (saved.quercusDone && saved.cleanedQuercusFileName) {
      setUploadedFileNames(saved.uploadedFileNames)
    }
  }, [])

  useEffect(() => {
    const saved = loadPipelineState()
    savePipelineState({
      quercusDone: cleanedQuercusFile !== null,
      uploadedFileNames,
      cleanedQuercusFileName: cleanedQuercusFile?.name ?? null,
    })
  }, [cleanedQuercusFile, uploadedFileNames])

  const setStepStatus = useCallback((system: string, status: StepStatus) => {
    setStepStatuses((prev) => ({ ...prev, [system]: status }))
  }, [])

  const setQuercusData = useCallback((data: {
    cleanedQuercusFile: File
    sampleRows: Record<string, unknown>[]
    auditInfo: AuditInfo
    uploadedFileNames?: string[]
  }) => {
    setCleanedQuercusFile(data.cleanedQuercusFile)
    setSampleRows(data.sampleRows)
    setAuditInfo(data.auditInfo)
    if (data.uploadedFileNames) {
      setUploadedFileNames(data.uploadedFileNames)
    }
  }, [])

  const reset = useCallback(() => {
    setCleanedQuercusFile(null)
    setSampleRows(null)
    setAuditInfo(null)
    setUploadedFileNames([])
    setStepStatuses({})
    setResetCount((c) => c + 1)
    clearStorage()
  }, [])

  return (
    <PipelineContext.Provider
      value={{
        cleanedQuercusFile,
        sampleRows,
        auditInfo,
        uploadedFileNames,
        step1Done: cleanedQuercusFile !== null,
        stepStatuses,
        setStepStatus,
        setQuercusData,
        reset,
        resetCount,
      }}
    >
      {children}
    </PipelineContext.Provider>
  )
}

export function usePipeline(): PipelineState {
  const ctx = useContext(PipelineContext)
  if (!ctx) throw new Error("usePipeline must be used within a PipelineProvider")
  return ctx
}

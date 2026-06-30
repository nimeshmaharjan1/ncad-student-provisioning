"use client"

import { useRef, useState } from "react"
import { cn } from "@/lib/utils"

interface FileUploadProps {
  accept?: string
  multiple?: boolean
  label: string
  disabled?: boolean
  onFilesSelected: (files: File[]) => void
}

export function FileUpload({
  accept = ".csv",
  multiple = false,
  label,
  disabled = false,
  onFilesSelected,
}: FileUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [fileNames, setFileNames] = useState<string[]>([])
  const [isDragOver, setIsDragOver] = useState(false)

  const handleFiles = (fileList: FileList | null) => {
    if (!fileList) return
    const files = Array.from(fileList)
    setFileNames(files.map((f) => f.name))
    onFilesSelected(files)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
    if (disabled) return
    handleFiles(e.dataTransfer.files)
  }

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); if (!disabled) setIsDragOver(true) }}
      onDragLeave={() => setIsDragOver(false)}
      onDrop={handleDrop}
      onClick={() => inputRef.current?.click()}
      className={cn(
        "flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed px-6 py-8 text-center transition-colors",
        isDragOver && "border-primary bg-primary/5",
        disabled
          ? "cursor-not-allowed opacity-50"
          : "border-border hover:border-primary/50",
      )}
    >
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        multiple={multiple}
        disabled={disabled}
        className="hidden"
        onChange={(e) => handleFiles(e.target.files)}
      />
      <p className="text-sm font-medium">{label}</p>
      <p className="mt-1 text-xs text-muted-foreground">
        or drag and drop
      </p>
      {fileNames.length > 0 && (
        <ul className="mt-3 space-y-0.5">
          {fileNames.map((name) => (
            <li key={name} className="text-xs text-muted-foreground">
              {name}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

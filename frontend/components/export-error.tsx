"use client"

import type { ExportErrorDetail } from "@/lib/api"
import { cn } from "@/lib/utils"
import {
  AlertTriangle,
  XCircle,
  CheckCircle,
  Info,
  FileWarning,
  ChevronDown,
  ChevronUp,
} from "lucide-react"
import { useState } from "react"

interface ExportErrorProps {
  message: string
  detail?: ExportErrorDetail | null
  className?: string
}

function Badge({
  variant,
  children,
}: {
  variant: "required" | "optional" | "present"
  children: React.ReactNode
}) {
  const styles = {
    required: "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400",
    optional: "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400",
    present: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400",
  }
  return (
    <span className={cn("inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider", styles[variant])}>
      {children}
    </span>
  )
}

function ColumnList({
  columns,
  icon: Icon,
  iconClass,
  badge,
  emptyText,
}: {
  columns: string[]
  icon: React.ComponentType<{ className?: string }>
  iconClass: string
  badge: "required" | "optional" | "present"
  emptyText: string
}) {
  if (columns.length === 0) {
    return (
      <p className="text-xs text-muted-foreground italic">{emptyText}</p>
    )
  }
  return (
    <ul className="space-y-1">
      {columns.map((col) => (
        <li key={col} className="flex items-center gap-2">
          <span className={iconClass}>
            <Icon className="size-3.5" />
          </span>
          <span className="text-sm font-medium">{col}</span>
          <Badge variant={badge}>{badge}</Badge>
        </li>
      ))}
    </ul>
  )
}

export function ExportError({ message, detail, className }: ExportErrorProps) {
  const [showDetails, setShowDetails] = useState(false)
  const isSchemaError = detail?.error_code === "missing_required_columns"
  const isGenericError = !isSchemaError

  return (
    <div
      className={cn(
        "rounded-xl border border-red-200 bg-card shadow-xs dark:border-red-900/50",
        className,
      )}
    >
      {/* Header bar */}
      <div className="flex items-center gap-3 rounded-t-xl bg-red-50 px-4 py-3 dark:bg-red-950/30">
        <div className="flex size-8 shrink-0 items-center justify-center rounded-full bg-red-100 text-red-600 dark:bg-red-900/50 dark:text-red-400">
          <AlertTriangle className="size-4" />
        </div>
        <div className="min-w-0">
          <p className="text-sm font-semibold text-red-800 dark:text-red-300">
            Export Failed
          </p>
          <p className="text-xs text-red-600 dark:text-red-400 truncate">
            {message}
          </p>
        </div>
      </div>

      {/* Schema validation error — rich details */}
      {isSchemaError && detail && (
        <div className="space-y-4 px-4 py-4">
          {/* Missing required */}
          {detail.missing_required && detail.missing_required.length > 0 && (
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <XCircle className="size-4 text-red-500" />
                <h4 className="text-xs font-semibold uppercase tracking-wider text-red-700 dark:text-red-400">
                  Missing Required Columns ({detail.missing_required.length})
                </h4>
              </div>
              <ColumnList
                columns={detail.missing_required}
                icon={XCircle}
                iconClass="text-red-500"
                badge="required"
                emptyText="None missing"
              />
            </div>
          )}

          {/* Missing optional */}
          {detail.missing_optional && detail.missing_optional.length > 0 && (
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <Info className="size-4 text-amber-500" />
                <h4 className="text-xs font-semibold uppercase tracking-wider text-amber-700 dark:text-amber-400">
                  Missing Optional Columns ({detail.missing_optional.length})
                </h4>
              </div>
              <ColumnList
                columns={detail.missing_optional}
                icon={Info}
                iconClass="text-amber-500"
                badge="optional"
                emptyText="None missing"
              />
            </div>
          )}

          {/* Present columns — collapsible */}
          {detail.present_columns && detail.present_columns.length > 0 && (
            <div className="space-y-2">
              <button
                type="button"
                onClick={() => setShowDetails(!showDetails)}
                className="flex items-center gap-2 text-xs text-muted-foreground hover:text-foreground transition-colors"
              >
                {showDetails ? (
                  <ChevronUp className="size-3.5" />
                ) : (
                  <ChevronDown className="size-3.5" />
                )}
                <span className="font-medium">
                  Present Columns ({detail.present_columns.length})
                </span>
              </button>
              {showDetails && (
                <div className="flex flex-wrap gap-1.5">
                  {detail.present_columns.map((col) => (
                    <span
                      key={col}
                      className="inline-flex items-center gap-1 rounded-md bg-emerald-50 px-2 py-1 text-xs text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-400"
                    >
                      <CheckCircle className="size-3" />
                      {col}
                    </span>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Tip */}
          <div className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2.5 dark:border-amber-900/50 dark:bg-amber-950/20">
            <div className="flex items-start gap-2">
              <FileWarning className="mt-0.5 size-4 shrink-0 text-amber-600 dark:text-amber-400" />
              <div>
                <p className="text-xs font-semibold text-amber-800 dark:text-amber-300">
                  How to fix this
                </p>
                <p className="mt-0.5 text-xs text-amber-700 dark:text-amber-400">
                  Open your Quercus export settings and ensure all{" "}
                  <strong>Required</strong> columns are included, then
                  re-export the CSV and upload it again.{" "}
                  {detail.missing_optional && detail.missing_optional.length > 0 && (
                    <>Missing <strong>Optional</strong> columns will be left blank — no action needed.</>
                  )}
                </p>
              </div>
            </div>
          </div>

          {/* Expected columns reference */}
          <div className="flex flex-wrap gap-x-4 gap-y-1 text-[11px] text-muted-foreground">
            {detail.all_required && (
              <span>
                Expected required:{" "}
                <code className="text-xs font-mono">{detail.all_required.join(", ")}</code>
              </span>
            )}
            {detail.all_optional && detail.all_optional.length > 0 && (
              <span>
                Expected optional:{" "}
                <code className="text-xs font-mono">{detail.all_optional.join(", ")}</code>
              </span>
            )}
          </div>
        </div>
      )}

      {/* Generic error — simple fallback */}
      {isGenericError && (
        <div className="px-4 py-3">
          <p className="text-xs text-muted-foreground">
            An unexpected error occurred. Please try again. If the problem
            persists, contact support.
          </p>
        </div>
      )}
    </div>
  )
}

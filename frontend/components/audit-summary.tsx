import type { AuditInfo } from "@/lib/api"

interface AuditSummaryProps {
  audit: AuditInfo
}

export function AuditSummary({ audit }: AuditSummaryProps) {
  const items = [
    { label: "Raw rows", value: audit.raw_row_count },
    { label: "Cleaned rows", value: audit.cleaned_row_count },
    { label: "Filtered by status", value: audit.filtered_out_status_count },
    { label: "External removed", value: audit.external_students_removed_count },
    { label: "Duplicates removed", value: audit.duplicate_rows_detected },
  ]

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-5">
      {items.map((item) => (
        <div
          key={item.label}
          className="rounded-md border bg-card px-3 py-2 text-center"
        >
          <p className="text-lg font-semibold tabular-nums">{item.value}</p>
          <p className="text-xs text-muted-foreground">{item.label}</p>
        </div>
      ))}
    </div>
  )
}

interface DataTableProps {
  rows: Record<string, unknown>[]
}

export function DataTable({ rows }: DataTableProps) {
  if (rows.length === 0) {
    return <p className="text-sm text-muted-foreground">No data to display.</p>
  }

  const columns = Object.keys(rows[0])

  return (
    <div className="overflow-x-auto rounded-md border">
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b bg-muted/50">
            {columns.map((col) => (
              <th key={col} className="px-3 py-2 font-medium text-muted-foreground whitespace-nowrap">
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i} className="border-b last:border-0">
              {columns.map((col) => (
                <td key={col} className="px-3 py-1.5 whitespace-nowrap">
                  {String(row[col] ?? "")}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

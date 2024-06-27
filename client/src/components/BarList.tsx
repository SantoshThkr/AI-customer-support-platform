interface Row {
  label: string
  value: number
}

// Horizontal single-series bars: value sits at the tip in text colour, bar grows from the left baseline.
export default function BarList({ rows, emptyText = 'No data yet' }: { rows: Row[]; emptyText?: string }) {
  const max = Math.max(...rows.map((row) => row.value), 0)
  if (max === 0) {
    return <p className="text-sm text-slate-500">{emptyText}</p>
  }
  return (
    <ul className="space-y-2">
      {rows.map((row) => (
        <li key={row.label} className="grid grid-cols-[7rem_1fr] items-center gap-3 text-sm sm:grid-cols-[9rem_1fr]">
          <span className="truncate text-slate-600" title={row.label}>
            {row.label}
          </span>
          <div className="flex items-center gap-2" title={`${row.label}: ${row.value}`}>
            <div
              className="h-3 rounded-r bg-indigo-500"
              style={{ width: `${(row.value / max) * 85}%`, minWidth: row.value > 0 ? 2 : 0 }}
            />
            <span className="tabular-nums text-slate-700">{row.value}</span>
          </div>
        </li>
      ))}
    </ul>
  )
}

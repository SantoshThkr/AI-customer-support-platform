interface Props {
  page: number
  pages: number
  total: number
  onChange: (page: number) => void
}

export default function Pagination({ page, pages, total, onChange }: Props) {
  if (pages <= 1) {
    return null
  }
  return (
    <nav aria-label="Pagination" className="flex items-center justify-between gap-2 pt-4 text-sm">
      <span className="text-slate-500">
        Page {page} of {pages} · {total} total
      </span>
      <div className="flex gap-2">
        <button type="button" className="btn-secondary" disabled={page <= 1} onClick={() => onChange(page - 1)}>
          Previous
        </button>
        <button type="button" className="btn-secondary" disabled={page >= pages} onClick={() => onChange(page + 1)}>
          Next
        </button>
      </div>
    </nav>
  )
}

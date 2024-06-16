import { useEffect, useState } from 'react'
import { listCategories } from '../services/categories'
import type { Category } from '../types/ticket'

export function useCategories() {
  const [categories, setCategories] = useState<Category[]>([])

  useEffect(() => {
    let cancelled = false
    listCategories()
      .then((data) => {
        if (!cancelled) setCategories(data)
      })
      .catch(() => {
        // Category labels are a nice-to-have; the codes are shown if this fails.
      })
    return () => {
      cancelled = true
    }
  }, [])

  const labelFor = (code: string | null) =>
    code ? (categories.find((category) => category.code === code)?.name ?? code) : 'Uncategorized'

  return { categories, labelFor }
}

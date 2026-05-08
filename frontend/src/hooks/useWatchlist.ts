import { useState, useCallback } from 'react'

const STORAGE_KEY = 'watchlist_ids'

function loadIds(): string[] {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) ?? '[]')
  } catch {
    return []
  }
}

export function useWatchlist(stockId: string | undefined) {
  const [ids, setIds] = useState<string[]>(loadIds)

  const isWatched = stockId != null && ids.includes(stockId)

  const toggle = useCallback(() => {
    if (!stockId) return
    setIds((prev) => {
      const next = prev.includes(stockId)
        ? prev.filter((id) => id !== stockId)
        : [...prev, stockId]
      localStorage.setItem(STORAGE_KEY, JSON.stringify(next))
      return next
    })
  }, [stockId])

  return { isWatched, toggle }
}

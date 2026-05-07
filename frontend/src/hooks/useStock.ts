import { useState, useEffect } from 'react'

export interface StockDetail {
  id: string
  name: string
  price: number
  change: number
  changePercent: number
  volume: number
  market: string
  industry: string
  tags: string[]
  status: string
  high: number | null
  low: number | null
  prevClose: number | null
  open: number | null
}

interface UseStockResult {
  stock: StockDetail | null
  loading: boolean
  error: string | null
}

export function useStock(id: string | undefined): UseStockResult {
  const [stock, setStock] = useState<StockDetail | null>(null)
  const [loading, setLoading] = useState(!!id)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!id) {
      setError('無效的股票代號')
      setLoading(false)
      return
    }

    let isMounted = true
    setLoading(true)
    setError(null)

    fetch(`/api/stocks/${id}`)
      .then((res) => {
        if (res.status === 404) throw new Error('找不到股票')
        if (!res.ok) throw new Error('伺服器錯誤')
        return res.json()
      })
      .then((data: StockDetail) => {
        if (isMounted) {
          setStock(data)
          setLoading(false)
        }
      })
      .catch((err: unknown) => {
        if (isMounted) {
          const message = err instanceof Error ? err.message : '伺服器錯誤'
          setError(message)
          setLoading(false)
        }
      })

    return () => {
      isMounted = false
    }
  }, [id])

  return { stock, loading, error }
}

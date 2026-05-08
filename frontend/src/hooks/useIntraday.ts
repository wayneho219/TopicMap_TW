import { useState, useEffect } from 'react'

export interface IntradayPoint {
  time: string
  price: number
  volume: number
  pct: number
}

export function useIntraday(id: string | undefined) {
  const [data, setData] = useState<IntradayPoint[]>([])
  const [loading, setLoading] = useState(!!id)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!id) { setLoading(false); return }
    let isMounted = true
    setLoading(true)
    setError(null)
    fetch(`/api/stocks/${id}/intraday`)
      .then(res => { if (!res.ok) throw new Error('無法取得分時資料'); return res.json() })
      .then((d: IntradayPoint[]) => { if (isMounted) { setData(d); setLoading(false) } })
      .catch((err: unknown) => {
        if (isMounted) { setError(err instanceof Error ? err.message : '載入失敗'); setLoading(false) }
      })
    return () => { isMounted = false }
  }, [id])

  return { data, loading, error }
}

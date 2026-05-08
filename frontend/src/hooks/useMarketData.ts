import { useState, useEffect } from 'react'

export interface MarketStock {
  id: string
  name: string
  price: number
  change: number
  changePercent: number
  volume?: number
}

type SortKey = 'volume' | 'turnover' | 'price' | 'gain' | 'loss'
type MarketKey = 'listed' | 'otc'
type StockType = 'stock' | 'etf' | 'all'

const sortKeyMap: SortKey[] = ['volume', 'turnover', 'price', 'gain', 'loss']

export function useMarketHot(sortTab: number, toggleTab: number, stockType: StockType = 'stock') {
  const [stocks, setStocks] = useState<MarketStock[]>([])
  const [loading, setLoading] = useState(true)

  const sort: SortKey = sortKeyMap[sortTab] ?? 'volume'
  const market: MarketKey = toggleTab === 1 ? 'otc' : 'listed'

  useEffect(() => {
    setLoading(true)
    fetch(`/api/market/hot?sort=${sort}&market=${market}&stock_type=${stockType}&limit=10`)
      .then((r) => r.json())
      .then((data: MarketStock[]) => { setStocks(data); setLoading(false) })
      .catch(() => setLoading(false))
  }, [sort, market, stockType])

  return { stocks, loading }
}

export function useSearchHot(stockType: StockType = 'stock') {
  const [stocks, setStocks] = useState<MarketStock[]>([])

  useEffect(() => {
    fetch(`/api/market/search_hot?stock_type=${stockType}&limit=6`)
      .then((r) => r.json())
      .then((data: MarketStock[]) => setStocks(data))
      .catch(() => {})
  }, [stockType])

  return stocks
}

export function useStockPrices(ids: string[]) {
  const [stocks, setStocks] = useState<MarketStock[]>([])

  const key = ids.join(',')
  useEffect(() => {
    if (!key) return
    fetch(`/api/stocks/prices?ids=${key}`)
      .then((r) => r.json())
      .then((data: MarketStock[]) => setStocks(data))
      .catch(() => {})
  }, [key])

  return stocks
}

export interface RecurringItem {
  rank: number
  id: string
  name: string
  price: number
  changePercent: number
}

export function useRecurringTW() {
  const [items, setItems] = useState<RecurringItem[]>([])

  useEffect(() => {
    fetch('/api/market/recurring/tw?limit=15')
      .then((r) => r.json())
      .then((data: RecurringItem[]) => setItems(data))
      .catch(() => {})
  }, [])

  return items
}

export interface SectorData {
  name: string
  changePercent: number
  advance: number
  decline: number
  totalVolume: number
}

export function useSectors(
  market: 'listed' | 'otc' = 'listed',
  sort: 'change' | 'volume' = 'change',
  order: 'asc' | 'desc' = 'desc',
) {
  const [sectors, setSectors] = useState<SectorData[]>([])

  useEffect(() => {
    fetch(`/api/market/sectors?market=${market}&sort=${sort}&order=${order}`)
      .then((r) => r.json())
      .then((data: SectorData[]) => setSectors(data))
      .catch(() => {})
  }, [market, sort, order])

  return sectors
}

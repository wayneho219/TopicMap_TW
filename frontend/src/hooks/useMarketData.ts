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


export interface IndustryData {
  name: string
  topicCount: number
  advance: number
  decline: number
  changePercent: number
  totalVolume: number
}

export interface IndustryTopic {
  name: string
  source: 'tpex' | 'nlp'
  changePercent: number
  stockCount: number
}

export function useIndustries(
  sort: 'change' | 'volume' = 'change',
  order: 'asc' | 'desc' = 'desc',
): IndustryData[] {
  const [industries, setIndustries] = useState<IndustryData[]>([])
  useEffect(() => {
    fetch(`/api/market/industries?sort=${sort}&order=${order}`)
      .then((r) => r.json())
      .then((data: IndustryData[]) => setIndustries(data))
      .catch(() => {})
  }, [sort, order])
  return industries
}

export function useIndustryTopics(name: string): { topics: IndustryTopic[]; loaded: boolean } {
  const [topics, setTopics] = useState<IndustryTopic[]>([])
  const [loaded, setLoaded] = useState(false)
  useEffect(() => {
    if (!name) { setTopics([]); setLoaded(false); return }
    setLoaded(false)
    fetch(`/api/market/industry/${encodeURIComponent(name)}/topics`)
      .then((r) => r.json())
      .then((data: IndustryTopic[]) => { setTopics(data); setLoaded(true) })
      .catch(() => { setTopics([]); setLoaded(true) })
  }, [name])
  return { topics, loaded }
}

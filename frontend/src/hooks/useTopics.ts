// frontend/src/hooks/useTopics.ts
import { useState, useEffect } from 'react'

export interface Topic {
  id: number
  name: string
  level: 'medium' | 'fine'
  parentId: number | null
  totalInvested: number
  articleCount: number
  stockCount: number
}

export interface TopicStock {
  id: string
  name: string
  price: number
  change: number
  changePercent: number
  volume: number
  articleCount: number
  topicInvested: number
}

export function useTopics(level: 'medium' | 'fine' = 'medium'): Topic[] {
  const [topics, setTopics] = useState<Topic[]>([])
  useEffect(() => {
    fetch(`/api/topics?level=${level}`)
      .then((r) => r.json())
      .then(setTopics)
      .catch(() => setTopics([]))
  }, [level])
  return topics
}

export function useTopicChildren(name: string): Topic[] {
  const [children, setChildren] = useState<Topic[]>([])
  useEffect(() => {
    if (!name) { setChildren([]); return }
    fetch(`/api/topics/${encodeURIComponent(name)}/children`)
      .then((r) => r.json())
      .then(setChildren)
      .catch(() => setChildren([]))
  }, [name])
  return children
}

export type TopicSortKey = 'change' | 'volume' | 'heat'

export function useTopicStocks(
  name: string,
  level: 'medium' | 'fine',
  sort: TopicSortKey,
  order: 'asc' | 'desc',
): { stocks: TopicStock[]; loading: boolean } {
  const [stocks, setStocks] = useState<TopicStock[]>([])
  const [loading, setLoading] = useState(true)
  useEffect(() => {
    if (!name) return
    setLoading(true)
    fetch(
      `/api/topics/${encodeURIComponent(name)}/stocks?level=${level}&sort=${sort}&order=${order}`,
    )
      .then((r) => r.json())
      .then((data) => { setStocks(data); setLoading(false) })
      .catch(() => { setStocks([]); setLoading(false) })
  }, [name, level, sort, order])
  return { stocks, loading }
}

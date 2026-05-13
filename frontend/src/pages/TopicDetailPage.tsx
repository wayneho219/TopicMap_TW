// frontend/src/pages/TopicDetailPage.tsx
import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { ArrowLeft, ArrowDown, ArrowUp } from 'lucide-react'
import { clsx } from 'clsx'
import { useTopicStocks } from '../hooks/useTopics'
import type { TopicSortKey } from '../hooks/useTopics'

const SORT_TABS = ['投入金額', '漲跌幅', '成交量', '討論熱度'] as const
const SORT_KEYS: TopicSortKey[] = ['invested', 'change', 'volume', 'heat']

function fmtInvested(n: number): string {
  if (n >= 1e8) return `${(n / 1e8).toFixed(1)}億`
  if (n >= 1e4) return `${(n / 1e4).toFixed(1)}萬`
  return Math.round(n).toString()
}

export function TopicDetailPage() {
  const { level, name } = useParams<{ level: string; name: string }>()
  const navigate = useNavigate()
  const [sortIdx, setSortIdx] = useState(0)
  const [order, setOrder] = useState<'asc' | 'desc'>('desc')

  const lv: 'medium' | 'fine' = level === 'fine' ? 'fine' : 'medium'
  const sort = SORT_KEYS[sortIdx]
  const { stocks, loading } = useTopicStocks(name ?? '', lv, sort, order)

  // Calculate total invested from stocks for display
  const totalInvested = stocks.reduce((sum, s) => sum + s.topicInvested, 0)

  function handleSortTab(i: number) {
    if (i === sortIdx) {
      setOrder((o) => (o === 'desc' ? 'asc' : 'desc'))
    } else {
      setSortIdx(i)
      setOrder('desc')
    }
  }

  const OrderIcon = order === 'desc' ? ArrowDown : ArrowUp

  return (
    <div className="flex flex-col bg-[#111111] min-h-screen">
      {/* Header */}
      <div className="flex-shrink-0 bg-[#111111] z-20">
        <div className="flex items-center px-4 pt-14 pb-3 gap-3">
          <button onClick={() => navigate(-1)} className="text-[#888] active:opacity-60">
            <ArrowLeft size={20} />
          </button>
          <div className="flex-1">
            <h1 className="text-white text-lg font-semibold">{name}</h1>
            <span className="text-[#555] text-xs">{lv === 'medium' ? '中層主題' : '細層主題'}</span>
          </div>
        </div>

        {/* Investment info card */}
        {!loading && stocks.length > 0 && (
          <div className="mx-4 mb-3 bg-[#1e1e1e] rounded-[10px] p-3">
            <div className="flex items-center justify-between">
              <div>
                <span className="text-[#888] text-xs block mb-1">總投入金額</span>
                <span className="text-[#3a7bd5] text-lg font-bold">{fmtInvested(totalInvested)}</span>
              </div>
              <div className="text-right">
                <span className="text-[#888] text-xs block mb-1">股票數量</span>
                <span className="text-white text-lg font-bold">{stocks.length}</span>
              </div>
            </div>
          </div>
        )}

        {/* Sort tabs */}
        <div className="flex border-b border-[#2e2e2e] px-4">
          {SORT_TABS.map((t, i) => (
            <button
              key={t}
              onClick={() => handleSortTab(i)}
              className={clsx(
                'flex items-center gap-1 mr-5 pb-2.5 text-sm font-medium relative',
                i === sortIdx ? 'text-[#2dba6a]' : 'text-[#888]',
              )}
            >
              {t}
              {i === sortIdx && <OrderIcon size={12} />}
              {i === sortIdx && (
                <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-[#2dba6a] rounded-full" />
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Stock list */}
      <div className="flex-1 overflow-y-auto px-4 py-3">
        {loading ? (
          <div className="text-[#666] text-sm text-center pt-10">載入中...</div>
        ) : stocks.length === 0 ? (
          <div className="text-[#666] text-sm text-center pt-10">此主題暫無資料</div>
        ) : (
          <div className="space-y-2">
            {stocks.map((s, idx) => {
              const up = s.changePercent >= 0
              return (
                <div
                  key={s.id}
                  className="bg-[#1e1e1e] rounded-[10px] px-4 py-3 cursor-pointer active:opacity-70"
                  onClick={() => navigate(`/stock/${s.id}`)}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <div className="flex items-center gap-2">
                      <span className="text-[#555] text-xs w-5">{idx + 1}</span>
                      <div>
                        <span className="text-white text-sm font-medium">{s.name}</span>
                        <span className="text-[#555] text-xs ml-1.5">{s.id}</span>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-white text-sm font-medium">{s.price.toFixed(2)}</div>
                      <div className={clsx('text-xs', up ? 'text-[#e84040]' : 'text-[#2dba6a]')}>
                        {up ? '+' : ''}{s.changePercent.toFixed(2)}%
                      </div>
                    </div>
                  </div>
                  <div className="flex gap-2 text-xs text-[#555]">
                    <span>投入 {fmtInvested(s.topicInvested)}</span>
                    <span>·</span>
                    <span>討論 {s.articleCount} 篇</span>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}

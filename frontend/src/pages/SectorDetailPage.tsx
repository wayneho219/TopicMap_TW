import { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { ArrowLeft, ArrowDown, ArrowUp } from 'lucide-react'
import { clsx } from 'clsx'
import { RankListItem } from '../components/RankListItem'

interface Stock {
  id: string
  name: string
  price: number
  change: number
  changePercent: number
  volume: number
}

const sortTabs = ['漲跌幅', '成交量'] as const
type SortKey = 'change' | 'volume'
type Order = 'asc' | 'desc'

interface Props {
  kind: 'sector' | 'chain'
}

export function SectorDetailPage({ kind }: Props) {
  const { name } = useParams<{ name: string }>()
  const navigate = useNavigate()
  const [sortIdx, setSortIdx] = useState(0)
  const [order, setOrder] = useState<Order>('desc')
  const [stocks, setStocks] = useState<Stock[]>([])
  const [loading, setLoading] = useState(true)

  const sort: SortKey = sortIdx === 0 ? 'change' : 'volume'
  const endpoint = kind === 'sector'
    ? `/api/market/sector/${encodeURIComponent(name ?? '')}/stocks?sort=${sort}&order=${order}`
    : `/api/market/chain/${encodeURIComponent(name ?? '')}/stocks?sort=${sort}&order=${order}`

  useEffect(() => {
    if (!name) return
    setLoading(true)
    fetch(endpoint)
      .then((r) => r.json())
      .then((data: Stock[]) => { setStocks(data); setLoading(false) })
      .catch(() => setLoading(false))
  }, [endpoint, name])

  function handleSortTab(i: number) {
    if (i === sortIdx) {
      setOrder((o) => o === 'desc' ? 'asc' : 'desc')
    } else {
      setSortIdx(i)
      setOrder('desc')
    }
  }

  const OrderIcon = order === 'desc' ? ArrowDown : ArrowUp

  return (
    <div className="flex flex-col bg-[#111111] h-screen">
      {/* Header */}
      <div className="flex-shrink-0 bg-[#111111] z-20">
        <div className="flex items-center gap-3 px-4 pt-14 pb-3">
          <button onClick={() => navigate(-1)} className="text-white active:opacity-60">
            <ArrowLeft size={20} />
          </button>
          <h1 className="text-white text-lg font-semibold flex-1">{name}</h1>
        </div>

        {/* Sort Tabs */}
        <div className="flex border-b border-[#2e2e2e] px-4">
          {sortTabs.map((t, i) => (
            <button
              key={t}
              onClick={() => handleSortTab(i)}
              className={clsx(
                'flex items-center gap-1 mr-6 pb-2.5 text-sm font-medium relative',
                i === sortIdx ? 'text-[#2dba6a]' : 'text-[#888]'
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

      {/* List */}
      <div className="flex-1 overflow-y-auto pb-16 px-3 pt-3">
        {loading ? (
          <div className="flex items-center justify-center h-40 text-[#666] text-sm">載入中...</div>
        ) : stocks.length === 0 ? (
          <div className="flex items-center justify-center h-40 text-[#666] text-sm">暫無資料</div>
        ) : (
          <div className="flex flex-col gap-2">
            {stocks.map((s, idx) => (
              <RankListItem
                key={s.id}
                stock={s}
                rank={idx + 1}
                onClick={() => navigate(`/stock/${s.id}`)}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

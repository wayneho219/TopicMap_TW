import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ChevronRight, ArrowDown, ArrowUp } from 'lucide-react'
import { clsx } from 'clsx'
import { useIndustries, useIndustryTopics, useIndustryStocks } from '../hooks/useMarketData'
import type { IndustryData, IndustryTopic, IndustrySortKey, IndustrySortOrder, MarketStock } from '../hooks/useMarketData'

const sortTabs = ['投入金額', '漲跌幅', '成交量'] as const

function StockRow({ stock }: { stock: MarketStock }) {
  const navigate = useNavigate()
  const up = stock.changePercent >= 0

  return (
    <div
      className="pl-6 pr-4 py-2.5 border-t border-[#252525] cursor-pointer active:opacity-70 flex items-center justify-between"
      onClick={() => navigate(`/stock/${stock.id}`)}
    >
      <div className="flex flex-col gap-0.5">
        <span className="text-[#bbb] text-sm">{stock.name}</span>
        <span className="text-[10px] text-[#666]">{stock.id}</span>
      </div>
      <div className="flex items-center gap-3">
        <div className="text-right">
          <div className="text-xs text-[#aaa]">${stock.price}</div>
          <div className={clsx('text-xs font-medium', up ? 'text-[#e84040]' : 'text-[#2dba6a]')}>
            {up ? '+' : ''}{stock.changePercent.toFixed(2)}%
          </div>
        </div>
      </div>
    </div>
  )
}

function TopicRow({ topic }: { topic: IndustryTopic }) {
  const navigate = useNavigate()
  const up = topic.changePercent >= 0

  function handleClick() {
    if (topic.source === 'tpex') {
      navigate(`/chain/${encodeURIComponent(topic.name)}`)
    } else {
      navigate(`/topic/fine/${encodeURIComponent(topic.name)}`)
    }
  }

  return (
    <div
      className="pl-6 pr-4 py-2.5 border-t border-[#252525] cursor-pointer active:opacity-70 flex items-center justify-between"
      onClick={handleClick}
    >
      <div className="flex items-center gap-2">
        <span className="text-[#bbb] text-sm">{topic.name}</span>
        {topic.source === 'nlp' && (
          <span className="text-[10px] text-[#3a7bd5] bg-[#1a2a40] px-1 py-0.5 rounded leading-none">
            ✦
          </span>
        )}
      </div>
      <div className="flex items-center gap-3">
        <span className="text-xs text-[#666]">{topic.stockCount}支</span>
        <span className={clsx('text-sm font-medium', up ? 'text-[#e84040]' : 'text-[#2dba6a]')}>
          {up ? '+' : ''}{topic.changePercent.toFixed(2)}%
        </span>
      </div>
    </div>
  )
}

function IndustryCard({
  industry,
  maxChange,
  expanded,
  expandedView,
  sortIdx,
  onToggle,
  onViewChange,
}: {
  industry: IndustryData
  maxChange: number
  expanded: boolean
  expandedView: 'stocks' | 'topics'
  sortIdx: number
  onToggle: () => void
  onViewChange: (view: 'stocks' | 'topics') => void
}) {
  const { topics, loaded: topicsLoaded } = useIndustryTopics(expanded && expandedView === 'topics' ? industry.name : '')
  const { stocks, loaded: stocksLoaded } = useIndustryStocks(expanded && expandedView === 'stocks' ? industry.name : '')
  const up = industry.changePercent >= 0
  const barW = sortIdx === 0
    ? (maxChange > 0 ? Math.round((industry.totalInvested / maxChange) * 100) : 0)
    : sortIdx === 1
      ? (maxChange > 0 ? Math.round((Math.abs(industry.changePercent) / maxChange) * 100) : 0)
      : 0

  const loaded = expandedView === 'topics' ? topicsLoaded : stocksLoaded
  const isEmpty = expandedView === 'topics' ? topics.length === 0 : stocks.length === 0

  return (
    <div className="bg-[#1e1e1e] rounded-[10px] overflow-hidden">
      <div className="px-4 py-3 cursor-pointer active:opacity-70" onClick={onToggle}>
        <div className="flex items-center justify-between mb-2">
          <span className="text-white text-sm font-medium">{industry.name}</span>
          <div className="flex items-center gap-2">
            {sortIdx === 0 ? (
              <span className="text-base font-bold text-[#3a7bd5]">
                NT${(industry.totalInvested / 1e8).toFixed(2)}億
              </span>
            ) : sortIdx === 1 ? (
              <span className={clsx('text-base font-bold', up ? 'text-[#e84040]' : 'text-[#2dba6a]')}>
                {up ? '+' : ''}{industry.changePercent.toFixed(2)}%
              </span>
            ) : (
              <span className="text-base font-bold text-[#888]">
                {(industry.totalVolume / 1e6).toFixed(0)}M
              </span>
            )}
            <ChevronRight
              size={16}
              className={clsx(
                'text-[#2dba6a] transition-transform duration-200',
                expanded && 'rotate-90',
              )}
            />
          </div>
        </div>
        <div className="h-1.5 bg-[#2e2e2e] rounded-full overflow-hidden mb-2">
          <div
            className={clsx('h-full rounded-full', sortIdx === 0 ? 'bg-[#3a7bd5]' : up ? 'bg-[#e84040]' : 'bg-[#2dba6a]')}
            style={{ width: `${barW}%` }}
          />
        </div>
        <div className="flex gap-3 text-xs text-[#666]">
          <span>{industry.topicCount}個主題</span>
          <span className="text-[#e84040]">漲 {industry.advance}</span>
          <span className="text-[#2dba6a]">跌 {industry.decline}</span>
        </div>
      </div>

      {expanded && (
        <>
          <div className="flex border-t border-[#252525]">
            <button
              className={clsx(
                'flex-1 px-4 py-2 text-xs font-medium',
                expandedView === 'stocks'
                  ? 'border-b-2 border-[#2dba6a] text-[#2dba6a]'
                  : 'text-[#666] border-b border-[#252525]'
              )}
              onClick={(e) => { e.stopPropagation(); onViewChange('stocks') }}
            >
              個股
            </button>
            <button
              className={clsx(
                'flex-1 px-4 py-2 text-xs font-medium',
                expandedView === 'topics'
                  ? 'border-b-2 border-[#2dba6a] text-[#2dba6a]'
                  : 'text-[#666] border-b border-[#252525]'
              )}
              onClick={(e) => { e.stopPropagation(); onViewChange('topics') }}
            >
              主題
            </button>
          </div>

          {!loaded && (
            <div className="pl-6 py-3 text-[#555] text-xs border-t border-[#252525]">載入中...</div>
          )}
          {loaded && isEmpty && (
            <div className="pl-6 py-3 text-[#555] text-xs border-t border-[#252525]">暫無資料</div>
          )}
          {loaded && !isEmpty && expandedView === 'stocks' && (
            <div>
              {stocks.map((s) => (
                <StockRow key={s.id} stock={s} />
              ))}
            </div>
          )}
          {loaded && !isEmpty && expandedView === 'topics' && (
            <div>
              {topics.map((t) => (
                <TopicRow key={`${t.source}-${t.name}`} topic={t} />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  )
}

type ExpandedState = { name: string; view: 'stocks' | 'topics' } | null

export function IndustryTab() {
  const [sortIdx, setSortIdx] = useState(0)
  const [order, setOrder] = useState<IndustrySortOrder>('desc')
  const [expanded, setExpanded] = useState<ExpandedState>(null)

  const sort: IndustrySortKey = sortIdx === 0 ? 'invested' : sortIdx === 1 ? 'change' : 'volume'

  function handleSortTab(i: number) {
    setExpanded(null)
    if (i === sortIdx) {
      setOrder((o) => (o === 'desc' ? 'asc' : 'desc'))
    } else {
      setSortIdx(i)
      setOrder('desc')
    }
  }

  function handleToggleExpand(name: string) {
    if (expanded?.name === name) {
      setExpanded(null)
    } else {
      setExpanded({ name, view: 'stocks' })
    }
  }

  function handleSwitchView(view: 'stocks' | 'topics') {
    if (expanded) {
      setExpanded({ ...expanded, view })
    }
  }

  const industries = useIndustries(sort, order)
  const OrderIcon = order === 'desc' ? ArrowDown : ArrowUp
  const maxChange = industries.length > 0
    ? sortIdx === 0
      ? Math.max(...industries.map((i) => i.totalInvested))
      : Math.max(...industries.map((i) => Math.abs(i.changePercent)))
    : 1

  if (industries.length === 0) {
    return <div className="text-[#666] text-sm text-center pt-10">載入中...</div>
  }

  return (
    <div>
      {/* Sort tabs */}
      <div className="flex border-b border-[#2e2e2e] mb-3">
        {sortTabs.map((t, i) => (
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

      <div className="space-y-2">
        {industries.map((industry) => (
          <IndustryCard
            key={industry.name}
            industry={industry}
            maxChange={maxChange}
            expanded={expanded?.name === industry.name}
            expandedView={expanded?.view || 'stocks'}
            sortIdx={sortIdx}
            onToggle={() => handleToggleExpand(industry.name)}
            onViewChange={handleSwitchView}
          />
        ))}
      </div>
    </div>
  )
}

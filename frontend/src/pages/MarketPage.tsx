import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, ArrowUp, ArrowDown } from 'lucide-react'
import { clsx } from 'clsx'
import { IndexCard } from '../components/IndexCard'
import { HotSearchCard } from '../components/HotSearchCard'
import { RankListItem } from '../components/RankListItem'
import {
  mockIndices, mockHotSearch, mockHotMarket,
  mockIndicesUS, mockHotSearchUS, mockHotMarketUS,
  mockIndicesETFTW, mockHotSearchETFTW, mockHotMarketETFTW,
  mockIndicesETFUS, mockHotSearchETFUS, mockHotMarketETFUS,
} from '../data/mock'
import { useMarketHot, useSearchHot, useSectors } from '../hooks/useMarketData'

const marketSubTabs = ['台股', '美股', '台股ETF', '美股ETF', '類股']
const hotSortTabs = ['成交量', '成交值', '成交價', '漲幅', '跌幅']
const marketToggle = ['上市', '上櫃']

export function MarketPage() {
  const [subTab, setSubTab] = useState(0)
  const [sortTab, setSortTab] = useState(0)
  const [toggle, setToggle] = useState(0)
  const navigate = useNavigate()

  const isTW = subTab === 0 || subTab === 2
  const isTWStock = subTab === 0

  const liveHot    = useMarketHot(sortTab, toggle)
  const liveSearch = useSearchHot()

  const indices   = subTab === 0 ? mockIndices      : subTab === 1 ? mockIndicesUS
                  : subTab === 2 ? mockIndicesETFTW  : mockIndicesETFUS
  const hotSearch = isTWStock ? liveSearch  : subTab === 1 ? mockHotSearchUS
                  : subTab === 2 ? mockHotSearchETFTW : mockHotSearchETFUS
  const hotMarket = isTWStock ? liveHot.stocks : subTab === 1 ? mockHotMarketUS
                  : subTab === 2 ? mockHotMarketETFTW : mockHotMarketETFUS

  return (
    <div className="flex flex-col bg-[#111111] h-screen">
      {/* ── 釘住頂部 ── */}
      <div className="flex-shrink-0 bg-[#111111] z-20">
        {/* Top Bar */}
        <div className="flex items-center justify-between px-4 pt-14 pb-3">
          <h1 className="text-white text-lg font-semibold">行情</h1>
          <button onClick={() => navigate('/search')} className="text-[#888] active:opacity-60">
            <Search size={20} />
          </button>
        </div>

        {/* Main Tabs: 自選 / 行情 */}
        <div className="flex px-4 border-b border-[#2e2e2e]">
          {['自選', '行情'].map((t, i) => (
            <button
              key={t}
              onClick={() => i === 0 && navigate('/watchlist')}
              className={clsx(
                'mr-6 pb-2 text-sm font-medium relative',
                i === 1 ? 'text-white' : 'text-[#888]'
              )}
            >
              {t}
              {i === 1 && (
                <span className="absolute bottom-0 left-1/2 -translate-x-1/2 w-1.5 h-1.5 rounded-full bg-[#2dba6a]" />
              )}
            </button>
          ))}
        </div>

        {/* Sub Tabs */}
        <div className="flex overflow-x-auto scrollbar-none border-b border-[#2e2e2e] px-4">
          {marketSubTabs.map((t, i) => (
            <button
              key={t}
              onClick={() => { setSubTab(i); setSortTab(0); setToggle(0) }}
              className={clsx(
                'flex-shrink-0 mr-5 py-2.5 text-sm font-medium relative whitespace-nowrap',
                i === subTab ? 'text-[#2dba6a]' : 'text-[#888]'
              )}
            >
              {t}
              {i === subTab && (
                <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-[#2dba6a] rounded-full" />
              )}
            </button>
          ))}
        </div>
      </div>

      {/* ── 捲動內容區 ── */}
      <div className="flex-1 overflow-y-auto pb-16">

        {/* 類股 tab — 獨立版面 */}
        {subTab === 4 ? (
          <SectorTab />
        ) : (
          <div className="px-3 pt-3 space-y-4">
            {/* Index Cards */}
            <div className="flex gap-2">
              {indices.map((idx) => (
                <IndexCard key={idx.name} item={idx} />
              ))}
            </div>

            {/* 今日熱搜 */}
            <section>
              <div className="flex items-center justify-between mb-2 px-1">
                <span className="text-white text-sm font-medium">今日熱搜</span>
                <button className="text-[#2dba6a] text-xs">看更多 &gt;</button>
              </div>
              <div className="flex gap-2 overflow-x-auto scrollbar-none pb-1">
                {hotSearch.map((s) => (
                  <HotSearchCard
                    key={s.id}
                    stock={s}
                    onClick={() => navigate(`/stock/${s.id}`)}
                  />
                ))}
              </div>
            </section>

            {/* 盤中熱門 */}
            <section>
              <div className="flex items-center justify-between mb-2 px-1">
                <span className="text-white text-sm font-medium">盤中熱門</span>
                <button className="text-[#2dba6a] text-xs">看更多 &gt;</button>
              </div>

              <div className="flex overflow-x-auto scrollbar-none mb-3 gap-1">
                {hotSortTabs.map((t, i) => (
                  <button
                    key={t}
                    onClick={() => setSortTab(i)}
                    className={clsx(
                      'flex-shrink-0 px-3 py-1 text-xs rounded-full border',
                      i === sortTab
                        ? 'border-[#2dba6a] text-[#2dba6a] bg-[#0f2e1c]'
                        : 'border-[#333] text-[#888]'
                    )}
                  >
                    {t}
                  </button>
                ))}
              </div>

              {isTW && (
                <div className="flex gap-2 mb-3">
                  {marketToggle.map((t, i) => (
                    <button
                      key={t}
                      onClick={() => setToggle(i)}
                      className={clsx(
                        'px-4 py-1 text-xs rounded-full',
                        i === toggle
                          ? 'bg-[#2dba6a] text-white font-medium'
                          : 'bg-[#2a2a2a] text-[#888]'
                      )}
                    >
                      {t}
                    </button>
                  ))}
                </div>
              )}

              <div className="flex flex-col gap-2">
                {hotMarket.map((s, idx) => (
                  <RankListItem
                    key={s.id}
                    stock={s}
                    rank={idx + 1}
                    onClick={() => navigate(`/stock/${s.id}`)}
                  />
                ))}
              </div>
            </section>
          </div>
        )}
      </div>
    </div>
  )
}

const sectorSortTabs = ['漲跌幅', '成交量'] as const
type SectorSort = 'change' | 'volume'
type SectorOrder = 'asc' | 'desc'

/* ── 類股 Tab ── */
function SectorTab() {
  const navigate = useNavigate()
  const [sortIdx, setSortIdx] = useState(0)
  const [order, setOrder] = useState<SectorOrder>('desc')

  const sort: SectorSort = sortIdx === 0 ? 'change' : 'volume'
  const sectors = useSectors('listed', sort, order)
  const maxVal = Math.max(...sectors.map((s) =>
    sort === 'change' ? Math.abs(s.changePercent) : s.totalVolume
  ), 1)

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
    <div className="px-3 pt-3 pb-6">
      {/* Sort tabs */}
      <div className="flex border-b border-[#2e2e2e] mb-3">
        {sectorSortTabs.map((t, i) => (
          <button
            key={t}
            onClick={() => handleSortTab(i)}
            className={clsx(
              'flex items-center gap-1 mr-5 pb-2.5 text-sm font-medium relative',
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

      <div className="space-y-2">
        {sectors.map((sector) => {
          const up   = sector.changePercent >= 0
          const barW = Math.round(
            (sort === 'change' ? Math.abs(sector.changePercent) : sector.totalVolume) / maxVal * 100
          )
          const rightVal = sort === 'change'
            ? `${up ? '+' : ''}${sector.changePercent.toFixed(2)}%`
            : `${(sector.totalVolume / 1e8).toFixed(1)}億`

          return (
            <div
              key={sector.name}
              className="bg-[#1e1e1e] rounded-[10px] px-4 py-3 active:opacity-70 cursor-pointer"
              onClick={() => navigate(`/sector/${encodeURIComponent(sector.name)}`)}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-white text-sm font-medium">{sector.name}</span>
                <span className={clsx(
                  'text-base font-bold',
                  sort === 'change' ? (up ? 'text-[#e84040]' : 'text-[#2dba6a]') : 'text-[#aaa]'
                )}>
                  {rightVal}
                </span>
              </div>
              <div className="h-1.5 bg-[#2e2e2e] rounded-full overflow-hidden mb-2">
                <div
                  className={clsx('h-full rounded-full',
                    sort === 'change' ? (up ? 'bg-[#e84040]' : 'bg-[#2dba6a]') : 'bg-[#3a7bd5]'
                  )}
                  style={{ width: `${barW}%` }}
                />
              </div>
              <div className="flex gap-3 text-xs text-[#666]">
                <span className="text-[#e84040]">漲 {sector.advance}</span>
                <span className="text-[#2dba6a]">跌 {sector.decline}</span>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

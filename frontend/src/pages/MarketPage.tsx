import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search } from 'lucide-react'
import { clsx } from 'clsx'
import { IndexCard } from '../components/IndexCard'
import { HotSearchCard } from '../components/HotSearchCard'
import { RankListItem } from '../components/RankListItem'
import {
  mockIndices, mockHotSearch, mockHotMarket,
  mockIndicesUS, mockHotSearchUS, mockHotMarketUS,
  mockIndicesETFTW, mockHotSearchETFTW, mockHotMarketETFTW,
  mockIndicesETFUS, mockHotSearchETFUS, mockHotMarketETFUS,
  mockSectors,
} from '../data/mock'

const marketSubTabs = ['台股', '美股', '台股ETF', '美股ETF', '類股']
const hotSortTabs = ['成交量', '成交值', '成交價', '漲幅', '跌幅']
const marketToggle = ['上市', '上櫃']

export function MarketPage() {
  const [subTab, setSubTab] = useState(0)
  const [sortTab, setSortTab] = useState(0)
  const [toggle, setToggle] = useState(0)
  const navigate = useNavigate()

  const isTW = subTab === 0 || subTab === 2

  const indices   = subTab === 0 ? mockIndices      : subTab === 1 ? mockIndicesUS
                  : subTab === 2 ? mockIndicesETFTW  : mockIndicesETFUS
  const hotSearch = subTab === 0 ? mockHotSearch     : subTab === 1 ? mockHotSearchUS
                  : subTab === 2 ? mockHotSearchETFTW : mockHotSearchETFUS
  const hotMarket = subTab === 0 ? mockHotMarket     : subTab === 1 ? mockHotMarketUS
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

/* ── 類股 Tab ── */
function SectorTab() {
  const sorted = [...mockSectors].sort((a, b) => b.changePercent - a.changePercent)
  const maxAbs = Math.max(...sorted.map((s) => Math.abs(s.changePercent)))

  return (
    <div className="px-3 pt-3 pb-6 space-y-2">
      <div className="flex items-center justify-between mb-3 px-1">
        <span className="text-white text-sm font-medium">產業類股漲跌</span>
        <span className="text-[#666] text-xs">依漲跌幅排序</span>
      </div>
      {sorted.map((sector) => {
        const up  = sector.changePercent >= 0
        const barW = Math.round(Math.abs(sector.changePercent) / maxAbs * 100)
        return (
          <div key={sector.name} className="bg-[#1e1e1e] rounded-[10px] px-4 py-3">
            <div className="flex items-center justify-between mb-2">
              <span className="text-white text-sm font-medium">{sector.name}</span>
              <span className={clsx('text-base font-bold', up ? 'text-[#e84040]' : 'text-[#2dba6a]')}>
                {up ? '+' : ''}{sector.changePercent.toFixed(2)}%
              </span>
            </div>
            {/* 漲跌幅條 */}
            <div className="h-1.5 bg-[#2e2e2e] rounded-full overflow-hidden mb-2">
              <div
                className={clsx('h-full rounded-full', up ? 'bg-[#e84040]' : 'bg-[#2dba6a]')}
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
  )
}

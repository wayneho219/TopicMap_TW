import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, Trash2, Plus, ChevronRight } from 'lucide-react'
import { clsx } from 'clsx'
import { mockRecentSearches, mockTop30 } from '../data/mock'

const recentSearchIdMap: Record<string, string> = {
  '玉山金': '2884',
  '華通': '2313',
  '昇達科': '3536',
  '光寶科': '2301',
  'First Majestic Silver Corp.': 'AG',
  'Fiserv Inc': 'FI',
}

const mainTabs = ['選股', '消息', '自選']
const hotTabs = ['熱門排行', 'AI幫你搜', '再買一次']
const timePills = ['一小時', '今日熱門', '最多評論']

export function StockSearchPage() {
  const [mainTab, setMainTab] = useState(0)
  const [hotTab, setHotTab] = useState(0)
  const [timePill, setTimePill] = useState(0)
  const [query, setQuery] = useState('')
  const navigate = useNavigate()

  return (
    <div className="flex flex-col bg-white h-screen">

      {/* ── 釘住頂部 ── */}
      <div className="flex-shrink-0 bg-white z-20">
        {/* Search Bar */}
        <div className="px-4 pt-14 pb-2">
          <div className="flex items-center bg-[#f2f2f2] rounded-full px-4 py-2.5 gap-2">
            <Search size={16} className="text-[#aaa] flex-shrink-0" />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="搜尋股票、期貨、概念、指標關鍵字"
              className="flex-1 bg-transparent text-[#1a1a1a] text-sm outline-none placeholder:text-[#aaa]"
            />
          </div>
        </div>

        {/* Main Tabs */}
        <div className="flex px-4 border-b border-[#eee]">
          {mainTabs.map((t, i) => (
            <button
              key={t}
              onClick={() => setMainTab(i)}
              className={clsx(
                'mr-6 py-2.5 text-sm font-medium relative',
                i === mainTab ? 'text-[#1a1a1a]' : 'text-[#aaa]'
              )}
            >
              {t}
              {i === mainTab && (
                <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-[#ff9500] rounded-full" />
              )}
            </button>
          ))}
        </div>
      </div>

      {/* ── 捲動內容區 ── */}
      <div className="flex-1 overflow-y-auto pb-16">
        {/* Recent Searches */}
        <div className="px-4 pt-4">
          <div className="flex items-center justify-between mb-3">
            <span className="text-[#1a1a1a] text-sm font-medium">最近的搜尋內容</span>
            <button className="text-[#2dba6a] active:opacity-60">
              <Trash2 size={18} />
            </button>
          </div>
          <div className="flex flex-wrap gap-2">
            {mockRecentSearches.map((kw) => (
              <button
                key={kw}
                onClick={() => navigate(`/stock/${recentSearchIdMap[kw] ?? kw}`)}
                className="px-3 py-1.5 rounded-full border border-[#ddd] text-[#333] text-sm bg-white active:bg-[#f5f5f5]"
              >
                {kw}
              </button>
            ))}
          </div>
        </div>

        {/* Hot Section */}
        <div className="px-4 mt-5">
          {/* Hot Tabs */}
          <div className="flex border-b border-[#eee] mb-3">
            {hotTabs.map((t, i) => (
              <button
                key={t}
                onClick={() => setHotTab(i)}
                className={clsx(
                  'mr-6 pb-2 text-sm font-medium relative',
                  i === hotTab ? 'text-[#1a1a1a]' : 'text-[#aaa]'
                )}
              >
                {t}
                {i === hotTab && (
                  <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-[#ff9500] rounded-full" />
                )}
              </button>
            ))}
          </div>

          {/* 標的類型 */}
          <div className="text-[#888] text-xs mb-2">標的類型</div>
          <div className="flex gap-2 mb-4">
            {timePills.map((t, i) => (
              <button
                key={t}
                onClick={() => setTimePill(i)}
                className={clsx(
                  'px-3 py-1.5 rounded-[6px] text-sm border relative',
                  i === timePill
                    ? 'border-[#ff9500] text-[#ff9500] bg-[#fff8ef]'
                    : 'border-[#ddd] text-[#555] bg-white'
                )}
              >
                {t}
                {i === timePill && (
                  <span className="absolute -top-0.5 -right-0.5 w-2 h-2 bg-[#ff9500] rounded-sm flex items-center justify-center">
                    <span className="text-white text-[7px] font-bold">✓</span>
                  </span>
                )}
              </button>
            ))}
          </div>

          {/* Section Header */}
          <div className="bg-[#f9f9f9] rounded-[6px] px-3 py-2 mb-2 text-[#555] text-xs">
            近一小時最多人搜尋的標的 TOP30
          </div>

          {/* Column Headers */}
          <div className="flex items-center px-1 mb-1">
            <span className="flex-1 text-[#aaa] text-xs">股名</span>
            <span className="w-24 text-center text-[#aaa] text-xs">成交價</span>
            <span className="w-12 text-right text-[#aaa] text-xs">加自選</span>
          </div>

          {/* Stock List */}
          <div className="divide-y divide-[#f0f0f0]">
            {mockTop30.map((s) => {
              const up = s.change >= 0
              return (
                <button
                  key={s.id}
                  onClick={() => navigate(`/stock/${s.id}`)}
                  className="w-full flex items-center py-3 px-1 active:bg-[#f9f9f9] text-left"
                >
                  {/* Stock name + id */}
                  <div className="flex-1 min-w-0">
                    <div className="text-[#1a1a1a] text-sm font-medium">{s.name}</div>
                    <div className="text-[#aaa] text-xs">{s.id}</div>
                  </div>

                  {/* Price + change */}
                  <div className="w-24 text-right">
                    <div className={clsx('text-sm font-bold', up ? 'text-[#e84040]' : 'text-[#2dba6a]')}>
                      {s.price.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                    </div>
                    <div className={clsx('text-xs', up ? 'text-[#e84040]' : 'text-[#2dba6a]')}>
                      {up ? '▲' : '▼'} {Math.abs(s.changePercent).toFixed(2)}%
                    </div>
                    {s.description && (
                      <div className="text-[#888] text-[10px] mt-0.5 leading-tight">{s.description}</div>
                    )}
                  </div>

                  {/* Add button */}
                  <div className="w-12 flex justify-end">
                    <button
                      onClick={(e) => { e.stopPropagation() }}
                      className="w-8 h-8 rounded-full bg-[#ff9500] flex items-center justify-center active:opacity-70"
                    >
                      <Plus size={16} className="text-white" strokeWidth={2.5} />
                    </button>
                  </div>
                </button>
              )
            })}
          </div>

          {/* See More */}
          <button className="w-full flex items-center justify-center py-3 text-[#2dba6a] text-sm gap-1">
            查看更多 <ChevronRight size={14} />
          </button>
        </div>
      </div>
    </div>
  )
}

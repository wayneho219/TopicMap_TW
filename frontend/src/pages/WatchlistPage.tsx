import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, ChevronDown, List, Pencil } from 'lucide-react'
import { clsx } from 'clsx'
import { StockCard } from '../components/StockCard'
import { mockWatchlistTW, mockWatchlistUS } from '../data/mock'

const subTabs = ['台股庫存', '海外股票庫存', '行動自選1', '行動自選2']

export function WatchlistPage() {
  const [subTab, setSubTab] = useState(0)
  const navigate = useNavigate()

  const isActionTab = subTab >= 2
  const stocks = subTab <= 1 ? mockWatchlistTW : mockWatchlistUS

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

        {/* Main Tabs */}
        <div className="flex px-4 border-b border-[#2e2e2e]">
          {['自選', '行情'].map((t, i) => (
            <button
              key={t}
              onClick={() => i === 1 && navigate('/')}
              className={clsx(
                'mr-6 pb-2 text-sm font-medium relative',
                i === 0 ? 'text-white' : 'text-[#888]'
              )}
            >
              {t}
              {i === 0 && (
                <span className="absolute bottom-0 left-1/2 -translate-x-1/2 w-1.5 h-1.5 rounded-full bg-[#2dba6a]" />
              )}
            </button>
          ))}
        </div>

        {/* Sub Tabs */}
        <div className="flex items-center border-b border-[#2e2e2e]">
          <div className="flex-1 flex overflow-x-auto scrollbar-none px-4">
            {subTabs.map((t, i) => (
              <button
                key={t}
                onClick={() => setSubTab(i)}
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
          <button className="flex-shrink-0 px-3 py-2.5 text-[#888]">
            <ChevronDown size={16} />
          </button>
        </div>

        {/* Account Selector */}
        <div className="flex items-center justify-between mx-3 my-2.5 bg-[#1e1e1e] rounded-[8px] px-3 py-2.5">
          <span className="text-[#aaa] text-sm">證券-台北總公司 9822896</span>
          <List size={18} className="text-[#666]" />
        </div>

        {/* Action Tab Meta Info */}
        {isActionTab && (
          <div className="flex items-center justify-between px-4 mb-1">
            <div>
              <span className="text-[#aaa] text-xs">已加入標的 16/60 檔</span>
              <div className="text-[#666] text-[11px] mt-0.5">目前暫不提供日、陸股報價</div>
            </div>
            <div className="flex items-center gap-3">
              <Pencil size={16} className="text-[#666]" />
              <List size={16} className="text-[#666]" />
            </div>
          </div>
        )}
      </div>

      {/* ── 捲動內容區 ── */}
      <div className="flex-1 overflow-y-auto pb-16">
        <div className="px-3 grid grid-cols-2 gap-2 mt-1">
          {stocks.map((s) => (
            <StockCard
              key={s.id}
              stock={s}
              decimals={isActionTab ? 4 : 2}
              onClick={() => navigate(`/stock/${s.id}`)}
            />
          ))}
        </div>
      </div>
    </div>
  )
}

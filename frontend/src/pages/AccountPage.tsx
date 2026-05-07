import { useState } from 'react'
import { Eye, RefreshCw, ChevronDown, Filter } from 'lucide-react'
import { clsx } from 'clsx'
import { mockPortfolio, mockPortfolioSummary } from '../data/mock'

const mainTabs    = ['總覽', '台股', '海外股票', '海外債券', '境外SN']
const subTabs     = ['委託', '成交', '庫存', '對帳單', '交割款']

/* 各子 tab 的篩選 chips */
const filterMap: Record<number, string[]> = {
  0: ['全部交易狀態', '全部商品種類', '全部查詢別'],
  1: ['全部交易狀態', '全部商品種類'],
  2: ['全部交易別'],
  3: ['全部日期', '全部商品'],
  4: ['全部'],
}

export function AccountPage() {
  const [mainTab, setMainTab] = useState(1)    // 台股 selected
  const [subTab,  setSubTab]  = useState(2)    // 庫存 selected
  const [hideAmt, setHideAmt] = useState(false)

  const filters = filterMap[subTab] ?? ['全部']

  return (
    <div className="flex flex-col bg-[#111111] h-screen pb-16">

      {/* ── 釘住頂部 ── */}
      <div className="flex-shrink-0 bg-[#111111] z-20">
        {/* Top Bar */}
        <div className="flex items-center justify-center px-4 pt-14 pb-3">
          <h1 className="text-white text-lg font-semibold">帳務</h1>
        </div>

        {/* Main Tabs */}
        <div className="flex overflow-x-auto scrollbar-none border-b border-[#2e2e2e] px-4">
          {mainTabs.map((t, i) => (
            <button
              key={t}
              onClick={() => setMainTab(i)}
              className={clsx(
                'flex-shrink-0 mr-5 pb-2 text-sm font-medium relative whitespace-nowrap',
                i === mainTab ? 'text-white' : 'text-[#666]'
              )}
            >
              {t}
              {i === mainTab && (
                <span className="absolute bottom-0 left-1/2 -translate-x-1/2 w-1.5 h-1.5 rounded-full bg-[#2dba6a]" />
              )}
            </button>
          ))}
        </div>

        {/* Account Selector */}
        <div className="mx-3 mt-2.5 mb-1 bg-[#1e1e1e] rounded-[8px] px-3 py-2.5">
          <span className="text-[#aaa] text-sm">證券-台北總公司 9822896</span>
        </div>

        {/* Sub Tabs */}
        <div className="flex overflow-x-auto scrollbar-none border-b border-[#2e2e2e] px-4">
          {subTabs.map((t, i) => (
            <button
              key={t}
              onClick={() => setSubTab(i)}
              className={clsx(
                'flex-shrink-0 mr-6 py-2.5 text-sm font-medium relative whitespace-nowrap',
                i === subTab ? 'text-[#2dba6a]' : 'text-[#666]'
              )}
            >
              {t}
              {i === subTab && (
                <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-[#2dba6a] rounded-full" />
              )}
            </button>
          ))}
        </div>

        {/* Filter Row */}
        <div className="flex items-center gap-2 px-3 py-2.5 border-b border-[#2e2e2e]">
          <Filter size={14} className="text-[#666] flex-shrink-0" />
          <div className="flex gap-2 overflow-x-auto scrollbar-none flex-1">
            {filters.map((f) => (
              <button
                key={f}
                className="flex-shrink-0 bg-[#2dba6a] text-white text-xs px-3 py-1 rounded-full font-medium"
              >
                {f}
              </button>
            ))}
          </div>
          {subTab === 2 && (
            <button className="flex-shrink-0 text-[#666]">
              <RefreshCw size={16} />
            </button>
          )}
        </div>
      </div>

      {/* ── 捲動內容區 ── */}
      <div className="flex-1 overflow-y-auto">

        {/* 委託 — 空狀態 */}
        {subTab === 0 && <EmptyState />}

        {/* 成交 — 空狀態 */}
        {subTab === 1 && <EmptyState />}

        {/* 庫存 */}
        {subTab === 2 && (
          <PortfolioTab hideAmt={hideAmt} onToggleHide={() => setHideAmt(h => !h)} />
        )}

        {/* 對帳單 / 交割款 */}
        {(subTab === 3 || subTab === 4) && <EmptyState />}
      </div>
    </div>
  )
}

/* ── 空狀態 ── */
function EmptyState() {
  return (
    <div className="flex items-center justify-center h-64 text-[#555] text-sm">
      查無資料
    </div>
  )
}

/* ── 庫存 Tab ── */
function PortfolioTab({ hideAmt, onToggleHide }: { hideAmt: boolean; onToggleHide: () => void }) {
  const s = mockPortfolioSummary
  const fmt = (n: number) => hideAmt ? '****' : n.toLocaleString()
  const fmtPct = (n: number) => hideAmt ? '**.**%' : `+${n.toFixed(2)}%`

  return (
    <div className="px-3 pt-3 space-y-3">
      {/* 庫存匯總卡 */}
      <div className="bg-[#1e1e1e] rounded-[10px] p-4">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <span className="text-white text-sm font-medium">庫存匯總</span>
            <button onClick={onToggleHide}>
              <Eye size={16} className="text-[#666]" />
            </button>
          </div>
          <button className="flex items-center gap-1.5 text-[#888] text-xs">
            <RefreshCw size={13} />
            不含息
          </button>
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-[#888]">總現值 (TWD)</span>
            <span className="text-white font-medium">{fmt(s.totalValue)}</span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-[#888]">總成本</span>
            <span className="text-white font-medium">{fmt(s.totalCost)}</span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-[#888]">總損益 (不含息)</span>
            <span className="text-[#e84040] font-medium">
              {hideAmt ? '****' : `+${s.totalPnl.toLocaleString()} (${fmtPct(s.totalPnlPercent)})`}
            </span>
          </div>
        </div>
      </div>

      {/* 庫存列表 header */}
      <div className="flex items-center justify-between px-1">
        <span className="text-white text-sm font-medium">庫存列表</span>
        <div className="flex items-center gap-3 text-[#2dba6a] text-xs">
          <button>排序</button>
          <span className="text-[#444]">|</span>
          <button>看列表</button>
        </div>
      </div>

      {/* 庫存列表 */}
      <div className="space-y-0 divide-y divide-[#2e2e2e]">
        {mockPortfolio.map((stock) => (
          <div key={stock.id} className="py-3.5 px-1">
            <div className="flex items-center justify-between mb-1.5">
              <div className="flex items-center gap-2">
                <span className="bg-[#2dba6a] text-white text-[10px] px-2 py-0.5 rounded-full font-medium">
                  {stock.type}
                </span>
                <span className="text-white text-sm font-medium">{stock.name}</span>
                <span className="text-[#666] text-xs">{stock.id}</span>
              </div>
            </div>
            <div className="flex items-center justify-between mb-1">
              <span className="text-[#888] text-xs">總股數</span>
              <button className="flex items-center gap-1 text-white text-sm font-medium underline decoration-dotted">
                {stock.shares.toLocaleString()}
                <ChevronDown size={14} className="text-[#666]" />
              </button>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-[#888] text-xs">總損益 (不含息)</span>
              <span className={clsx('text-sm font-medium', stock.pnl >= 0 ? 'text-[#e84040]' : 'text-[#2dba6a]')}>
                {hideAmt
                  ? '****'
                  : `+${stock.pnl.toLocaleString()} (${stock.pnlPercent === 0 ? '0%' : `+${stock.pnlPercent.toFixed(2)}%`})`
                }
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

import { useState } from 'react'
import { Eye, RefreshCw, ChevronDown, Filter, ChevronRight, Leaf } from 'lucide-react'
import { clsx } from 'clsx'
import { mockPortfolio, mockPortfolioSummary } from '../data/mock'
import { PieChart, Pie, Cell } from 'recharts'

const sg = (n: number) => n >= 0 ? '+' : ''   // sign prefix for PnL

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
  const [mainTab, setMainTab] = useState(0)    // 總覽 selected
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

        {/* Account Selector — 只在非總覽 tab 顯示 */}
        {mainTab !== 0 && (
          <div className="mx-3 mt-2.5 mb-1 bg-[#1e1e1e] rounded-[8px] px-3 py-2.5">
            <span className="text-[#aaa] text-sm">證券-台中總公司 0012345</span>
          </div>
        )}

        {/* Sub Tabs — 只在非總覽 tab 顯示 */}
        {mainTab !== 0 && (
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
        )}

        {/* Filter Row — 只在非總覽 tab 顯示 */}
        {mainTab !== 0 && (
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
        )}
      </div>

      {/* ── 捲動內容區 ── */}
      <div className="flex-1 overflow-y-auto">

        {/* 總覽 tab */}
        {mainTab === 0 && (
          <OverviewTab hideAmt={hideAmt} onToggleHide={() => setHideAmt(h => !h)} />
        )}

        {/* 其他 tab（台股/海外/債券/SN） */}
        {mainTab !== 0 && (
          <>
            {subTab !== 2 && <EmptyState />}
            {subTab === 2 && mainTab === 1 && (
              <PortfolioTab hideAmt={hideAmt} onToggleHide={() => setHideAmt(h => !h)} />
            )}
            {subTab === 2 && mainTab === 2 && (
              <USPortfolioTab hideAmt={hideAmt} onToggleHide={() => setHideAmt(h => !h)} />
            )}
            {subTab === 2 && mainTab >= 3 && <EmptyState />}
          </>
        )}
      </div>
    </div>
  )
}

/* ── 總覽 Tab ── */
const PIE_COLORS = ['#4a9fd4', '#7ec8e3', '#2dba6a', '#e8a040', '#a06ad4']
const twTotal = mockPortfolio.reduce((s, p) => s + p.totalValue, 0)
const twPie = mockPortfolio.map((p, i) => ({
  name: p.name.slice(0, 5),
  value: Math.round(p.totalValue / twTotal * 1000) / 10,
  color: PIE_COLORS[i % PIE_COLORS.length],
}))

const usMock = { totalValueUSD: 1243.50, totalCostUSD: 1180.00, pnlUSD: 63.50, pnlPct: 5.38 }
const US_RATE = 32.5
const usTotalTWD = Math.round(usMock.totalValueUSD * US_RATE)
const usPie = [
  { name: 'AAPL', value: 45, color: '#4a9fd4' },
  { name: 'MSFT', value: 35, color: '#7ec8e3' },
  { name: 'GOOGL', value: 20, color: '#2dba6a' },
]

const mockUSPortfolio = [
  { id: 'AAPL',  name: 'Apple',     type: '美股', shares: 2,   totalValue: 559.58, totalCost: 531.00, pnl:  28.58, pnlPercent: 5.38 },
  { id: 'MSFT',  name: 'Microsoft', type: '美股', shares: 1,   totalValue: 435.23, totalCost: 413.00, pnl:  22.23, pnlPercent: 5.38 },
  { id: 'GOOGL', name: 'Alphabet',  type: '美股', shares: 0.6, totalValue: 248.70, totalCost: 236.00, pnl:  12.70, pnlPercent: 5.38 },
]

const twCost    = mockPortfolioSummary.totalCost
const twPnl     = mockPortfolioSummary.totalPnl
const twPnlPct  = mockPortfolioSummary.totalPnlPercent
const grandTotal   = twTotal + usTotalTWD
const grandCost    = twCost + Math.round(usMock.totalCostUSD * US_RATE)
const grandPnl     = twPnl + Math.round(usMock.pnlUSD * US_RATE)
const grandPnlPct  = grandPnl / grandCost * 100
const twAllocPct   = (twTotal / grandTotal * 100).toFixed(2)
const usAllocPct   = (usTotalTWD / grandTotal * 100).toFixed(2)

function DonutCard({
  currency, amount, pctLabel, pie, legend, cost, pnl,
}: {
  currency: string
  amount: string
  pctLabel: string
  pie: { name: string; value: number; color: string }[]
  legend: { name: string; value: number; color: string }[]
  cost: string
  pnl: string
}) {
  return (
    <div className="bg-[#1e1e1e] rounded-[12px] p-4">
      <div className="text-[#888] text-xs mb-1">庫存現值比例 <span className="text-[#666]">｜ 總資產</span></div>
      <div className="flex items-center gap-4 my-2">
        {/* Donut */}
        <div className="relative flex-shrink-0" style={{ width: 140, height: 140 }}>
          <PieChart width={140} height={140}>
            <Pie data={pie} cx={65} cy={65} innerRadius={46} outerRadius={66} dataKey="value" startAngle={90} endAngle={-270} strokeWidth={0}>
              {pie.map((entry, i) => <Cell key={i} fill={entry.color} />)}
            </Pie>
          </PieChart>
          <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
            <span className="text-[#888] text-[10px]">{currency}</span>
            <span className="text-white text-lg font-bold leading-tight">{amount}</span>
            <span className="text-[#e84040] text-[11px]">({pctLabel})</span>
          </div>
        </div>
        {/* Legend */}
        <div className="flex flex-col gap-2">
          {legend.map((item) => (
            <div key={item.name} className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ background: item.color }} />
              <span className="text-[#aaa] text-xs">{item.value}% {item.name}</span>
            </div>
          ))}
        </div>
      </div>
      <div className="flex border-t border-[#2e2e2e] pt-3 mt-1">
        <div className="flex-1">
          <div className="text-[#888] text-xs mb-0.5">總成本</div>
          <div className="text-white text-sm font-medium">{cost}</div>
        </div>
        <div className="flex-1">
          <div className="text-[#888] text-xs mb-0.5">不含息參考報酬</div>
          <div className="text-[#e84040] text-sm font-medium">{pnl}</div>
        </div>
      </div>
    </div>
  )
}

function OverviewTab({ hideAmt, onToggleHide }: { hideAmt: boolean; onToggleHide: () => void }) {
  const mask = (v: string) => hideAmt ? '****' : v
  return (
    <div className="px-3 pt-4 space-y-4 pb-6">
      {/* 總資產摘要 */}
      <div>
        <div className="flex items-center justify-between mb-1">
          <div className="flex items-center gap-1.5 text-[#888] text-xs">
            <span>庫存總現值 (TWD)</span>
            <button onClick={onToggleHide}><Eye size={14} className="text-[#666]" /></button>
          </div>
          <span className="text-[#666] text-xs">依昨收匯率計算</span>
        </div>
        <div className="flex items-baseline gap-2 mb-3">
          <span className="text-white text-2xl font-bold">{mask(grandTotal.toLocaleString())}</span>
          <span className={clsx('text-sm', grandPnlPct >= 0 ? 'text-[#e84040]' : 'text-[#2dba6a]')}>({mask(`${sg(grandPnlPct)}${grandPnlPct.toFixed(2)}%`)})</span>
        </div>
        <div className="flex gap-6 mb-3">
          <div>
            <div className="text-[#888] text-xs mb-0.5">總成本</div>
            <div className="text-white text-sm font-medium">{mask(grandCost.toLocaleString())}</div>
          </div>
          <div>
            <div className="text-[#888] text-xs mb-0.5">不含息參考報酬 <span className="text-[#666]">ⓘ</span></div>
            <div className={clsx('text-sm font-medium', grandPnl >= 0 ? 'text-[#e84040]' : 'text-[#2dba6a]')}>{mask(`${sg(grandPnl)}${grandPnl.toLocaleString()}`)}</div>
          </div>
        </div>
        {/* 台股/海外分配條 */}
        <div className="h-2 rounded-full overflow-hidden flex mb-1.5">
          <div className="bg-[#4a9fd4]" style={{ width: `${twAllocPct}%` }} />
          <div className="bg-[#2dba6a]" style={{ width: `${usAllocPct}%` }} />
        </div>
        <div className="flex gap-4 text-xs">
          <span><span className="inline-block w-2.5 h-2.5 rounded-sm bg-[#4a9fd4] mr-1 align-middle" />台 <span className="text-[#4a9fd4]">{twAllocPct}%</span></span>
          <span><span className="inline-block w-2.5 h-2.5 rounded-sm bg-[#2dba6a] mr-1 align-middle" />海外股 <span className="text-[#2dba6a]">{usAllocPct}%</span></span>
        </div>
      </div>

      {/* 台股區塊 */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <span className="text-white text-sm font-semibold">台股</span>
          <button className="flex items-center gap-0.5 text-[#2dba6a] text-xs">看台股明細 <ChevronRight size={13} /></button>
        </div>
        <DonutCard
          currency="TWD"
          amount={mask(twTotal.toLocaleString())}
          pctLabel={mask(`${sg(twPnlPct)}${twPnlPct.toFixed(2)}%`)}
          pie={twPie}
          legend={twPie}
          cost={mask(twCost.toLocaleString())}
          pnl={mask(`${sg(twPnl)}${twPnl.toLocaleString()}`)}
        />
        <button className="flex items-center gap-2 mt-3 text-[#2dba6a] text-xs">
          <Leaf size={14} />
          查看我的台股庫存永續力
          <ChevronRight size={13} />
        </button>
      </div>

      {/* 股息再投資橫幅 */}
      <div className="bg-[#3a2800] rounded-[10px] px-4 py-3.5 flex items-center justify-between">
        <div>
          <div className="text-white text-sm font-medium mb-0.5">股息再投資，持續投入讓庫存再長大</div>
          <div className="text-[#c8a84b] text-xs">快來查看，<span className="underline">開啟複利計畫</span></div>
        </div>
        <ChevronRight size={16} className="text-[#c8a84b] flex-shrink-0" />
      </div>

      {/* 海外股票區塊 */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <span className="text-white text-sm font-semibold">海外股票</span>
          <button className="flex items-center gap-0.5 text-[#2dba6a] text-xs">看海外股票明細 <ChevronRight size={13} /></button>
        </div>
        <div className="flex gap-2 mb-3">
          <span className="bg-[#2dba6a] text-white text-xs px-3 py-1 rounded-full font-medium">美股</span>
        </div>
        <DonutCard
          currency="USD"
          amount={mask(usMock.totalValueUSD.toFixed(2))}
          pctLabel={mask(`${sg(usMock.pnlPct)}${usMock.pnlPct.toFixed(2)}%`)}
          pie={usPie}
          legend={usPie}
          cost={mask(usMock.totalCostUSD.toFixed(2))}
          pnl={mask(`${sg(usMock.pnlUSD)}${usMock.pnlUSD.toFixed(2)}`)}
        />
      </div>
    </div>
  )
}

/* ── 美股庫存 Tab ── */
function USPortfolioTab({ hideAmt, onToggleHide }: { hideAmt: boolean; onToggleHide: () => void }) {
  const fmt = (n: number) => hideAmt ? '****' : n.toFixed(2)

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
            <span className="text-[#888]">總現值 (USD)</span>
            <span className="text-white font-medium">{fmt(usMock.totalValueUSD)}</span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-[#888]">總成本</span>
            <span className="text-white font-medium">{fmt(usMock.totalCostUSD)}</span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-[#888]">總損益 (不含息)</span>
            <span className={clsx('font-medium', usMock.pnlUSD >= 0 ? 'text-[#e84040]' : 'text-[#2dba6a]')}>
              {hideAmt ? '****' : `${sg(usMock.pnlUSD)}${usMock.pnlUSD.toFixed(2)} (${sg(usMock.pnlPct)}${usMock.pnlPct.toFixed(2)}%)`}
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
        {mockUSPortfolio.map((stock) => (
          <div key={stock.id} className="py-3.5 px-1">
            <div className="flex items-center justify-between mb-1.5">
              <div className="flex items-center gap-2">
                <span className="bg-[#4a9fd4] text-white text-[10px] px-2 py-0.5 rounded-full font-medium">
                  {stock.type}
                </span>
                <span className="text-white text-sm font-medium">{stock.name}</span>
                <span className="text-[#666] text-xs">{stock.id}</span>
              </div>
            </div>
            <div className="flex items-center justify-between mb-1">
              <span className="text-[#888] text-xs">持股數量</span>
              <button className="flex items-center gap-1 text-white text-sm font-medium underline decoration-dotted">
                {stock.shares}
                <ChevronDown size={14} className="text-[#666]" />
              </button>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-[#888] text-xs">總損益 (不含息)</span>
              <span className={clsx('text-sm font-medium', stock.pnl >= 0 ? 'text-[#e84040]' : 'text-[#2dba6a]')}>
                {hideAmt ? '****' : `${sg(stock.pnl)}${stock.pnl.toFixed(2)} (${sg(stock.pnlPercent)}${stock.pnlPercent.toFixed(2)}%)`}
              </span>
            </div>
          </div>
        ))}
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
  const fmtPct = (n: number) => hideAmt ? '**.**%' : `${sg(n)}${n.toFixed(2)}%`

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
            <span className={clsx('font-medium', s.totalPnl >= 0 ? 'text-[#e84040]' : 'text-[#2dba6a]')}>
              {hideAmt ? '****' : `${sg(s.totalPnl)}${s.totalPnl.toLocaleString()} (${fmtPct(s.totalPnlPercent)})`}
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
                  : `${sg(stock.pnl)}${stock.pnl.toLocaleString()} (${stock.pnlPercent === 0 ? '0%' : `${sg(stock.pnlPercent)}${stock.pnlPercent.toFixed(2)}%`})`
                }
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

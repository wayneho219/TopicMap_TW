import { useState } from 'react'
import { Eye, RefreshCw, ChevronDown, Filter, ChevronRight, Leaf } from 'lucide-react'
import { clsx } from 'clsx'
import { mockPortfolio, mockPortfolioSummary } from '../data/mock'
import { PieChart, Pie, Cell } from 'recharts'

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
            <span className="text-[#aaa] text-sm">證券-台北總公司 9822896</span>
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
            {subTab === 0 && <EmptyState />}
            {subTab === 1 && <EmptyState />}
            {subTab === 2 && (
              <PortfolioTab hideAmt={hideAmt} onToggleHide={() => setHideAmt(h => !h)} />
            )}
            {(subTab === 3 || subTab === 4) && <EmptyState />}
          </>
        )}
      </div>
    </div>
  )
}

/* ── 總覽 Tab ── */
const twPie = [
  { name: '富邦公司...', value: 70.5, color: '#4a9fd4' },
  { name: '富邦台50',   value: 25.4, color: '#7ec8e3' },
  { name: '華通',       value: 4.1,  color: '#2dba6a' },
]
const usPie = [
  { name: 'PLTR', value: 100, color: '#4a9fd4' },
]

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
          <span className="text-white text-2xl font-bold">{mask('326,202')}</span>
          <span className="text-[#e84040] text-sm">({mask('+1047.95%')})</span>
        </div>
        <div className="flex gap-6 mb-3">
          <div>
            <div className="text-[#888] text-xs mb-0.5">總成本</div>
            <div className="text-white text-sm font-medium">{mask('28,416')}</div>
          </div>
          <div>
            <div className="text-[#888] text-xs mb-0.5">不含息參考報酬 <span className="text-[#666]">ⓘ</span></div>
            <div className="text-[#e84040] text-sm font-medium">{mask('+297,786')}</div>
          </div>
        </div>
        {/* 台股/海外分配條 */}
        <div className="h-2 rounded-full overflow-hidden flex mb-1.5">
          <div className="bg-[#4a9fd4]" style={{ width: '93.41%' }} />
          <div className="bg-[#2dba6a]" style={{ width: '6.59%' }} />
        </div>
        <div className="flex gap-4 text-xs">
          <span><span className="inline-block w-2.5 h-2.5 rounded-sm bg-[#4a9fd4] mr-1 align-middle" />台 <span className="text-[#4a9fd4]">93.41%</span></span>
          <span><span className="inline-block w-2.5 h-2.5 rounded-sm bg-[#2dba6a] mr-1 align-middle" />海外股 <span className="text-[#2dba6a]">6.59%</span></span>
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
          amount={mask('304,719')}
          pctLabel={mask('+4251.89%')}
          pie={twPie}
          legend={twPie}
          cost={mask('7,002')}
          pnl={mask('+297,717')}
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
          amount={mask('685.25')}
          pctLabel={mask('+0.32%')}
          pie={usPie}
          legend={usPie}
          cost={mask('683.05')}
          pnl={mask('+2.20')}
        />
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

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, ChevronRight, MessageSquare } from 'lucide-react'
import { clsx } from 'clsx'
import { mockRecurringUS, type RecurringStock } from '../data/mock'
import { useRecurringTW } from '../hooks/useMarketData'

const twPills = ['人氣爆棚', '月月配息', '高殖利率', '火熱上架']
const usPills = ['人氣爆棚', '標的總覽', '績優標的', '火熱上架']

const rankColors: Record<number, string> = { 1: '#ff9500', 2: '#ff9500', 3: '#ff9500' }

export function RecurringPage() {
  const [mainTab, setMainTab]   = useState(0)   // 0=台股 1=美股
  const [pill, setPill]         = useState(0)
  const navigate = useNavigate()

  const rawTW = useRecurringTW()
  const liveTW: RecurringStock[] = rawTW.map((s) => ({
    rank: s.rank, id: s.id, name: s.name, price: s.price,
    type: 'ETF', metric: s.changePercent, metricIsYield: false,
  }))

  const isTW    = mainTab === 0
  const pills   = isTW ? twPills : usPills
  const stocks  = isTW ? liveTW : mockRecurringUS
  const col1    = '收盤價'
  const col2    = isTW ? '漲跌幅' : '漲跌幅(月)'

  return (
    <div className="flex flex-col bg-white h-screen">

      {/* ── 釘住頂部 ── */}
      <div className="flex-shrink-0 bg-white z-20 border-b border-[#f0f0f0]">
        {/* Top Bar */}
        <div className="flex items-center justify-between px-4 pt-14 pb-3">
          <div className="w-6" />
          <h1 className="text-[#1a1a1a] text-lg font-semibold">定期投資</h1>
          <button className="text-[#888]">
            <Search size={20} />
          </button>
        </div>
      </div>

      {/* ── 捲動內容區 ── */}
      <div className="flex-1 overflow-y-auto pb-16 bg-[#f7f7f7]">

        {/* Banner Carousel */}
        <div className="mx-3 mt-3 rounded-[12px] overflow-hidden bg-[#fdf0e0]" style={{ minHeight: 110 }}>
          <div className="flex items-center justify-between px-4 py-5">
            <div className="flex-1">
              <div className="text-[#888] text-xs mb-1">好評再進化 台股定期定額</div>
              <div className="text-[#ff9500] text-2xl font-bold leading-tight">
                100元就能買
              </div>
              <div className="text-[#333] text-sm font-medium">手續費只要<span className="text-[#ff9500] font-bold">1</span>元</div>
            </div>
            <div className="text-5xl">👩‍💼</div>
          </div>
          <div className="flex justify-center gap-1.5 pb-2">
            {[0, 1, 2].map((i) => (
              <span key={i} className={`w-2 h-2 rounded-full ${i === 1 ? 'bg-[#ff9500]' : 'bg-[#ddd]'}`} />
            ))}
          </div>
        </div>

        {/* 我的定期投資 */}
        <div className="mx-3 mt-3 bg-white rounded-[12px] overflow-hidden border border-[#eee]">
          <div className="px-4 py-3 border-b border-[#f0f0f0]">
            <div className="text-[#1a1a1a] text-sm font-semibold mb-2">我的定期投資</div>
          </div>
          {[
            {
              label: '申購單',
              right: <span className="text-sm">台股 <span className="text-[#2dba6a] font-medium">0</span> 筆｜美股 <span className="text-[#2dba6a] font-medium">0</span> 筆</span>,
            },
            {
              label: '股息再投資',
              right: <span className="text-[#888] text-xs">每月100元，打造複利存股計畫</span>,
            },
            {
              label: undefined,
              right: <span className="text-[#888] text-xs flex items-center gap-1">
                <span className="text-[#2dba6a]">$</span>定期定額手續費：台股皆1元｜美股皆0.1美元
              </span>,
            },
          ].map((row, i) => (
            <button key={i} className="w-full flex items-center justify-between px-4 py-3 border-b border-[#f5f5f5] last:border-0 active:bg-[#f9f9f9]">
              {row.label && <span className="text-[#1a1a1a] text-sm mr-3 flex-shrink-0">{row.label}</span>}
              <div className="flex-1 flex justify-end items-center gap-1.5">
                {row.right}
                <ChevronRight size={14} className="text-[#ccc]" />
              </div>
            </button>
          ))}
        </div>

        {/* Main Tabs + Pills + List (white card) */}
        <div className="mx-3 mt-3 bg-white rounded-[12px] overflow-hidden border border-[#eee]">

          {/* Main Tabs */}
          <div className="flex border-b border-[#eee]">
            {['台股', '美股'].map((t, i) => (
              <button
                key={t}
                onClick={() => { setMainTab(i); setPill(0) }}
                className={clsx(
                  'flex-1 py-3 text-sm font-medium relative',
                  i === mainTab ? 'text-[#2dba6a]' : 'text-[#aaa]'
                )}
              >
                {t}
                {i === mainTab && (
                  <span className="absolute bottom-0 left-1/4 right-1/4 h-0.5 bg-[#2dba6a] rounded-full" />
                )}
              </button>
            ))}
          </div>

          {/* Category Pills */}
          <div className="flex gap-2 px-3 py-3 overflow-x-auto scrollbar-none">
            {pills.map((p, i) => (
              <button
                key={p}
                onClick={() => setPill(i)}
                className={clsx(
                  'flex-shrink-0 px-4 py-1.5 rounded-full text-sm font-medium',
                  i === pill
                    ? 'bg-[#2dba6a] text-white'
                    : 'bg-[#f0f0f0] text-[#888]'
                )}
              >
                {p}
              </button>
            ))}
          </div>

          {/* Column Headers */}
          <div className="flex items-center px-4 py-2 border-t border-[#f5f5f5]">
            <span className="flex-1 text-[#aaa] text-xs">股票</span>
            <span className="w-20 text-right text-[#aaa] text-xs">{col1}</span>
            <span className="w-24 text-right text-[#aaa] text-xs mr-10">{col2}</span>
          </div>

          {/* Stock List */}
          <div className="divide-y divide-[#f5f5f5]">
            {stocks.map((s) => (
              <StockRow
                key={`${s.rank}-${s.id}`}
                stock={s}
                onBuy={() => navigate(isTW ? `/subscribe/tw/${s.id}` : `/subscribe/us/${s.id}`)}
              />
            ))}
          </div>

          {/* 看更多標的 */}
          <div className="px-3 py-3">
            <button className="w-full py-3.5 bg-[#2dba6a] text-white rounded-[10px] text-sm font-medium active:opacity-80">
              看更多標的
            </button>
          </div>
        </div>

        {/* 幫助中心 */}
        <div className="mx-3 mt-3 mb-3">
          <div className="text-[#1a1a1a] text-sm font-semibold mb-2 px-1">幫助中心</div>
          <button className="w-full bg-white rounded-[12px] border border-[#eee] px-4 py-4 flex items-center gap-3 active:bg-[#f9f9f9]">
            <div className="w-10 h-10 rounded-[10px] bg-[#e8f8f0] flex items-center justify-center flex-shrink-0">
              <MessageSquare size={20} className="text-[#2dba6a]" />
            </div>
            <div className="flex-1 text-left">
              <div className="text-[#1a1a1a] text-sm font-medium">定期投資是什麼？</div>
              <div className="text-[#aaa] text-xs mt-0.5">申請流程、常見問題...</div>
            </div>
            <ChevronRight size={16} className="text-[#ccc]" />
          </button>
        </div>
      </div>
    </div>
  )
}

function StockRow({ stock, onBuy }: { stock: RecurringStock; onBuy: () => void }) {
  const rankColor = rankColors[stock.rank] ?? '#1a1a1a'
  const up = stock.metric >= 0

  return (
    <div className="flex items-center px-4 py-3.5">
      {/* Rank + Name */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-sm font-bold w-4 flex-shrink-0" style={{ color: rankColor }}>
            {stock.rank}
          </span>
          <span className="text-[#1a1a1a] text-sm font-medium truncate">{stock.name}</span>
        </div>
        <div className="flex items-center gap-1.5 mt-0.5 ml-6">
          <span className="bg-[#f0f0f0] text-[#888] text-[10px] px-1.5 py-0.5 rounded">
            {stock.type}
          </span>
          <span className="text-[#aaa] text-xs">{stock.id}</span>
        </div>
      </div>

      {/* Price */}
      <div className="w-20 text-right">
        <span className="text-[#1a1a1a] text-sm font-medium">{stock.price.toFixed(2)}</span>
      </div>

      {/* Metric */}
      <div className="w-20 text-right">
        <span className={clsx('text-sm font-medium', stock.metricIsYield ? 'text-[#1a1a1a]' : up ? 'text-[#e84040]' : 'text-[#2dba6a]')}>
          {!stock.metricIsYield && (up ? '▲' : '▼')}{stock.metric.toFixed(2)}%
        </span>
      </div>

      {/* 申購 Button */}
      <button
        onClick={onBuy}
        className="ml-2 border border-[#ff9500] text-[#ff9500] text-xs px-2.5 py-1.5 rounded-[6px] font-medium active:bg-[#fff8ef] flex-shrink-0"
      >
        申購
      </button>
    </div>
  )
}

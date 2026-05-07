import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import {
  ArrowLeft, Heart, Search, ChevronDown, Maximize2, Info,
} from 'lucide-react'
import { clsx } from 'clsx'
import {
  ComposedChart, Line, Bar, XAxis, YAxis, CartesianGrid,
  ResponsiveContainer, ReferenceLine,
} from 'recharts'
import { mockChartData } from '../data/mock'
import { useStock } from '../hooks/useStock'

const chartTabs = ['K線', '五檔', '價量', '明細', '券商分點', '指標', '籌碼']
const timeTabs = ['分時', '日', '週', '月']
const brokerTopTabs = ['買超 Top 15', '賣超 Top 15']

// TODO: replace with GET /api/stocks/:id/broker
const mockBrokerStats = {
  netFlow: '+846',
  concentration: '+9.6',
  volume: '8827',
  shareRatio: '0.05%',
  turnoverRate: '0.48%',
  signal: '小買',
}

const mockBrokerTop: { name: string; net: number; buyAvg: number; sellAvg: number }[] = [
  { name: '元大', net: 312, buyAvg: 226.5, sellAvg: 227.1 },
  { name: '富邦', net: 198, buyAvg: 226.2, sellAvg: 226.8 },
  { name: '凱基', net: 142, buyAvg: 226.0, sellAvg: 227.3 },
  { name: '國泰', net: 94, buyAvg: 225.9, sellAvg: 226.6 },
  { name: '永豐金', net: 68, buyAvg: 226.1, sellAvg: 226.9 },
]

export function StockDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [chartTab, setChartTab] = useState(0)
  const [timeTab, setTimeTab] = useState(0)
  const [brokerTopTab, setBrokerTopTab] = useState(0)
  const { stock, loading, error } = useStock(id)

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-[#111111]">
        <div className="w-8 h-8 rounded-full border-2 border-[#2dba6a] border-t-transparent animate-spin" />
      </div>
    )
  }

  if (error || !stock) {
    return (
      <div className="flex flex-col items-center justify-center h-screen bg-[#111111] gap-3">
        <span className="text-[#888] text-sm">{error ?? '找不到股票'}</span>
        <button onClick={() => navigate(-1)} className="text-[#2dba6a] text-sm">返回</button>
      </div>
    )
  }

  const isUp = stock.change >= 0

  return (
    <div className="flex flex-col bg-[#111111] h-screen">

      {/* ── 釘住頂部 ── */}
      <div className="flex-shrink-0 bg-[#111111] z-20">
        {/* Top Bar */}
        <div className="flex items-center justify-between px-4 pt-14 pb-3">
          <button onClick={() => navigate(-1)} className="text-[#aaa] active:opacity-60 p-1">
            <ArrowLeft size={20} />
          </button>
          <span className="text-white text-base font-medium">
            ({id ?? stock.id}) {stock.name}
          </span>
          <div className="flex items-center gap-3 text-[#888]">
            <Heart size={20} />
            <Search size={20} />
          </div>
        </div>

        {/* Price Card */}
        <div className="mx-3 bg-[#1e1e1e] rounded-[12px] p-4 mb-3">
          <div className="flex items-start justify-between mb-2">
            <span className="bg-[#3a3020] text-[#c8a84b] text-xs px-2 py-0.5 rounded">
              {stock.status}
            </span>
            <button className="border border-[#2dba6a] text-[#2dba6a] text-xs px-3 py-1 rounded">
              零股
            </button>
          </div>

          <div className="flex items-end gap-3 mb-2">
            <span className={`${isUp ? 'text-[#e84040]' : 'text-[#2dba6a]'} text-4xl font-bold tracking-tight`}>
              {stock.price.toFixed(2)}
            </span>
            <div className={`${isUp ? 'text-[#e84040]' : 'text-[#2dba6a]'} text-sm pb-1`}>
              <div>{isUp ? '▲' : '▼'} {Math.abs(stock.change).toFixed(2)}</div>
              <div>{isUp ? '▲' : '▼'} {Math.abs(stock.changePercent).toFixed(2)}%</div>
            </div>
          </div>

          <div className="flex gap-2 mb-3">
            {stock.tags.map((tag) => (
              <span key={tag} className="border border-[#444] text-[#aaa] text-xs px-2.5 py-0.5 rounded-full">
                {tag}
              </span>
            ))}
          </div>

          <div className="grid grid-cols-2 gap-y-1.5 text-sm">
            <div className="flex gap-2">
              <span className="text-[#888]">最高</span>
              <span className="text-[#e84040] font-medium">{stock.high != null ? stock.high.toFixed(2) : '—'}</span>
            </div>
            <div className="flex gap-2">
              <span className="text-[#888]">昨收</span>
              <span className="text-white font-medium">{stock.prevClose != null ? stock.prevClose.toFixed(2) : '—'}</span>
            </div>
            <div className="flex gap-2">
              <span className="text-[#888]">最低</span>
              <span className="text-[#e84040] font-medium">{stock.low != null ? stock.low.toFixed(2) : '—'}</span>
            </div>
            <div className="flex gap-2">
              <span className="text-[#888]">開盤</span>
              <span className="text-[#e84040] font-medium">{stock.open != null ? stock.open.toFixed(2) : '—'}</span>
            </div>
          </div>

          <div className="flex justify-center mt-2">
            <ChevronDown size={16} className="text-[#555]" />
          </div>
        </div>

        {/* Chart Tab Bar */}
        <div className="flex overflow-x-auto scrollbar-none border-b border-[#2e2e2e] px-3">
          {chartTabs.map((t, i) => (
            <button
              key={t}
              onClick={() => setChartTab(i)}
              className={clsx(
                'flex-shrink-0 mr-5 pb-2 text-sm font-medium relative whitespace-nowrap',
                i === chartTab ? 'text-[#2dba6a]' : 'text-[#666]'
              )}
            >
              {t}
              {i === chartTab && (
                <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-[#2dba6a] rounded-full" />
              )}
            </button>
          ))}
        </div>
      </div>

      {/* ── 捲動內容區 ── */}
      <div className="flex-1 overflow-y-auto pb-24">
        {chartTab === 0 && <KLineTab timeTab={timeTab} setTimeTab={setTimeTab} prevClose={stock.prevClose ?? stock.price} />}
        {chartTab === 4 && <BrokerTab brokerTopTab={brokerTopTab} setBrokerTopTab={setBrokerTopTab} />}
        {chartTab !== 0 && chartTab !== 4 && (
          <div className="flex items-center justify-center h-40 text-[#555] text-sm">
            {chartTabs[chartTab]}（開發中）
          </div>
        )}
      </div>

      {/* Bottom CTA Buttons — always visible */}
      <div className="fixed bottom-0 left-1/2 -translate-x-1/2 w-full max-w-[430px] flex gap-2 px-3 py-3 bg-[#111111] border-t border-[#2e2e2e] z-40">
        <button
          onClick={() => navigate(`/subscribe/tw/${id}`)}
          className="flex-1 py-3.5 rounded-[10px] bg-[#2dba6a] text-white font-medium text-sm active:opacity-80"
        >
          定期投資申購
        </button>
        <button
          onClick={() => navigate('/order')}
          className="flex-1 py-3.5 rounded-[10px] bg-[#2dba6a] text-white font-medium text-sm active:opacity-80"
        >
          個股下單
        </button>
      </div>
    </div>
  )
}

/* ── K線 Tab ── */
function KLineTab({
  timeTab, setTimeTab, prevClose,
}: {
  timeTab: number
  setTimeTab: (i: number) => void
  prevClose: number
}) {
  return (
    <>
      <div className="flex items-center px-3 py-2 gap-2">
        {timeTabs.map((t, i) => (
          <button
            key={t}
            onClick={() => setTimeTab(i)}
            className={clsx(
              'px-3 py-1 rounded text-sm',
              i === timeTab ? 'bg-[#2dba6a] text-white font-medium' : 'text-[#888]'
            )}
          >
            {t}
          </button>
        ))}
        <button className="flex items-center gap-0.5 text-[#888] text-sm ml-1">
          60 分鐘 <ChevronDown size={14} />
        </button>
        <button className="ml-auto text-[#888]">
          <Maximize2 size={16} />
        </button>
      </div>

      <div className="flex items-center gap-3 px-3 pb-1 text-xs">
        <span className="text-[#888]">13:30</span>
        <span className="text-[#aaa]">價：<span className="text-[#e84040]">97.70</span></span>
        <span className="text-[#e84040]">▲1.95(2.04%)</span>
        <span className="text-[#aaa]">量：<span className="text-[#2dba6a]">132</span></span>
      </div>

      <div className="px-1" style={{ height: 260 }}>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={mockChartData} margin={{ top: 4, right: 44, left: 4, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2a" vertical={false} />
            <XAxis dataKey="time" tick={{ fill: '#666', fontSize: 10 }} tickLine={false} axisLine={false} interval={3} />
            <YAxis yAxisId="price" orientation="left" domain={[93, 98.8]} tick={{ fill: '#666', fontSize: 10 }} tickLine={false} axisLine={false} tickCount={5} tickFormatter={(v) => v.toFixed(2)} width={44} />
            <YAxis yAxisId="pct" orientation="right" domain={[-3.2, 3.2]} tick={{ fill: '#666', fontSize: 10 }} tickLine={false} axisLine={false} tickCount={5} tickFormatter={(v) => `${v > 0 ? '+' : ''}${v.toFixed(1)}%`} width={44} />
            <ReferenceLine yAxisId="price" y={prevClose} stroke="#555" strokeDasharray="4 2" />
            <Bar yAxisId="pct" dataKey="volume" fill="#c8a020" opacity={0.7} maxBarSize={6} />
            <Line yAxisId="price" type="monotone" dataKey="price" stroke="#e84040" strokeWidth={1.5} dot={false} activeDot={{ r: 3, fill: '#e84040' }} />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </>
  )
}

/* ── 券商分點 Tab ── */
function BrokerTab({
  brokerTopTab, setBrokerTopTab,
}: {
  brokerTopTab: number
  setBrokerTopTab: (i: number) => void
}) {
  const showBuy = brokerTopTab === 0

  return (
    <div className="px-3 pt-3">
      {/* Header row */}
      <div className="flex items-start justify-between mb-1">
        <div>
          <div className="flex items-center gap-1.5">
            <span className="text-white text-sm font-medium">主力動向</span>
            <Info size={14} className="text-[#666]" />
          </div>
          <div className="text-[#666] text-xs mt-0.5">更新時間 2026/05/06 21:30</div>
        </div>
        <button className="flex items-center gap-2 bg-[#2a2a2a] rounded-[8px] px-3 py-2 text-[#aaa] text-sm">
          近1日 <ChevronDown size={14} />
        </button>
      </div>

      {/* Signal circle + stats */}
      <div className="flex items-center gap-4 mt-4 mb-5">
        {/* Circle */}
        <div
          className="flex-shrink-0 w-36 h-36 rounded-full flex items-center justify-center relative"
          style={{
            background: 'radial-gradient(circle at 40% 40%, #5a1a1a, #2a0808)',
            boxShadow: '0 0 30px rgba(180,20,20,0.3)',
          }}
        >
          {/* Scattered dots */}
          <span className="absolute top-3 right-5 w-2 h-2 rounded-full bg-[#e84040] opacity-70" />
          <span className="absolute bottom-6 left-3 w-2.5 h-2.5 rounded-full bg-[#e84040] opacity-80" />
          <span className="absolute top-1/2 right-2 w-1.5 h-1.5 rounded-full bg-[#e84040] opacity-50" />
          <span className="text-[#e84040] text-3xl font-bold tracking-wide">{mockBrokerStats.signal}</span>
        </div>

        {/* Stats */}
        <div className="flex-1 space-y-2.5">
          {[
            { label: '主力進出 (張)', value: mockBrokerStats.netFlow, red: true },
            { label: '主力集中 (%)', value: mockBrokerStats.concentration, red: true },
            { label: '成交量 (張)', value: mockBrokerStats.volume, red: false },
            { label: '佔股本比重', value: mockBrokerStats.shareRatio, red: false },
            { label: '區間週轉率', value: mockBrokerStats.turnoverRate, red: false },
          ].map(({ label, value, red }) => (
            <div key={label} className="flex items-center justify-between">
              <span className="text-[#888] text-xs">{label}</span>
              <span className={clsx('text-sm font-medium', red ? 'text-[#e84040]' : 'text-white')}>
                {value}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Top 15 toggle */}
      <div className="flex rounded-[8px] overflow-hidden border border-[#333] mb-4">
        {brokerTopTabs.map((t, i) => (
          <button
            key={t}
            onClick={() => setBrokerTopTab(i)}
            className={clsx(
              'flex-1 py-2.5 text-sm font-medium',
              i === brokerTopTab ? 'bg-[#2a2a2a] text-white' : 'text-[#666]'
            )}
          >
            {t}
          </button>
        ))}
      </div>

      {/* Table header */}
      <div className="flex items-center px-1 mb-1 text-xs text-[#666]">
        <span className="flex-1">券商</span>
        <span className="w-20 text-right">{showBuy ? '買賣超 (張)' : '賣超 (張)'}</span>
        <span className="w-16 text-right">買均價</span>
        <span className="w-16 text-right">賣均價</span>
      </div>

      {/* Table rows */}
      <div className="divide-y divide-[#222]">
        {mockBrokerTop.map((row) => (
          <div key={row.name} className="flex items-center py-3 px-1 text-sm">
            <span className="flex-1 text-white">{row.name}</span>
            <span className={clsx('w-20 text-right font-medium', row.net > 0 ? 'text-[#e84040]' : 'text-[#2dba6a]')}>
              {row.net > 0 ? `+${row.net}` : row.net}
            </span>
            <span className="w-16 text-right text-[#aaa]">{row.buyAvg.toFixed(1)}</span>
            <span className="w-16 text-right text-[#aaa]">{row.sellAvg.toFixed(1)}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

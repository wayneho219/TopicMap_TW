import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import {
  ArrowLeft, Heart, Search, ChevronDown, Maximize2, Info,
} from 'lucide-react'
import { clsx } from 'clsx'
import {
  ComposedChart, BarChart, Line, Bar, XAxis, YAxis, CartesianGrid,
  ResponsiveContainer, ReferenceLine,
} from 'recharts'
import { mockChartData } from '../data/mock'
import { useStock } from '../hooks/useStock'
import { useWatchlist } from '../hooks/useWatchlist'
import { useIntraday, type IntradayPoint } from '../hooks/useIntraday'

const chartTabs = ['K線', '五檔', '價量', '明細', '券商分點', '指標', '籌碼']
const timeTabs = ['分時', '日', '週', '月']
const brokerTopTabs = ['買超 Top 15', '賣超 Top 15']

const mockOrderBook = {
  bids: [
    { vol: 96,  price: 224.25 },
    { vol: 121, price: 224.20 },
    { vol: 48,  price: 224.15 },
    { vol: 246, price: 224.10 },
    { vol: 261, price: 224.05 },
  ],
  asks: [
    { price: 224.30, vol: 1  },
    { price: 224.40, vol: 2  },
    { price: 224.45, vol: 12 },
    { price: 224.50, vol: 46 },
    { price: 224.55, vol: 35 },
  ],
}

const mockVolumePrice = [
  { price: 226.20, vol: 5   },
  { price: 226.10, vol: 115 },
  { price: 226.05, vol: 1   },
  { price: 226.00, vol: 389 },
  { price: 225.95, vol: 26  },
  { price: 225.90, vol: 170 },
  { price: 225.85, vol: 31  },
  { price: 225.80, vol: 192 },
  { price: 225.75, vol: 22  },
  { price: 225.70, vol: 114 },
  { price: 225.65, vol: 6   },
  { price: 225.60, vol: 93  },
]

const mockTradeDetail = [
  { time: '12:22:49', bid: 224.25, ask: 224.30, last: 224.25, vol: 1 },
  { time: '12:22:38', bid: 224.25, ask: 224.30, last: 224.25, vol: 1 },
  { time: '12:22:29', bid: 224.25, ask: 224.30, last: 224.25, vol: 1 },
  { time: '12:22:27', bid: 224.25, ask: 224.30, last: 224.25, vol: 1 },
  { time: '12:22:16', bid: 224.25, ask: 224.30, last: 224.25, vol: 1 },
  { time: '12:22:04', bid: 224.25, ask: 224.30, last: 224.25, vol: 1 },
  { time: '12:21:52', bid: 224.20, ask: 224.40, last: 224.30, vol: 1 },
  { time: '12:21:40', bid: 224.20, ask: 224.40, last: 224.25, vol: 2 },
  { time: '12:21:28', bid: 224.20, ask: 224.35, last: 224.20, vol: 1 },
  { time: '12:21:15', bid: 224.15, ask: 224.35, last: 224.20, vol: 3 },
]

const mockIndicators = [
  { label: '外資連3日買超',   active: true  },
  { label: '均線多頭排列',    active: true  },
  { label: '股價創5日新高',   active: true  },
  { label: '股價創20日新高',  active: true  },
  { label: '5日均量>1000張', active: false },
  { label: 'KD黃金交叉',     active: false },
  { label: '週MACD翻多',     active: true  },
]

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
  const { isWatched, toggle } = useWatchlist(id)
  const { data: intradayData, loading: intradayLoading } = useIntraday(id)

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
          <div className="flex items-center gap-3">
            <button onClick={toggle} className="active:opacity-60 p-1">
              <Heart
                size={20}
                className={isWatched ? 'text-[#e84040]' : 'text-[#888]'}
                fill={isWatched ? 'currentColor' : 'none'}
              />
            </button>
            <button onClick={() => navigate('/search')} className="text-[#888] active:opacity-60 p-1">
              <Search size={20} />
            </button>
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
        {chartTab === 0 && <KLineTab timeTab={timeTab} setTimeTab={setTimeTab} prevClose={stock.prevClose ?? stock.price} intradayData={intradayData} intradayLoading={intradayLoading} />}
        {chartTab === 1 && <OrderBookTab />}
        {chartTab === 2 && <VolumePriceTab />}
        {chartTab === 3 && <TradeDetailTab />}
        {chartTab === 4 && <BrokerTab brokerTopTab={brokerTopTab} setBrokerTopTab={setBrokerTopTab} />}
        {chartTab === 5 && <IndicatorsTab />}
        {chartTab === 6 && (
          <div className="flex items-center justify-center h-40 text-[#555] text-sm">
            籌碼（開發中）
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

/* ── 五檔 Tab ── */
function OrderBookTab() {
  const { bids, asks } = mockOrderBook
  const totalBid = bids.reduce((s, r) => s + r.vol, 0)
  const totalAsk = asks.reduce((s, r) => s + r.vol, 0)
  const bidPct = totalBid / (totalBid + totalAsk)

  return (
    <div className="pt-2">
      <div className="flex items-center px-4 py-2 text-[#666] text-xs border-b border-[#2e2e2e]">
        <span className="w-16 text-right">委買量</span>
        <span className="flex-1 text-center">買價</span>
        <span className="flex-1 text-center">賣價</span>
        <span className="w-16 pl-4">委賣量</span>
      </div>
      {bids.map((bid, i) => (
        <div key={i} className="flex items-center px-4 py-3.5 border-b border-[#1e1e1e]">
          <span className="w-16 text-right text-white text-sm">{bid.vol}</span>
          <span className="flex-1 text-center text-[#2dba6a] text-sm font-medium relative">
            {bid.price.toFixed(2)}
            {i === 0 && (
              <span className="absolute -bottom-[3px] left-1/2 -translate-x-1/2 w-14 h-[2px] bg-orange-400 rounded-full" />
            )}
          </span>
          <span className="flex-1 text-center text-[#2dba6a] text-sm font-medium">
            {asks[i].price.toFixed(2)}
          </span>
          <span className="w-16 pl-4 text-white text-sm">{asks[i].vol}</span>
        </div>
      ))}
      <div className="flex items-center px-4 py-3 gap-3">
        <span className="w-16 text-right text-white text-xs">小計 {totalBid}</span>
        <div className="flex-1 h-2 rounded-full overflow-hidden flex">
          <div className="bg-[#e84040]" style={{ width: `${bidPct * 100}%` }} />
          <div className="bg-[#2dba6a]" style={{ width: `${(1 - bidPct) * 100}%` }} />
        </div>
        <span className="w-16 pl-4 text-white text-xs">{totalAsk} 小計</span>
      </div>
    </div>
  )
}

/* ── 價量 Tab ── */
function VolumePriceTab() {
  const maxVol = Math.max(...mockVolumePrice.map((r) => r.vol))
  return (
    <div className="pt-2">
      <div className="flex items-center px-4 py-2 text-[#666] text-xs border-b border-[#2e2e2e]">
        <span className="w-20 text-right">價</span>
        <span className="flex-1 mx-3" />
        <span className="w-12 text-right">量</span>
      </div>
      {mockVolumePrice.map((row, i) => (
        <div key={i} className="flex items-center px-4 py-2 border-b border-[#1e1e1e]">
          <span className="w-20 text-right text-[#2dba6a] text-sm font-medium">
            {row.price.toFixed(2)}
          </span>
          <div className="flex-1 mx-3 h-3 rounded-sm overflow-hidden bg-[#222]">
            <div
              className="h-full bg-orange-400 rounded-sm"
              style={{ width: `${(row.vol / maxVol) * 100}%` }}
            />
          </div>
          <span className="w-12 text-right text-white text-sm">{row.vol}</span>
        </div>
      ))}
    </div>
  )
}

/* ── 明細 Tab ── */
function TradeDetailTab() {
  return (
    <div className="pt-2">
      <div className="flex items-center px-4 py-2 text-[#666] text-xs border-b border-[#2e2e2e]">
        <span className="w-20">時間</span>
        <span className="flex-1 text-right">買價</span>
        <span className="flex-1 text-right">賣價</span>
        <span className="flex-1 text-right">成交</span>
        <span className="w-10 text-right">單量</span>
      </div>
      {mockTradeDetail.map((row, i) => (
        <div key={i} className="flex items-center px-4 py-3 border-b border-[#1e1e1e] text-sm">
          <span className="w-20 text-[#888]">{row.time}</span>
          <span className="flex-1 text-right text-[#2dba6a]">{row.bid.toFixed(2)}</span>
          <span className="flex-1 text-right text-[#2dba6a]">{row.ask.toFixed(2)}</span>
          <span className="flex-1 text-right text-[#2dba6a]">{row.last.toFixed(2)}</span>
          <span className="w-10 text-right text-white">{row.vol}</span>
        </div>
      ))}
    </div>
  )
}

/* ── 指標 Tab ── */
function IndicatorsTab() {
  const activeCount = mockIndicators.filter((i) => i.active).length
  return (
    <div className="pt-3 px-4">
      <div className="text-orange-400 text-base font-semibold mb-1">
        {activeCount} 個變動
      </div>
      <div className="divide-y divide-[#2e2e2e]">
        {mockIndicators.map((item) => (
          <div key={item.label} className="flex items-center gap-3 py-4">
            <span
              className="w-2.5 h-2.5 rounded-full flex-shrink-0"
              style={{ background: item.active ? '#e84040' : '#555' }}
            />
            <span className="text-white text-sm">{item.label}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

/* ── K線 Tab ── */
function KLineTab({
  timeTab, setTimeTab, prevClose, intradayData, intradayLoading,
}: {
  timeTab: number
  setTimeTab: (i: number) => void
  prevClose: number
  intradayData: IntradayPoint[]
  intradayLoading: boolean
}) {
  const chartData = timeTab === 0
    ? (intradayData.length > 0 ? intradayData : mockChartData)
    : mockChartData

  const prices = chartData.map((d) => d.price)
  const minP = prices.length ? Math.min(...prices) : prevClose * 0.95
  const maxP = prices.length ? Math.max(...prices) : prevClose * 1.05
  const pad = Math.max(maxP - minP, prevClose * 0.005) * 0.3
  const priceDomain: [number, number] = [
    Math.floor((minP - pad) * 100) / 100,
    Math.ceil((maxP + pad) * 100) / 100,
  ]
  const maxVol = Math.max(...chartData.map((d) => d.volume || 0), 1)
  const volDomain: [number, number] = [0, maxVol * 4]
  const pctTickFormatter = (v: number) => {
    const pct = (v - prevClose) / prevClose * 100
    return `${pct >= 0 ? '+' : ''}${pct.toFixed(1)}%`
  }

  const last = chartData[chartData.length - 1]
  const isUp = last ? last.pct >= 0 : true

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

      {timeTab === 0 && intradayLoading ? (
        <div className="flex items-center justify-center" style={{ height: 280 }}>
          <div className="w-6 h-6 rounded-full border-2 border-[#2dba6a] border-t-transparent animate-spin" />
        </div>
      ) : (
        <>
          {last && (
            <div className="flex items-center gap-3 px-3 pb-1 text-xs">
              <span className="text-[#888]">{last.time}</span>
              <span className="text-[#aaa]">價：<span className={isUp ? 'text-[#e84040]' : 'text-[#2dba6a]'}>{last.price.toFixed(2)}</span></span>
              <span className={isUp ? 'text-[#e84040]' : 'text-[#2dba6a]'}>
                {isUp ? '▲' : '▼'}{Math.abs(last.price - prevClose).toFixed(2)}({Math.abs(last.pct).toFixed(2)}%)
              </span>
              <span className="text-[#aaa]">量：<span className="text-[#2dba6a]">{Math.round(last.volume / 1000)}</span></span>
            </div>
          )}
          <div className="px-1">
            {/* 價格線 */}
            <ResponsiveContainer width="100%" height={200}>
              <ComposedChart data={chartData} margin={{ top: 4, right: 44, left: 4, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2a" vertical={false} />
                <XAxis dataKey="time" hide />
                <YAxis orientation="left" domain={priceDomain} tick={{ fill: '#666', fontSize: 10 }} tickLine={false} axisLine={false} tickCount={5} tickFormatter={(v) => v.toFixed(0)} width={44} />
                <YAxis yAxisId="pct" orientation="right" domain={priceDomain} tick={{ fill: '#666', fontSize: 10 }} tickLine={false} axisLine={false} tickCount={5} tickFormatter={pctTickFormatter} width={44} />
                <ReferenceLine y={prevClose} stroke="#555" strokeDasharray="4 2" />
                <Line yAxisId="pct" dataKey="price" stroke="transparent" dot={false} />
                <Line type="monotone" dataKey="price" stroke="#e84040" strokeWidth={1.5} dot={false} activeDot={{ r: 3, fill: '#e84040' }} />
              </ComposedChart>
            </ResponsiveContainer>
            {/* 成交量 */}
            <ResponsiveContainer width="100%" height={60}>
              <BarChart data={chartData} margin={{ top: 0, right: 44, left: 4, bottom: 0 }}>
                <XAxis dataKey="time" tick={{ fill: '#666', fontSize: 10 }} tickLine={false} axisLine={false} interval={Math.floor(chartData.length / 5)} />
                <YAxis hide domain={[0, maxVol]} />
                <Bar dataKey="volume" fill="#c8a020" opacity={0.8} maxBarSize={4} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </>
      )}
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

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft, Settings, Search, Info, Minus, Plus, ChevronDown } from 'lucide-react'
import { clsx } from 'clsx'

// TODO: replace with GET /api/stocks/:id/order-info
const mockSelectedStock = {
  id: '006208',
  name: '富邦台 50',
  price: 226.80,
  change: 4.80,
  changePercent: 2.16,
}

// TODO: replace with GET /api/stocks/:id/five-tier
const mockFiveTier = {
  buy:  [{ price: 226.65, qty: 3 }, { price: 226.50, qty: 8 }, { price: 226.45, qty: 1 }, { price: 226.40, qty: 9 }, { price: 226.35, qty: 2 }],
  sell: [{ price: 226.80, qty: 17 }, { price: 226.85, qty: 62 }, { price: 226.90, qty: 41 }, { price: 226.95, qty: 36 }, { price: 227.00, qty: 72 }],
}

const orderTypeTabs = ['現股', '沖賣', '融資', '融券']
const priceTypeTabs  = ['限價', '市價', '漲停', '跌停', '平盤']
const infoTabs       = ['五檔價量', '庫存資訊', '銀行餘額']

/* ── 單格 Toggle 按鈕 ── */
function ToggleBtn({
  label, active, onClick, first, last,
}: { label: string; active: boolean; onClick: () => void; first?: boolean; last?: boolean }) {
  return (
    <button
      onClick={onClick}
      className={clsx(
        'flex-1 py-2.5 text-sm font-medium',
        !first && 'border-l border-[#3a3a3a]',
        active ? 'bg-[#2dba6a] text-white' : 'bg-[#2a2a2a] text-[#666]',
        first && 'rounded-l-[8px]',
        last  && 'rounded-r-[8px]',
      )}
    >
      {label}
    </button>
  )
}

/* ── 數量 / 價格 Stepper ── */
function Stepper({
  value, unit, highlight, onDec, onInc,
}: { value: string; unit?: string; highlight?: boolean; onDec: () => void; onInc: () => void }) {
  return (
    <div className="flex items-center bg-[#2a2a2a] rounded-[8px] border border-[#3a3a3a] overflow-hidden">
      <button onClick={onDec} className="px-3.5 py-3 active:bg-[#333]">
        <Minus size={16} className={highlight ? 'text-[#e8a040]' : 'text-[#666]'} />
      </button>
      <div className={clsx('flex-1 text-center text-sm font-medium', highlight ? 'text-[#e84040]' : 'text-white')}>
        {value}{unit && <span className="text-[#888] text-xs ml-1">{unit}</span>}
      </div>
      <button onClick={onInc} className="px-3.5 py-3 active:bg-[#333]">
        <Plus size={16} className={highlight ? 'text-[#e8a040]' : 'text-[#666]'} />
      </button>
    </div>
  )
}

export function OrderPage() {
  const navigate = useNavigate()
  const [hasStock] = useState(true)
  const [shareSize, setShareSize]   = useState(0)
  const [session, setSession]       = useState(0)
  const [orderType, setOrderType]   = useState(0)
  const [priceType, setPriceType]   = useState(0)
  const [infoTab, setInfoTab]       = useState(0)
  const [price, setPrice]           = useState(mockSelectedStock.price.toFixed(2))
  const [qty, setQty]               = useState('1')
  const [showConfirm, setShowConfirm] = useState(false)
  const [confirmType, setConfirmType] = useState<'buy' | 'sell'>('buy')

  const buyTotal  = mockFiveTier.buy.reduce((s, r) => s + r.qty, 0)
  const sellTotal = mockFiveTier.sell.reduce((s, r) => s + r.qty, 0)
  const totalBar  = buyTotal + sellTotal
  const buyPct    = (buyTotal / totalBar) * 100

  const estimatedAmt = hasStock
    ? (parseFloat(price) * parseInt(qty) * 1000).toLocaleString()
    : '-'

  return (
    <div className="flex flex-col bg-[#111111] h-screen">

      {/* ── 釘住頂部 ── */}
      <div className="flex-shrink-0 bg-[#111111] z-20">
        {/* Top Bar */}
        <div className="flex items-center justify-between px-4 pt-14 pb-3">
          <button onClick={() => navigate(-1)} className="text-[#aaa] active:opacity-60 p-1">
            <ArrowLeft size={20} />
          </button>
          <span className="text-white text-base font-medium">下單</span>
          <div className="flex items-center gap-3">
            <Settings size={18} className="text-[#888]" />
            <button className="text-[#2dba6a] text-sm font-medium">看委託</button>
          </div>
        </div>

        {/* Account Row */}
        <div className="flex gap-2 px-3 pb-3">
          <button className="flex items-center gap-1.5 bg-[#2a2a2a] rounded-[8px] px-3 py-2.5 text-white text-sm border border-[#3a3a3a]">
            台股 <ChevronDown size={13} className="text-[#666]" />
          </button>
          <div className="flex-1 bg-[#2a2a2a] rounded-[8px] px-3 py-2.5 border border-[#3a3a3a]">
            <span className="text-[#888] text-sm">台北總公司 9822896</span>
          </div>
        </div>
      </div>

      {/* ── 捲動內容區 ── */}
      <div className="flex-1 overflow-y-auto pb-24 px-3">

        {/* ── 已選股票資訊 / 股票搜尋 ── */}
        {hasStock ? (
          <div className="py-3">
            <div className="flex items-start justify-between">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-white text-base font-medium">{mockSelectedStock.name}</span>
                  <span className="text-[#666] text-sm">{mockSelectedStock.id}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-[#e84040] text-2xl font-bold">{mockSelectedStock.price.toFixed(2)}</span>
                  <span className="text-[#e84040] text-sm">
                    ▲{mockSelectedStock.change.toFixed(2)} ▲{mockSelectedStock.changePercent.toFixed(2)}%
                  </span>
                </div>
              </div>
              <button className="flex items-center gap-1.5 bg-[#2a2a2a] border border-[#3a3a3a] text-[#2dba6a] text-sm px-3 py-1.5 rounded-[8px] mt-1">
                <Search size={14} />搜尋
              </button>
            </div>
          </div>
        ) : (
          <div className="bg-[#1e1e1e] rounded-[10px] p-3 mb-3">
            <div className="flex items-start justify-between">
              <div>
                <div className="text-white text-sm font-medium">股票搜尋</div>
                <div className="text-[#666] text-xs mt-0.5">輸入股票代號或名稱</div>
              </div>
              <button className="flex items-center gap-1.5 bg-[#2a2a2a] border border-[#3a3a3a] text-[#2dba6a] text-sm px-3 py-1.5 rounded-[8px]">
                <Search size={14} />搜尋
              </button>
            </div>
          </div>
        )}

        {/* ── Toggle Row 1: [整張|零股] + [盤中|盤後] ── */}
        <div className="flex gap-2 mb-2">
          <div className="flex flex-1 rounded-[8px] overflow-hidden border border-[#3a3a3a]">
            <ToggleBtn label="整張" active={shareSize === 0} onClick={() => setShareSize(0)} first />
            <ToggleBtn label="零股" active={shareSize === 1} onClick={() => setShareSize(1)} last />
          </div>
          <div className="flex flex-1 rounded-[8px] overflow-hidden border border-[#3a3a3a]">
            <ToggleBtn label="盤中" active={session === 0} onClick={() => setSession(0)} first />
            <ToggleBtn label="盤後" active={session === 1} onClick={() => setSession(1)} last />
          </div>
        </div>

        {/* ── Toggle Row 2: 現股 沖賣 融資 融券 | ROD▼ ── */}
        <div className="flex gap-2 mb-1">
          <div className="flex flex-1 rounded-[8px] overflow-hidden border border-[#3a3a3a]">
            {orderTypeTabs.map((t, i) => (
              <ToggleBtn
                key={t}
                label={t}
                active={orderType === i}
                onClick={() => setOrderType(i)}
                first={i === 0}
                last={i === orderTypeTabs.length - 1}
              />
            ))}
          </div>
          <button className="flex items-center gap-1 bg-[#2a2a2a] border border-[#3a3a3a] rounded-[8px] px-3 text-white text-sm font-medium">
            ROD <ChevronDown size={13} className="text-[#888]" />
          </button>
        </div>

        {/* Info Line */}
        {hasStock && (
          <div className="text-[#888] text-xs mb-2 leading-relaxed">
            資：無限 (60%)｜券：0(90%) 可買賣現沖，
            <button className="text-[#2dba6a] underline">查看詳情</button>
          </div>
        )}

        {/* ── Toggle Row 3: 限價 市價 漲停 跌停 平盤 ── */}
        <div className="flex rounded-[8px] overflow-hidden border border-[#3a3a3a] mb-3">
          {priceTypeTabs.map((t, i) => (
            <ToggleBtn
              key={t}
              label={t}
              active={priceType === i}
              onClick={() => setPriceType(i)}
              first={i === 0}
              last={i === priceTypeTabs.length - 1}
            />
          ))}
        </div>

        {/* ── 價格 / 數量 Steppers ── */}
        <div className="flex gap-2 mb-1">
          <div className="flex-1">
            <Stepper
              value={price}
              highlight
              onDec={() => setPrice(p => (parseFloat(p) - 0.05).toFixed(2))}
              onInc={() => setPrice(p => (parseFloat(p) + 0.05).toFixed(2))}
            />
          </div>
          <div className="flex-1">
            <Stepper
              value={qty}
              unit="張"
              onDec={() => setQty(q => String(Math.max(1, parseInt(q) - 1)))}
              onInc={() => setQty(q => String(parseInt(q) + 1))}
            />
          </div>
        </div>
        <div className="text-right text-[#555] text-xs mb-3">1 張 = 1,000 股</div>

        {/* ── Info Tabs ── */}
        <div className="flex border-b border-[#2e2e2e] mb-2">
          {infoTabs.map((t, i) => (
            <button
              key={t}
              onClick={() => setInfoTab(i)}
              className={clsx(
                'flex-1 pb-2 text-sm font-medium relative',
                i === infoTab ? 'text-[#2dba6a]' : 'text-[#555]'
              )}
            >
              {t}
              {i === infoTab && (
                <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-[#2dba6a] rounded-full" />
              )}
            </button>
          ))}
        </div>

        {/* ── 五檔價量 ── */}
        {infoTab === 0 && (
          <div>
            <div className="flex items-center py-1.5 text-xs text-[#555]">
              <span className="flex-1 text-left">委買量</span>
              <span className="w-24 text-right">價格</span>
              <span className="w-24 text-right">價格</span>
              <span className="flex-1 text-right">委賣量</span>
            </div>

            {mockFiveTier.buy.map((buyRow, i) => {
              const sellRow = mockFiveTier.sell[i]
              const isCurrentPrice = sellRow.price === mockSelectedStock.price
              return (
                <div key={i} className="flex items-center py-2.5 text-sm border-t border-[#1e1e1e]">
                  <span className="flex-1 text-left text-white">{buyRow.qty}</span>
                  <span className="w-24 text-right text-[#e84040]">{buyRow.price.toFixed(2)}</span>
                  <div className="w-24 text-right">
                    <span className="text-[#e84040]">{sellRow.price.toFixed(2)}</span>
                    {isCurrentPrice && (
                      <div className="h-0.5 bg-[#e8a040] rounded-full mt-0.5 ml-auto w-12" />
                    )}
                  </div>
                  <span className="flex-1 text-right text-white">{sellRow.qty}</span>
                </div>
              )
            })}

            {/* Buy / Sell ratio bar */}
            <div className="flex items-center gap-2 py-2.5 border-t border-[#1e1e1e]">
              <span className="text-[#e84040] text-sm font-medium w-6">{buyTotal}</span>
              <div className="flex-1 h-3 rounded-full overflow-hidden flex bg-[#2dba6a]">
                <div
                  className="h-full bg-[#e84040] rounded-full"
                  style={{ width: `${buyPct}%` }}
                />
              </div>
              <span className="text-[#2dba6a] text-sm font-medium w-8 text-right">{sellTotal}</span>
            </div>
          </div>
        )}

        {infoTab !== 0 && (
          <div className="flex items-center justify-center h-24 text-[#555] text-sm">
            {infoTabs[infoTab]}（開發中）
          </div>
        )}

        {/* ── 預估金額 ── */}
        <div className="flex items-center justify-between py-3 border-t border-[#2e2e2e]">
          <div className="flex items-center gap-1.5">
            <span className="text-[#888] text-xs">預估金額</span>
            <span className="text-[#555] text-[10px]">不含手續費與交易稅</span>
            <Info size={12} className="text-[#555]" />
          </div>
          <span className={clsx('text-sm font-medium', hasStock ? 'text-white' : 'text-[#888]')}>
            {estimatedAmt}
          </span>
        </div>
      </div>

      {/* ── 固定底部按鈕 ── */}
      <div className="fixed bottom-0 left-1/2 -translate-x-1/2 w-full max-w-[430px] flex gap-2 px-3 py-3 bg-[#111111] border-t border-[#2e2e2e] z-40">
        <button
          onClick={() => { if (hasStock) { setConfirmType('buy'); setShowConfirm(true) } }}
          className={clsx('flex-1 py-3.5 rounded-[10px] font-medium text-sm', hasStock ? 'bg-[#e84040] text-white active:opacity-80' : 'bg-[#2a2a2a] text-[#555]')}
        >買進</button>
        <button
          onClick={() => { if (hasStock) { setConfirmType('sell'); setShowConfirm(true) } }}
          className={clsx('flex-1 py-3.5 rounded-[10px] font-medium text-sm', hasStock ? 'bg-[#2dba6a] text-white active:opacity-80' : 'bg-[#2a2a2a] text-[#555]')}
        >賣出</button>
      </div>

      {/* ── 買進/賣出確認 Modal ── */}
      {showConfirm && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center px-4"
          style={{ background: 'rgba(0,0,0,0.6)' }}
          onClick={() => setShowConfirm(false)}
        >
          <div
            className="w-full max-w-[360px] bg-[#2a2a2a] rounded-[16px] overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Title */}
            <div className="py-4 text-center border-b border-[#3a3a3a]">
              <span className={clsx('text-base font-semibold', confirmType === 'buy' ? 'text-[#e84040]' : 'text-[#2dba6a]')}>
                {confirmType === 'buy' ? '整張買進' : '整張賣出'}
              </span>
            </div>

            {/* Order Summary Card */}
            <div className="mx-4 mt-4 bg-[#1e1e1e] rounded-[12px] p-4 space-y-2">
              <div className="text-white text-sm font-medium text-center mb-3">
                {mockSelectedStock.id} {mockSelectedStock.name}
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-[#888]">委託量</span>
                <span className="text-white font-medium">{parseInt(qty) * 1000} 股</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-[#888]">委託價</span>
                <span className="text-white font-medium">{parseFloat(price).toFixed(2)} 元</span>
              </div>
              <div className="pt-2 border-t border-[#2e2e2e]">
                <div className="flex justify-between text-sm mb-0.5">
                  <span className="text-[#888]">預估金額</span>
                  <span className="text-white font-bold text-base">{estimatedAmt} 元</span>
                </div>
                <div className="text-[#555] text-xs text-right">不含手續費及交易稅</div>
              </div>
            </div>

            {/* Details */}
            <div className="px-4 py-3 space-y-2">
              {[
                ['交易方式', '現股買進盤中整張'],
                ['委託條件', 'ROD - 當日有效單'],
                ['下單帳號', '證券-台北總公司 9822896'],
              ].map(([k, v]) => (
                <div key={k} className="flex gap-3 text-sm">
                  <span className="text-[#888] flex-shrink-0">{k}</span>
                  <span className="text-white">{v}</span>
                </div>
              ))}
            </div>

            {/* Action Buttons */}
            <div className="flex gap-2 px-4 pb-4">
              <button
                onClick={() => setShowConfirm(false)}
                className="flex-1 py-3 rounded-[10px] border border-[#e84040] text-[#e84040] text-sm font-medium"
              >取消</button>
              <button
                onClick={() => setShowConfirm(false)}
                className={clsx(
                  'flex-1 py-3 rounded-[10px] text-white text-sm font-semibold',
                  confirmType === 'buy' ? 'bg-[#e84040]' : 'bg-[#2dba6a]'
                )}
              >{confirmType === 'buy' ? '確定買進' : '確定賣出'}</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

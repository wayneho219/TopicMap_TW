import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft, Info, HelpCircle } from 'lucide-react'
import { clsx } from 'clsx'


export function RecurringSubscribeTWPage() {
  const navigate = useNavigate()
  const [payMethod, setPayMethod]     = useState(0)   // 0=現金 1=小樹點
  const [dividendOn, setDividendOn]   = useState(false)
  const [lowCheck, setLowCheck]       = useState(false)
  const [highCheck, setHighCheck]     = useState(false)
  const [lowPct, setLowPct]           = useState(0)
  const [highPct, setHighPct]         = useState(0)
  const [lowAmt, setLowAmt]           = useState(0)
  const [highAmt, setHighAmt]         = useState(0)

  return (
    <div className="flex flex-col h-screen bg-[#f5f5f5]">

      {/* ── 釘住頂部 ── */}
      <div className="flex-shrink-0 bg-white z-20 border-b border-[#eee]">
        <div className="flex items-center justify-between px-4 pt-14 pb-3">
          <button onClick={() => navigate(-1)} className="text-[#888] active:opacity-60 p-1">
            <ArrowLeft size={20} />
          </button>
          <span className="text-[#1a1a1a] text-base font-semibold">申購定期定額</span>
          <div className="w-8" />
        </div>
      </div>

      {/* ── 捲動內容 ── */}
      <div className="flex-1 overflow-y-auto pb-24">

        {/* 股票資訊卡 */}
        <div className="bg-white mx-3 mt-3 rounded-[12px] border border-[#eee] px-4 py-4">
          <div className="text-center mb-3">
            <div className="text-[#1a1a1a] text-base font-semibold">(2301) 光寶科</div>
            <div className="text-[#888] text-xs mt-0.5">收盤價 (05/07)</div>
            <div className="text-[#1a1a1a] text-3xl font-bold mt-1">203.50</div>
          </div>
          <div className="flex border-t border-[#f0f0f0] pt-3">
            {[
              { label: 'EPS', value: '1.66', sub: '(2026年Q1)' },
              { label: '殖利率', value: '2.92%', sub: '(05/05)' },
              { label: '股價淨值比', value: '4.40', sub: '(05/05)' },
            ].map((item) => (
              <div key={item.label} className="flex-1 text-center">
                <div className="text-[#888] text-xs">{item.label}</div>
                <div className="text-[#1a1a1a] text-base font-bold mt-0.5">{item.value}</div>
                <div className="text-[#aaa] text-[10px]">{item.sub}</div>
              </div>
            ))}
          </div>
        </div>

        {/* 帳號 */}
        <div className="bg-white mx-3 mt-2 rounded-[12px] border border-[#eee] px-4 py-3">
          <span className="text-[#444] text-sm">證券-台北總公司 9822896</span>
        </div>

        {/* 申購表單 */}
        <div className="bg-white mx-3 mt-2 rounded-[12px] border border-[#eee] divide-y divide-[#f0f0f0]">
          {/* 申購方式 */}
          <div className="flex items-center justify-between px-4 py-3.5">
            <span className="text-[#1a1a1a] text-sm">申購方式</span>
            <div className="flex items-center gap-4">
              {['現金申購', '小樹點申購'].map((m, i) => (
                <button key={m} onClick={() => setPayMethod(i)} className="flex items-center gap-1.5">
                  <div className={clsx(
                    'w-4 h-4 rounded-full border-2 flex items-center justify-center',
                    i === payMethod ? 'border-[#2dba6a]' : 'border-[#ccc]'
                  )}>
                    {i === payMethod && <div className="w-2 h-2 rounded-full bg-[#2dba6a]" />}
                  </div>
                  <span className="text-[#444] text-sm">{m}</span>
                </button>
              ))}
            </div>
          </div>
          {/* 申購金額 */}
          <div className="flex items-center justify-between px-4 py-3.5">
            <span className="text-[#1a1a1a] text-sm">申購金額</span>
            <span className="text-[#aaa] text-xs">以百元為單位，最低100元</span>
          </div>
          {/* 每月交易日 */}
          <div className="flex items-center justify-between px-4 py-3.5">
            <span className="text-[#1a1a1a] text-sm">每月交易日</span>
            <button className="flex items-center gap-1 text-[#2dba6a] text-sm">
              請選擇日期 <span className="text-[#aaa]">›</span>
            </button>
          </div>
          {/* 手續費 */}
          <div className="flex items-center justify-between px-4 py-3.5">
            <div className="flex items-center gap-1.5">
              <span className="text-[#1a1a1a] text-sm">手續費</span>
              <Info size={13} className="text-[#aaa]" />
            </div>
            <span className="text-[#1a1a1a] text-sm font-medium">1 元</span>
          </div>
        </div>

        {/* 股息再投資 */}
        <div className="bg-white mx-3 mt-2 rounded-[12px] border border-[#eee] px-4 py-4">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-1.5">
              <span className="text-[#1a1a1a] text-sm font-medium">股息再投資</span>
              <Info size={13} className="text-[#aaa]" />
            </div>
            <div className="flex items-center gap-2">
              <span className="text-[#aaa] text-xs">{dividendOn ? '已開啟' : '未開啟'}</span>
              <button
                onClick={() => setDividendOn(v => !v)}
                className={clsx(
                  'w-11 h-6 rounded-full transition-colors relative',
                  dividendOn ? 'bg-[#2dba6a]' : 'bg-[#ddd]'
                )}
              >
                <span className={clsx(
                  'absolute top-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform',
                  dividendOn ? 'translate-x-5' : 'translate-x-0.5'
                )} />
              </button>
            </div>
          </div>
          <p className="text-[#aaa] text-xs leading-relaxed">
            股票每次現金股息發放日後第 2 個交易日，依股息金額自動買進交易。
          </p>
        </div>

        {/* 智慧加減碼條件 */}
        <div className="mt-2">
          <div className="flex items-center justify-between px-4 py-3 bg-white border-y border-[#eee]">
            <span className="text-[#1a1a1a] text-sm font-medium">智慧加減碼條件</span>
            <button className="flex items-center gap-1 text-[#888] text-xs">
              什麼是智慧加減碼 <HelpCircle size={13} />
            </button>
          </div>

          <div className="bg-white mx-0 px-4 py-3 border-b border-[#eee]">
            {/* 價格比較 */}
            <div className="flex items-center justify-between mb-3 pb-3 border-b border-[#f0f0f0]">
              <span className="text-[#888] text-sm">收盤價 <span className="text-[#1a1a1a] font-medium">203.50</span></span>
              <span className="text-[#888] text-sm">季均價(05/07) <span className="text-[#1a1a1a] font-medium">163.38</span></span>
            </div>

            {/* 逢低 */}
            <SmartAdjustBlock
              label="逢低調整申購金額"
              colorLabel="下跌幅度："
              colorClass="text-[#2dba6a]"
              checked={lowCheck}
              onCheck={setLowCheck}
              pct={lowPct}
              onPct={setLowPct}
              amt={lowAmt}
              onAmtDec={() => setLowAmt(a => Math.max(0, a - 100))}
              onAmtInc={() => setLowAmt(a => a + 100)}
            />

            {/* 逢高 */}
            <div className="mt-4">
              <SmartAdjustBlock
                label="逢高調整申購金額"
                colorLabel="上漲幅度："
                colorClass="text-[#e84040]"
                checked={highCheck}
                onCheck={setHighCheck}
                pct={highPct}
                onPct={setHighPct}
                amt={highAmt}
                onAmtDec={() => setHighAmt(a => Math.max(0, a - 100))}
                onAmtInc={() => setHighAmt(a => a + 100)}
              />
            </div>
          </div>
        </div>
      </div>

      {/* ── 固定底部 ── */}
      <div className="fixed bottom-0 left-1/2 -translate-x-1/2 w-full max-w-[430px] flex gap-2 px-3 py-3 bg-white border-t border-[#eee] z-40">
        <button className="flex-1 py-3.5 rounded-[10px] border border-[#2dba6a] text-[#2dba6a] text-sm font-medium active:bg-[#f0faf5]">
          報酬率試算
        </button>
        <button className="flex-1 py-3.5 rounded-[10px] bg-[#2dba6a] text-white text-sm font-semibold active:opacity-80">
          申購
        </button>
      </div>
    </div>
  )
}

function SmartAdjustBlock({
  label, colorLabel, colorClass, checked, onCheck, pct, onPct, amt, onAmtDec, onAmtInc,
}: {
  label: string; colorLabel: string; colorClass: string
  checked: boolean; onCheck: (v: boolean) => void
  pct: number; onPct: (v: number) => void
  amt: number; onAmtDec: () => void; onAmtInc: () => void
}) {
  return (
    <div>
      <button onClick={() => onCheck(!checked)} className="flex items-center gap-2 mb-3">
        <div className={clsx(
          'w-4 h-4 rounded border-2 flex items-center justify-center',
          checked ? 'border-[#2dba6a] bg-[#2dba6a]' : 'border-[#ccc]'
        )}>
          {checked && <span className="text-white text-[10px] font-bold">✓</span>}
        </div>
        <span className="text-[#1a1a1a] text-sm">{label}</span>
      </button>
      <div className="text-[#888] text-xs mb-2">當「前一日收盤價」與「季均價」相比，</div>
      <div className={clsx('text-xs font-medium mb-1.5', colorClass)}>{colorLabel}</div>
      <div className="flex rounded-[8px] overflow-hidden bg-[#f5f5f5] mb-3">
        {['>0%', '≥5%', '≥10%', '≥15%'].map((p, i) => (
          <button
            key={p}
            onClick={() => onPct(i)}
            className={clsx(
              'flex-1 py-2 text-xs font-medium',
              i !== 0 && 'border-l border-[#e0e0e0]',
              i === pct ? 'bg-white text-[#1a1a1a] shadow-sm' : 'text-[#888]'
            )}
          >
            {p}
          </button>
        ))}
      </div>
      <div className="text-[#888] text-xs mb-1.5">我要將申購金額調整為：</div>
      <div className="flex items-center border border-[#ddd] rounded-[8px] overflow-hidden">
        <button onClick={onAmtDec} className="px-3 py-2.5 text-[#888] active:bg-[#f5f5f5]">—</button>
        <div className="flex-1 text-center text-[#888] text-sm">{amt > 0 ? amt : '--'}</div>
        <button onClick={onAmtInc} className="px-3 py-2.5 text-[#888] active:bg-[#f5f5f5]">+</button>
      </div>
    </div>
  )
}

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft, HelpCircle, Info } from 'lucide-react'
import { clsx } from 'clsx'

const tradeDays = [5, 15, 25]
const returnYears = ['1年', '2年', '3年']

export function RecurringSubscribeUSPage() {
  const navigate = useNavigate()
  const [tab, setTab]         = useState(0)   // 0=定額 1=定股
  const [amount, setAmount]   = useState(10)
  const [days, setDays]       = useState<number[]>([])
  const [year, setYear]       = useState(0)

  const fee = 0.1
  const total = amount + fee

  return (
    <div className="flex flex-col h-screen bg-[#f5f5f5]">

      {/* ── 釘住頂部（綠色漸層） ── */}
      <div
        className="flex-shrink-0 z-20"
        style={{ background: 'linear-gradient(180deg, #1dba6a 0%, #2dba6a 100%)' }}
      >
        <div className="flex items-center justify-between px-4 pt-14 pb-3">
          <button onClick={() => navigate(-1)} className="text-white active:opacity-70 p-1">
            <ArrowLeft size={20} />
          </button>
          <span className="text-white text-base font-semibold">我要申購</span>
          <div className="w-8" />
        </div>
        <div className="text-center pb-4">
          <div className="text-white text-lg font-bold">蘋果</div>
          <div className="text-white/80 text-sm">Apple Inc</div>
        </div>
      </div>

      {/* ── 捲動內容 ── */}
      <div className="flex-1 overflow-y-auto pb-24">

        {/* Price Card */}
        <div className="bg-white mx-3 mt-3 rounded-[12px] overflow-hidden border border-[#eee]">
          <div className="flex divide-x divide-[#eee]">
            <div className="flex-1 p-4">
              <div className="text-[#888] text-xs mb-1">收盤價格 (USD)</div>
              <div className="text-[#1a1a1a] text-xl font-bold">287.51</div>
            </div>
            <div className="flex-1 p-4">
              <div className="text-[#888] text-xs mb-1">漲跌幅 (月)</div>
              <div className="text-[#e84040] text-xl font-bold">▲ 11.07%</div>
            </div>
          </div>
        </div>

        {/* Account Card */}
        <div className="bg-white mx-3 mt-2 rounded-[12px] px-4 py-3 border border-[#eee] flex items-center gap-2">
          <span className="bg-[#2dba6a] text-white text-[10px] font-bold px-1.5 py-0.5 rounded-full">外幣</span>
          <span className="text-[#444] text-sm">複委託-台北總公司 9835205</span>
        </div>

        {/* 定額 / 定股 Tab */}
        <div className="bg-white mx-3 mt-2 rounded-[12px] border border-[#eee] overflow-hidden">
          <div className="flex border-b border-[#eee]">
            {['我要定額', '我要定股'].map((t, i) => (
              <button
                key={t}
                onClick={() => setTab(i)}
                className={clsx(
                  'flex-1 py-3 text-sm font-medium relative',
                  i === tab ? 'text-[#1a1a1a]' : 'text-[#aaa]'
                )}
              >
                {t}
                {i === tab && (
                  <span className="absolute bottom-0 left-1/4 right-1/4 h-0.5 bg-[#ff9500] rounded-full" />
                )}
              </button>
            ))}
          </div>

          <div className="px-4 pt-4 pb-3 space-y-4">
            {/* 申購金額 */}
            <div>
              <div className="flex items-start justify-between mb-1">
                <div>
                  <div className="text-[#1a1a1a] text-sm font-medium">申購金額 (USD)</div>
                  <div className="text-[#aaa] text-xs mt-0.5">最低10元，10元為單位</div>
                </div>
                <div className="flex items-center border border-[#ddd] rounded-[8px] overflow-hidden">
                  <button
                    onClick={() => setAmount(a => Math.max(10, a - 10))}
                    className="px-3 py-2 text-[#888] active:bg-[#f5f5f5]"
                  >—</button>
                  <span className="px-4 text-[#1a1a1a] text-sm font-medium min-w-[40px] text-center">{amount}</span>
                  <button
                    onClick={() => setAmount(a => a + 10)}
                    className="px-3 py-2 text-[#2dba6a] font-bold active:bg-[#f5f5f5]"
                  >+</button>
                </div>
              </div>
            </div>

            {/* 估計每次圈存 */}
            <div className="flex items-start justify-between py-3 border-t border-[#f0f0f0]">
              <div>
                <div className="text-[#1a1a1a] text-sm">估計每次圈存金額</div>
                <div className="flex items-center gap-1 mt-0.5">
                  <span className="text-[#aaa] text-xs">含手續費 USD {fee}</span>
                  <HelpCircle size={13} className="text-[#2dba6a]" />
                </div>
              </div>
              <span className="text-[#1a1a1a] text-sm font-medium">USD {total.toFixed(1)}</span>
            </div>
          </div>
        </div>

        {/* 交易日 */}
        <div className="bg-white mx-3 mt-2 rounded-[12px] border border-[#eee] px-4 py-4">
          <div className="text-[#1a1a1a] text-sm font-medium mb-3">交易日 (可複選)</div>
          <div className="flex gap-3">
            {tradeDays.map((d) => {
              const active = days.includes(d)
              return (
                <button
                  key={d}
                  onClick={() => setDays(prev =>
                    active ? prev.filter(x => x !== d) : [...prev, d]
                  )}
                  className={clsx(
                    'flex-1 py-4 rounded-[12px] border-2 flex flex-col items-center',
                    active ? 'border-[#2dba6a] bg-[#f0faf5]' : 'border-[#ddd]'
                  )}
                >
                  <span className="text-[#888] text-xs">每月</span>
                  <span className={clsx('text-3xl font-bold', active ? 'text-[#2dba6a]' : 'text-[#1a1a1a]')}>{d}</span>
                  <span className="text-[#888] text-xs">號</span>
                </button>
              )
            })}
          </div>

          {/* Orange notice */}
          <div className="flex items-start gap-2 mt-3 p-3 bg-[#fff8ef] rounded-[8px]">
            <Info size={14} className="text-[#ff9500] flex-shrink-0 mt-0.5" />
            <span className="text-[#ff9500] text-xs leading-relaxed">
              定股及定額買賣均獨立庫存，同一標的買入及賣出，手續費會分別計算。
            </span>
          </div>
        </div>

        {/* 報酬率試算 */}
        <div className="mt-2">
          <div className="bg-[#f0f0f0] px-4 py-2">
            <span className="text-[#888] text-sm font-medium">報酬率試算</span>
          </div>
          <div className="bg-white mx-0 px-4 pt-3 pb-4">
            <div className="flex gap-2 mb-4">
              {returnYears.map((y, i) => (
                <button
                  key={y}
                  onClick={() => setYear(i)}
                  className={clsx(
                    'flex-1 py-2 rounded-[8px] text-sm font-medium',
                    i === year ? 'bg-[#e8f8f0] text-[#2dba6a]' : 'bg-[#f5f5f5] text-[#888]'
                  )}
                >
                  {y}
                </button>
              ))}
            </div>
            {['累計損益', '股票市值', '累計成本', '累計股數'].map((label) => (
              <div key={label} className="flex items-center justify-between py-3 border-t border-[#f5f5f5]">
                <span className="text-[#888] text-sm">{label}</span>
                <span className="text-[#1a1a1a] text-sm">—</span>
              </div>
            ))}
            <p className="text-[#aaa] text-xs leading-relaxed mt-2">
              如果你在 {returnYears[year]} 前開始持續買進，持有至今的結果。股價以過去交易日的收盤價計算（已還原權息），不含手續費及交易稅。試算僅供參考，實際報酬以交易結果為主。
            </p>
          </div>
        </div>
      </div>

      {/* ── 固定底部 ── */}
      <div className="fixed bottom-0 left-1/2 -translate-x-1/2 w-full max-w-[430px] px-4 py-3 bg-white border-t border-[#eee] z-40">
        <button className="w-full py-4 bg-[#2dba6a] text-white rounded-full text-base font-semibold active:opacity-80">
          我要申購
        </button>
      </div>
    </div>
  )
}

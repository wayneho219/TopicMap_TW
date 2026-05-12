import { Bell, MoreHorizontal, ChevronRight, Ticket, SlidersHorizontal, BookOpen, TrendingUp, BarChart2, ArrowRightLeft, Coins, PenLine, Receipt, CreditCard, ArrowUpDown, Download, Leaf, Banknote } from 'lucide-react'

interface GridItem {
  icon: React.ElementType
  label: string
  badge?: 'HOT' | 'NEW'
}

const gridItems: GridItem[] = [
  { icon: Ticket,            label: '股票抽籤' },
  { icon: SlidersHorizontal, label: '額度調整' },
  { icon: BookOpen,          label: '教學懶人包' },
  { icon: TrendingUp,        label: '期貨開戶' },
  { icon: BarChart2,         label: '研究報告',      badge: 'HOT' },
  { icon: ArrowRightLeft,    label: '股票出借' },
  { icon: Coins,             label: '配股配息' },
  { icon: PenLine,           label: '線上簽署' },
  { icon: Receipt,           label: '預收款券' },
  { icon: CreditCard,        label: '信用戶專區' },
  { icon: ArrowUpDown,       label: '券差出借' },
  { icon: Download,          label: '匯出帳務資料', badge: 'NEW' },
  { icon: Leaf,              label: 'ESG 永續投資' },
  { icon: Banknote,          label: '定期定額' },
]

export function ProfilePage() {
  return (
    <div className="flex flex-col h-screen">

      {/* ── 釘住頂部（漸層） ── */}
      <div
        className="flex-shrink-0 z-20"
        style={{ background: 'linear-gradient(135deg, #00a878 0%, #1dcfae 100%)' }}
      >
        {/* Top Bar */}
        <div className="flex items-center justify-between px-4 pt-14 pb-3">
          {/* Avatar */}
          <div className="w-9 h-9 rounded-full bg-[#ff9500] flex items-center justify-center text-white text-lg font-bold">
            😊
          </div>
          <span className="text-white text-lg font-semibold">我的</span>
          <div className="flex items-center gap-3 text-white">
            <Bell size={20} />
            <MoreHorizontal size={20} />
          </div>
        </div>

        {/* Greeting + CTA */}
        <div className="flex items-center justify-between px-4 pb-4">
          <div>
            <div className="text-white text-lg font-medium mb-1">嗨，陳小明</div>
            <button className="flex items-center gap-1 text-white text-xs opacity-90">
              線上調升額度，一鍵申請
              <ChevronRight size={13} />
            </button>
          </div>
          <button className="border border-white text-white text-xs px-4 py-1.5 rounded-full opacity-90 active:opacity-70">
            立即申請
          </button>
        </div>
      </div>

      {/* ── 捲動內容區（白底） ── */}
      <div className="flex-1 overflow-y-auto bg-white pb-16">

        {/* Banner Carousel */}
        <div className="mx-3 mt-3 rounded-[12px] overflow-hidden bg-[#4a3fc0] relative" style={{ minHeight: 100 }}>
          <div className="flex items-center justify-between p-4">
            <div>
              <div className="text-white text-lg font-bold leading-tight">
                買ETF 選國泰
              </div>
              <div className="text-white text-xs opacity-80 mt-0.5">
                總價值60萬月月抽
              </div>
              <button className="mt-2 bg-[#e84040] text-white text-xs px-3 py-1 rounded-sm font-medium">
                立即了解 ▶
              </button>
            </div>
            <div className="text-6xl">🏠</div>
          </div>
          {/* Dots */}
          <div className="flex justify-center gap-1.5 pb-2">
            {[0, 1, 2, 3].map((i) => (
              <span
                key={i}
                className={`w-1.5 h-1.5 rounded-full ${i === 0 ? 'bg-white' : 'bg-white/40'}`}
              />
            ))}
          </div>
        </div>

        {/* Activity Row */}
        <button className="w-full flex items-center justify-between px-4 py-3 border-b border-[#f0f0f0] active:bg-[#f9f9f9]">
          <div className="flex items-center gap-2 text-sm">
            <span className="text-[#ff9500] font-medium">活動</span>
            <span className="text-[#444]">｜與好友共享 600 元立即 GO</span>
          </div>
          <ChevronRight size={16} className="text-[#aaa]" />
        </button>

        {/* Icon Grid */}
        <div className="grid grid-cols-3 gap-0 px-2 py-2">
          {gridItems.map(({ icon: Icon, label, badge }) => (
            <button
              key={label}
              className="flex flex-col items-center justify-center py-4 gap-2 active:bg-[#f5f5f5] rounded-[8px] relative"
            >
              {/* Badge */}
              {badge && (
                <span className={`absolute top-2 right-4 text-white text-[9px] font-bold px-1.5 py-0.5 rounded-full ${badge === 'HOT' ? 'bg-[#e84040]' : 'bg-[#ff9500]'}`}>
                  {badge}
                </span>
              )}
              {/* Icon container */}
              <div className="w-12 h-12 rounded-[12px] border border-[#e8f8f0] bg-[#f2fbf7] flex items-center justify-center">
                <Icon size={22} className="text-[#2dba6a]" strokeWidth={1.5} />
              </div>
              <span className="text-[#333] text-xs text-center leading-tight">{label}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}

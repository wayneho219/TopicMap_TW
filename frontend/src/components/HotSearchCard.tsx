import { Heart } from 'lucide-react'
import { clsx } from 'clsx'
import type { StockItem } from '../data/mock'

interface Props {
  stock: StockItem
  onClick?: () => void
}

export function HotSearchCard({ stock, onClick }: Props) {
  const up = stock.change >= 0

  return (
    <button
      onClick={onClick}
      className="flex flex-col justify-between bg-[#1e1e1e] rounded-[10px] p-3 text-left flex-shrink-0 w-[140px] active:opacity-80 transition-opacity"
      style={{ minHeight: 90 }}
    >
      <div className="flex items-start justify-between">
        <div>
          <div className="text-white text-sm font-medium">{stock.name}</div>
          <div className="text-[#666] text-xs mt-0.5">{stock.id}</div>
        </div>
        <Heart size={14} className="text-[#555] flex-shrink-0 mt-0.5" />
      </div>
      <div>
        <div className={clsx('text-lg font-bold', up ? 'text-[#e84040]' : 'text-[#2dba6a]')}>
          {stock.price.toLocaleString()}
        </div>
        <div className={clsx('text-xs', up ? 'text-[#e84040]' : 'text-[#2dba6a]')}>
          {up ? '▲' : '▼'} {Math.abs(stock.changePercent).toFixed(2)}%
        </div>
      </div>
    </button>
  )
}

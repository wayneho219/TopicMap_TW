import { clsx } from 'clsx'
import type { StockItem } from '../data/mock'

interface Props {
  stock: StockItem
  rank: number
  onClick?: () => void
}

const rankColors: Record<number, string> = {
  1: 'bg-[#c0392b]',
  2: 'bg-[#e67e22]',
  3: 'bg-[#f39c12]',
}

export function RankListItem({ stock, rank, onClick }: Props) {
  const up = stock.change >= 0

  return (
    <button
      onClick={onClick}
      className="flex items-center w-full px-3 py-3.5 bg-[#1e1e1e] rounded-[8px] active:opacity-80 transition-opacity text-left"
    >
      <span className={clsx(
        'w-6 h-6 rounded flex items-center justify-center text-white text-xs font-bold flex-shrink-0 mr-3',
        rankColors[rank] ?? 'bg-[#333]'
      )}>
        {rank}
      </span>
      <div className="flex-1 min-w-0">
        <div className="text-white text-sm font-medium">{stock.name}</div>
        <div className="text-[#666] text-xs">{stock.id}</div>
      </div>
      <div className="text-right">
        <div className={clsx('text-base font-bold', up ? 'text-[#e84040]' : 'text-[#2dba6a]')}>
          {stock.price.toLocaleString()}
        </div>
        <div className={clsx('text-xs', up ? 'text-[#e84040]' : 'text-[#2dba6a]')}>
          {up ? '▲' : '▼'} {Math.abs(stock.change).toFixed(2)} {up ? '▲' : '▼'} {Math.abs(stock.changePercent).toFixed(2)}%
        </div>
      </div>
    </button>
  )
}

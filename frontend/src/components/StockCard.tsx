import { clsx } from 'clsx'
import type { WatchlistStock } from '../data/mock'

interface Props {
  stock: WatchlistStock
  onClick?: () => void
  decimals?: number
}

export function StockCard({ stock, onClick, decimals = 2 }: Props) {
  const up = stock.change >= 0

  return (
    <button
      onClick={onClick}
      className={clsx(
        'flex flex-col justify-between p-3 rounded-[8px] border text-left w-full',
        'bg-[#1e1e1e] active:opacity-80 transition-opacity',
        up ? 'border-[#e84040]' : 'border-[#2dba6a]'
      )}
      style={{ minHeight: decimals === 4 ? 120 : 110 }}
    >
      <div className="text-white text-sm font-medium leading-tight">
        {stock.name} <span className="text-[#888] text-xs">{decimals === 2 ? stock.id : ''}</span>
      </div>
      <div className={clsx('font-bold tracking-tight mt-1', up ? 'text-[#e84040]' : 'text-[#2dba6a]', decimals === 4 ? 'text-2xl' : 'text-3xl')}>
        {stock.price.toFixed(decimals)}
      </div>
      <div className={clsx('flex items-center gap-2 text-xs mt-1', up ? 'text-[#e84040]' : 'text-[#2dba6a]')}>
        <span className="flex items-center gap-0.5">
          {Math.abs(stock.change).toFixed(decimals)}
          <span className="ml-0.5">{up ? '🔺' : '🔻'}</span>
        </span>
        <span>{Math.abs(stock.changePercent).toFixed(2)}%</span>
      </div>
    </button>
  )
}

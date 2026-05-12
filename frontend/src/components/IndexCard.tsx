import { clsx } from 'clsx'
import type { IndexItem } from '../data/mock'

interface Props {
  item: IndexItem
}

export function IndexCard({ item }: Props) {
  const up = item.change >= 0

  return (
    <div className={clsx(
      'flex-1 rounded-[10px] p-3',
      up ? 'bg-[#3a1515]' : 'bg-[#0f2e1c]'
    )}>
      <div className="text-[#aaa] text-xs mb-1">{item.name}</div>
      <div className={clsx('text-2xl font-bold tracking-tight', up ? 'text-[#e84040]' : 'text-[#2dba6a]')}>
        {item.value.toLocaleString('en-US', { minimumFractionDigits: 2 })}
      </div>
      <div className={clsx('flex items-center gap-1.5 mt-1 text-xs', up ? 'text-[#e84040]' : 'text-[#2dba6a]')}>
        <span>{up ? '▲' : '▼'} {Math.abs(item.change).toFixed(2)}</span>
        <span>{up ? '▲' : '▼'} {Math.abs(item.changePercent).toFixed(2)}%</span>
      </div>
    </div>
  )
}

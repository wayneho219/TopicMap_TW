import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ChevronRight } from 'lucide-react'
import { clsx } from 'clsx'
import { useIndustries, useIndustryTopics } from '../hooks/useMarketData'
import type { IndustryData, IndustryTopic } from '../hooks/useMarketData'

function TopicRow({ topic }: { topic: IndustryTopic }) {
  const navigate = useNavigate()
  const up = topic.changePercent >= 0

  function handleClick() {
    if (topic.source === 'tpex') {
      navigate(`/chain/${encodeURIComponent(topic.name)}`)
    } else {
      navigate(`/topic/fine/${encodeURIComponent(topic.name)}`)
    }
  }

  return (
    <div
      className="pl-6 pr-4 py-2.5 border-t border-[#252525] cursor-pointer active:opacity-70 flex items-center justify-between"
      onClick={handleClick}
    >
      <div className="flex items-center gap-2">
        <span className="text-[#bbb] text-sm">{topic.name}</span>
        {topic.source === 'nlp' && (
          <span className="text-[10px] text-[#3a7bd5] bg-[#1a2a40] px-1 py-0.5 rounded leading-none">
            ✦
          </span>
        )}
      </div>
      <div className="flex items-center gap-3">
        <span className="text-xs text-[#666]">{topic.stockCount}支</span>
        <span className={clsx('text-sm font-medium', up ? 'text-[#e84040]' : 'text-[#2dba6a]')}>
          {up ? '+' : ''}{topic.changePercent.toFixed(2)}%
        </span>
      </div>
    </div>
  )
}

function IndustryCard({
  industry,
  maxChange,
  expanded,
  onToggle,
}: {
  industry: IndustryData
  maxChange: number
  expanded: boolean
  onToggle: () => void
}) {
  const topics = useIndustryTopics(expanded ? industry.name : '')
  const up = industry.changePercent >= 0
  const barW = maxChange > 0
    ? Math.round((Math.abs(industry.changePercent) / maxChange) * 100)
    : 0

  return (
    <div className="bg-[#1e1e1e] rounded-[10px] overflow-hidden">
      <div className="px-4 py-3 cursor-pointer active:opacity-70" onClick={onToggle}>
        <div className="flex items-center justify-between mb-2">
          <span className="text-white text-sm font-medium">{industry.name}</span>
          <div className="flex items-center gap-2">
            <span className={clsx('text-base font-bold', up ? 'text-[#e84040]' : 'text-[#2dba6a]')}>
              {up ? '+' : ''}{industry.changePercent.toFixed(2)}%
            </span>
            <ChevronRight
              size={16}
              className={clsx(
                'text-[#2dba6a] transition-transform duration-200',
                expanded && 'rotate-90',
              )}
            />
          </div>
        </div>
        <div className="h-1.5 bg-[#2e2e2e] rounded-full overflow-hidden mb-2">
          <div
            className={clsx('h-full rounded-full', up ? 'bg-[#e84040]' : 'bg-[#2dba6a]')}
            style={{ width: `${barW}%` }}
          />
        </div>
        <div className="flex gap-3 text-xs text-[#666]">
          <span>{industry.topicCount}個主題</span>
          <span className="text-[#e84040]">漲 {industry.advance}</span>
          <span className="text-[#2dba6a]">跌 {industry.decline}</span>
        </div>
      </div>

      {expanded && topics.length > 0 && (
        <div>
          {topics.map((t) => (
            <TopicRow key={`${t.source}-${t.name}`} topic={t} />
          ))}
        </div>
      )}
      {expanded && topics.length === 0 && (
        <div className="pl-6 py-3 text-[#555] text-xs border-t border-[#252525]">載入中...</div>
      )}
    </div>
  )
}

export function IndustryTab() {
  const industries = useIndustries()
  const [expandedName, setExpandedName] = useState<string | null>(null)
  const maxChange = industries.length > 0
    ? Math.max(...industries.map((i) => Math.abs(i.changePercent)))
    : 1

  if (industries.length === 0) {
    return <div className="text-[#666] text-sm text-center pt-10">載入中...</div>
  }

  return (
    <div className="space-y-2">
      {industries.map((industry) => (
        <IndustryCard
          key={industry.name}
          industry={industry}
          maxChange={maxChange}
          expanded={expandedName === industry.name}
          onToggle={() =>
            setExpandedName((prev) => (prev === industry.name ? null : industry.name))
          }
        />
      ))}
    </div>
  )
}

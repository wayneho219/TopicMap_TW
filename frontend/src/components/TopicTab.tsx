// frontend/src/components/TopicTab.tsx
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ChevronRight } from 'lucide-react'
import { useTopics, useTopicChildren } from '../hooks/useTopics'
import type { Topic } from '../hooks/useTopics'

function fmtInvested(n: number): string {
  if (n >= 1e8) return `${(n / 1e8).toFixed(0)}億`
  if (n >= 1e4) return `${(n / 1e4).toFixed(0)}萬`
  return n.toFixed(0)
}

function FineRow({ topic, maxInvested }: { topic: Topic; maxInvested: number }) {
  const navigate = useNavigate()
  const barW = maxInvested > 0 ? Math.round((topic.totalInvested / maxInvested) * 100) : 0
  return (
    <div
      className="pl-6 pr-4 py-2.5 border-t border-[#252525] cursor-pointer active:opacity-70"
      onClick={() => navigate(`/topic/fine/${encodeURIComponent(topic.name)}`)}
    >
      <div className="flex items-center justify-between mb-1">
        <span className="text-[#bbb] text-sm">{topic.name}</span>
        <span className="text-[#999] text-sm">{fmtInvested(topic.totalInvested)}</span>
      </div>
      <div className="h-1 bg-[#2e2e2e] rounded-full overflow-hidden mb-1">
        <div className="h-full bg-[#3a7bd5] rounded-full" style={{ width: `${barW}%` }} />
      </div>
      <span className="text-[#555] text-xs">{topic.stockCount}支 · {topic.articleCount}篇</span>
    </div>
  )
}

function MediumCard({
  topic,
  maxInvested,
  expanded,
  onToggle,
}: {
  topic: Topic
  maxInvested: number
  expanded: boolean
  onToggle: () => void
}) {
  const navigate = useNavigate()
  const children = useTopicChildren(expanded ? topic.name : '')
  const childMax = children.length > 0
    ? Math.max(...children.map((c) => c.totalInvested))
    : 1
  const barW = maxInvested > 0 ? Math.round((topic.totalInvested / maxInvested) * 100) : 0

  return (
    <div className="bg-[#1e1e1e] rounded-[10px] overflow-hidden">
      <div className="px-4 py-3 cursor-pointer active:opacity-70" onClick={onToggle}>
        <div className="flex items-center justify-between mb-2">
          <span className="text-white text-sm font-medium">{topic.name}</span>
          <div className="flex items-center gap-2">
            <span className="text-[#aaa] text-sm">{fmtInvested(topic.totalInvested)}</span>
            <button
              className="text-[#2dba6a] active:opacity-60"
              onClick={(e) => {
                e.stopPropagation()
                navigate(`/topic/medium/${encodeURIComponent(topic.name)}`)
              }}
            >
              <ChevronRight size={16} />
            </button>
          </div>
        </div>
        <div className="h-1.5 bg-[#2e2e2e] rounded-full overflow-hidden mb-2">
          <div className="h-full bg-[#3a7bd5] rounded-full" style={{ width: `${barW}%` }} />
        </div>
        <span className="text-[#555] text-xs">{topic.stockCount}支 · {topic.articleCount}篇</span>
      </div>

      {expanded && children.length > 0 && (
        <div>
          {children.map((child) => (
            <FineRow key={child.id} topic={child} maxInvested={childMax} />
          ))}
        </div>
      )}
    </div>
  )
}

export function TopicTab() {
  const topics = useTopics('medium')
  const [expandedName, setExpandedName] = useState<string | null>(null)
  const maxInvested = topics.length > 0 ? Math.max(...topics.map((t) => t.totalInvested)) : 1

  return (
    <div className="space-y-2">
      {topics.length === 0 && (
        <div className="text-[#666] text-sm text-center pt-10">載入中...</div>
      )}
      {topics.map((topic) => (
        <MediumCard
          key={topic.id}
          topic={topic}
          maxInvested={maxInvested}
          expanded={expandedName === topic.name}
          onToggle={() =>
            setExpandedName((prev) => (prev === topic.name ? null : topic.name))
          }
        />
      ))}
    </div>
  )
}

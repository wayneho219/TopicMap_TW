import { useLocation, useNavigate } from 'react-router-dom'
import { BarChart2, TrendingUp, RefreshCw, ShoppingCart, PieChart, User } from 'lucide-react'
import { clsx } from 'clsx'

const tabs = [
  { label: '行情', icon: BarChart2, path: '/' },
  { label: '選股', icon: TrendingUp, path: '/search' },
  { label: '定期投資', icon: RefreshCw, path: '/recurring' },
  { label: '下單', icon: ShoppingCart, path: '/order' },
  { label: '帳務', icon: PieChart, path: '/account' },
  { label: '我的', icon: User, path: '/profile' },
]

export function BottomNav() {
  const location = useLocation()
  const navigate = useNavigate()

  return (
    <nav className="fixed bottom-0 left-1/2 -translate-x-1/2 w-full max-w-[430px] bg-[#1a1a1a] border-t border-[#2e2e2e] flex z-50">
      {tabs.map((tab) => {
        const active = location.pathname === tab.path
        return (
          <button
            key={tab.path}
            onClick={() => navigate(tab.path)}
            className={clsx(
              'flex-1 flex flex-col items-center justify-center py-2 gap-0.5 min-h-[56px] text-[10px]',
              active ? 'text-[#2dba6a]' : 'text-[#666]'
            )}
          >
            <tab.icon size={20} strokeWidth={active ? 2.5 : 1.8} />
            <span>{tab.label}</span>
          </button>
        )
      })}
    </nav>
  )
}

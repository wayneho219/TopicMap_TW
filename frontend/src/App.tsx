import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom'
import { BottomNav } from './components/BottomNav'
import { MarketPage } from './pages/MarketPage'
import { WatchlistPage } from './pages/WatchlistPage'
import { StockDetailPage } from './pages/StockDetailPage'
import { StockSearchPage } from './pages/StockSearchPage'
import { OrderPage } from './pages/OrderPage'
import { AccountPage } from './pages/AccountPage'
import { ProfilePage } from './pages/ProfilePage'
import { RecurringPage } from './pages/RecurringPage'
import { RecurringSubscribeUSPage } from './pages/RecurringSubscribeUSPage'
import { RecurringSubscribeTWPage } from './pages/RecurringSubscribeTWPage'
import { SectorDetailPage } from './pages/SectorDetailPage'

function Layout() {
  const location = useLocation()
  const hideBottomNav =
    location.pathname.startsWith('/stock/') ||
    location.pathname === '/order' ||
    location.pathname.startsWith('/subscribe/') ||
    location.pathname.startsWith('/sector/') ||
    location.pathname.startsWith('/chain/')

  return (
    <div className="relative">
      <Routes>
        <Route path="/" element={<MarketPage />} />
        <Route path="/watchlist" element={<WatchlistPage />} />
        <Route path="/stock/:id" element={<StockDetailPage />} />
        <Route path="/search" element={<StockSearchPage />} />
        <Route path="/recurring" element={<RecurringPage />} />
        <Route path="/order" element={<OrderPage />} />
        <Route path="/subscribe/tw/:id" element={<RecurringSubscribeTWPage />} />
        <Route path="/subscribe/us/:id" element={<RecurringSubscribeUSPage />} />
        <Route path="/account" element={<AccountPage />} />
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="/sector/:name" element={<SectorDetailPage kind="sector" />} />
        <Route path="/chain/:name" element={<SectorDetailPage kind="chain" />} />
      </Routes>
      {!hideBottomNav && <BottomNav />}
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Layout />
    </BrowserRouter>
  )
}

export interface IndexItem {
  name: string
  value: number
  change: number
  changePercent: number
}

export interface StockItem {
  id: string
  name: string
  price: number
  change: number
  changePercent: number
  volume?: number
  description?: string
}

export interface WatchlistStock {
  id: string
  name: string
  price: number
  change: number
  changePercent: number
}

export interface PortfolioStock {
  id: string
  name: string
  type: string
  shares: number
  totalValue: number
  totalCost: number
  pnl: number
  pnlPercent: number
}

// TODO: replace with GET /api/indices
export const mockIndices: IndexItem[] = [
  { name: '加權指數', value: 41933.78, change: 794.93, changePercent: 1.93 },
  { name: '櫃檯指數', value: 416.41, change: 6.12, changePercent: 1.49 },
]

// TODO: replace with GET /api/stocks/hot-search
export const mockHotSearch: StockItem[] = [
  { id: '2454', name: '聯發科', price: 3420.0, change: -9.8, changePercent: -0.29 },
  { id: '2303', name: '聯電', price: 96.5, change: 5.1, changePercent: 5.58 },
  { id: '2330', name: '台積電', price: 1025.0, change: 25.0, changePercent: 2.5 },
  { id: '2317', name: '鴻海', price: 180.5, change: -2.0, changePercent: -1.1 },
]

// TODO: replace with GET /api/stocks/hot-market?sort=volume
export const mockHotMarket: StockItem[] = [
  { id: '3481', name: '群創', price: 29.75, change: 1.65, changePercent: 5.87, volume: 328450 },
  { id: '2344', name: '華邦電', price: 114.0, change: 5.5, changePercent: 5.07, volume: 291200 },
  { id: '2308', name: '台達電', price: 412.0, change: 12.0, changePercent: 3.0, volume: 215400 },
  { id: '2382', name: '廣達', price: 320.5, change: -4.5, changePercent: -1.39, volume: 198700 },
  { id: '2395', name: '研華', price: 280.0, change: 8.0, changePercent: 2.94, volume: 145300 },
]

// TODO: replace with GET /api/watchlist
export const mockWatchlistTW: WatchlistStock[] = [
  { id: '006208', name: '富邦台50', price: 226.8, change: 4.8, changePercent: 2.16 },
  { id: '00692', name: '富邦公司治理', price: 85.3, change: 1.75, changePercent: 2.09 },
  { id: '2313', name: '華通', price: 249.5, change: 0.5, changePercent: 0.2 },
]

export const mockWatchlistUS: WatchlistStock[] = [
  { id: 'NBIS', name: 'NBIS', price: 195.09, change: 19.17, changePercent: 10.9 },
  { id: 'AMD', name: 'AMD', price: 421.39, change: 66.13, changePercent: 18.61 },
  { id: 'NVDA', name: 'NVDA', price: 207.83, change: 11.33, changePercent: 5.77 },
  { id: 'PLTR', name: 'PLTR', price: 133.79, change: 2.12, changePercent: 1.56 },
  { id: 'HIMS', name: 'HIMS', price: 26.88, change: -0.55, changePercent: -2.09 },
  { id: 'PYPL', name: 'PYPL', price: 46.27, change: 0.22, changePercent: 0.47 },
  { id: 'ISRG', name: 'ISRG', price: 451.73, change: -3.2, changePercent: -0.7 },
  { id: 'BRK/B', name: 'BRK/B', price: 469.83, change: 5.1, changePercent: 1.09 },
]

// TODO: replace with GET /api/stocks/:id
export const mockStockDetail = {
  id: '0050',
  name: '元大台灣50',
  price: 97.7,
  change: 1.95,
  changePercent: 2.04,
  status: '已收盤',
  high: 98.4,
  low: 97.4,
  prevClose: 95.75,
  open: 97.95,
  tags: ['上市', '可現沖'],
}

// TODO: replace with GET /api/portfolio
export const mockPortfolio: PortfolioStock[] = [
  { id: '006208', name: '富邦台50', type: '現股', shares: 345, totalValue: 78137, totalCost: 7000, pnl: 78137, pnlPercent: 0 },
  { id: '00692', name: '富邦公司治理', type: '現股', shares: 2539, totalValue: 216274, totalCost: 50000, pnl: 216274, pnlPercent: 0 },
  { id: '2313', name: '華通', type: '現股', shares: 50, totalValue: 12462, totalCost: 7000, pnl: 5432, pnlPercent: 77.58 },
]

export const mockPortfolioSummary = {
  totalValue: 306845,
  totalCost: 7002,
  totalPnl: 299843,
  totalPnlPercent: 4282.25,
}

export interface ChartPoint {
  time: string
  price: number
  volume: number
  pct: number
}

// TODO: replace with GET /api/stocks/0050/intraday
export const mockChartData: ChartPoint[] = [
  { time: '9:00', price: 97.95, volume: 8200, pct: 2.3 },
  { time: '9:15', price: 98.2, volume: 12400, pct: 2.56 },
  { time: '9:30', price: 98.4, volume: 9800, pct: 2.77 },
  { time: '9:45', price: 98.1, volume: 7600, pct: 2.45 },
  { time: '10:00', price: 97.9, volume: 6300, pct: 2.24 },
  { time: '10:15', price: 97.75, volume: 5800, pct: 2.08 },
  { time: '10:30', price: 97.8, volume: 4900, pct: 2.14 },
  { time: '10:45', price: 97.6, volume: 5200, pct: 1.93 },
  { time: '11:00', price: 97.7, volume: 4700, pct: 2.04 },
  { time: '11:15', price: 97.85, volume: 5100, pct: 2.19 },
  { time: '11:30', price: 97.65, volume: 6200, pct: 1.98 },
  { time: '11:45', price: 97.55, volume: 4400, pct: 1.88 },
  { time: '12:00', price: 97.7, volume: 3900, pct: 2.04 },
  { time: '12:15', price: 97.8, volume: 4100, pct: 2.14 },
  { time: '12:30', price: 97.6, volume: 4800, pct: 1.93 },
  { time: '12:45', price: 97.5, volume: 3700, pct: 1.83 },
  { time: '13:00', price: 97.65, volume: 5500, pct: 1.98 },
  { time: '13:15', price: 97.7, volume: 8900, pct: 2.04 },
  { time: '13:30', price: 97.7, volume: 13200, pct: 2.04 },
]

export interface RecurringStock {
  rank: number
  name: string
  id: string
  type: 'ETF' | '股票'
  price: number
  metric: number   // 殖利率(台股) 或 漲跌幅月(美股)
  metricIsYield: boolean
}

// TODO: replace with GET /api/recurring/tw
export const mockRecurringTW: RecurringStock[] = [
  { rank: 1,  name: '國泰永續高股息',   id: '00878',  type: 'ETF', price: 27.89,  metric: 2.37,  metricIsYield: true },
  { rank: 2,  name: '國泰台灣科技...',   id: '00881',  type: 'ETF', price: 50.95,  metric: 2.55,  metricIsYield: true },
  { rank: 3,  name: '元大台灣50',        id: '0050',   type: 'ETF', price: 97.70,  metric: 3.13,  metricIsYield: true },
  { rank: 4,  name: '元大高股息',         id: '0056',   type: 'ETF', price: 38.42,  metric: 4.82,  metricIsYield: true },
  { rank: 5,  name: '富邦台50',           id: '006208', type: 'ETF', price: 226.80, metric: 2.16,  metricIsYield: true },
  { rank: 6,  name: '永豐台灣ESG...',     id: '00930',  type: 'ETF', price: 22.15,  metric: 1.92,  metricIsYield: true },
  { rank: 7,  name: '群益台灣精選...',    id: '00919',  type: 'ETF', price: 25.43,  metric: 3.07,  metricIsYield: true },
  { rank: 8,  name: '國泰10Y+金融債',    id: '00933B', type: 'ETF', price: 16.00,  metric: 1.38,  metricIsYield: true },
  { rank: 9,  name: '復華台灣科技...',    id: '00929',  type: 'ETF', price: 25.08,  metric: 1.36,  metricIsYield: true },
  { rank: 10, name: '元大台灣高息...',    id: '00713',  type: 'ETF', price: 54.30,  metric: 1.44,  metricIsYield: true },
]

// TODO: replace with GET /api/recurring/us
export const mockRecurringUS: RecurringStock[] = [
  { rank: 1,  name: 'NVIDIA',           id: 'NVDA',   type: '股票', price: 207.83,  metric: 42.15, metricIsYield: false },
  { rank: 2,  name: 'Apple',            id: 'AAPL',   type: '股票', price: 287.51,  metric: 18.50, metricIsYield: false },
  { rank: 3,  name: 'Microsoft',        id: 'MSFT',   type: '股票', price: 492.30,  metric: 15.20, metricIsYield: false },
  { rank: 4,  name: 'Tesla',            id: 'TSLA',   type: '股票', price: 285.60,  metric: 28.40, metricIsYield: false },
  { rank: 5,  name: 'Amazon',           id: 'AMZN',   type: '股票', price: 225.10,  metric: 22.80, metricIsYield: false },
  { rank: 6,  name: 'Meta',             id: 'META',   type: '股票', price: 618.40,  metric: 35.60, metricIsYield: false },
  { rank: 7,  name: 'Alphabet Inc A',   id: 'GOOGL',  type: '股票', price: 398.04,  metric: 32.68, metricIsYield: false },
  { rank: 8,  name: '台積電 ADR',        id: 'TSM',    type: '股票', price: 419.50,  metric: 22.75, metricIsYield: false },
  { rank: 9,  name: 'State Street S...', id: 'SPY',   type: 'ETF',  price: 733.83,  metric: 11.37, metricIsYield: false },
  { rank: 10, name: '蘋果',              id: 'AAPL',  type: '股票',  price: 287.51,  metric: 11.07, metricIsYield: false },
]

export const mockRecentSearches = ['玉山金', '華通', '昇達科', '光寶科', 'First Majestic Silver Corp.', 'Fiserv Inc']

// TODO: replace with GET /api/stocks/top30
export const mockTop30: StockItem[] = [
  { id: '0050', name: '元大台灣50', price: 97.7, change: 1.95, changePercent: 2.04, description: '69% 存股族加入自選' },
  { id: '2330', name: '台積電', price: 2310.0, change: 60.0, changePercent: 2.67, description: '21% 存股族近期交易' },
  { id: '00981A', name: '主動統一台股增長', price: 29.58, change: 0.28, changePercent: 0.96, description: '猜你也會喜歡' },
  { id: '2317', name: '鴻海', price: 180.5, change: -2.0, changePercent: -1.1, description: '' },
  { id: '2454', name: '聯發科', price: 3420.0, change: -9.8, changePercent: -0.29, description: '' },
]

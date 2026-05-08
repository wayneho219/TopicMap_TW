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

// ── 美股 ──
export const mockIndicesUS: IndexItem[] = [
  { name: 'S&P 500',  value: 5308.13, change:  36.88, changePercent:  0.70 },
  { name: 'NASDAQ',   value: 16742.39, change: 137.53, changePercent:  0.83 },
]

export const mockHotSearchUS: StockItem[] = [
  { id: 'NVDA',  name: 'NVIDIA',    price: 207.83, change:  8.43, changePercent:  4.23 },
  { id: 'AAPL',  name: 'Apple',     price: 287.51, change:  3.21, changePercent:  1.13 },
  { id: 'TSLA',  name: 'Tesla',     price: 285.60, change: 12.40, changePercent:  4.54 },
  { id: 'META',  name: 'Meta',      price: 618.40, change: 15.20, changePercent:  2.52 },
]

export const mockHotMarketUS: StockItem[] = [
  { id: 'NVDA',  name: 'NVIDIA',    price: 207.83, change:  8.43, changePercent:  4.23, volume: 412300 },
  { id: 'AAPL',  name: 'Apple',     price: 287.51, change:  3.21, changePercent:  1.13, volume: 385600 },
  { id: 'MSFT',  name: 'Microsoft', price: 492.30, change:  7.10, changePercent:  1.46, volume: 298400 },
  { id: 'TSLA',  name: 'Tesla',     price: 285.60, change: 12.40, changePercent:  4.54, volume: 276800 },
  { id: 'AMZN',  name: 'Amazon',    price: 225.10, change:  4.80, changePercent:  2.18, volume: 189500 },
]

// ── 台股 ETF ──
export const mockIndicesETFTW: IndexItem[] = [
  { name: '台灣50指數',   value: 2318.75, change:  60.50, changePercent:  2.68 },
  { name: '高股息指數',   value: 1052.40, change:  15.30, changePercent:  1.48 },
]

export const mockHotSearchETFTW: StockItem[] = [
  { id: '0050',   name: '元大台灣50',       price: 178.35, change:  3.45, changePercent:  1.97 },
  { id: '00878',  name: '國泰永續高股息',   price:  27.89, change:  0.52, changePercent:  1.90 },
  { id: '0056',   name: '元大高股息',       price:  38.42, change:  0.68, changePercent:  1.80 },
  { id: '006208', name: '富邦台50',         price: 226.80, change:  4.80, changePercent:  2.16 },
]

export const mockHotMarketETFTW: StockItem[] = [
  { id: '0050',   name: '元大台灣50',       price: 178.35, change:  3.45, changePercent:  1.97, volume: 312400 },
  { id: '00878',  name: '國泰永續高股息',   price:  27.89, change:  0.52, changePercent:  1.90, volume: 289100 },
  { id: '0056',   name: '元大高股息',       price:  38.42, change:  0.68, changePercent:  1.80, volume: 241500 },
  { id: '006208', name: '富邦台50',         price: 226.80, change:  4.80, changePercent:  2.16, volume: 187300 },
  { id: '00929',  name: '復華台灣科技主題', price:  25.08, change:  0.48, changePercent:  1.95, volume: 156700 },
]

// ── 美股 ETF ──
export const mockIndicesETFUS: IndexItem[] = [
  { name: 'SPY',  value: 584.30, change:  4.08, changePercent:  0.70 },
  { name: 'QQQ',  value: 449.20, change:  6.15, changePercent:  1.39 },
]

export const mockHotSearchETFUS: StockItem[] = [
  { id: 'SPY',   name: 'SPDR S&P 500', price: 584.30, change:  4.08, changePercent:  0.70 },
  { id: 'QQQ',   name: 'Invesco QQQ',  price: 449.20, change:  6.15, changePercent:  1.39 },
  { id: 'VTI',   name: 'Vanguard VTI', price: 272.50, change:  1.85, changePercent:  0.68 },
  { id: 'ARKK',  name: 'ARK Innovation', price: 52.30, change:  2.10, changePercent:  4.19 },
]

export const mockHotMarketETFUS: StockItem[] = [
  { id: 'SPY',   name: 'SPDR S&P 500', price: 584.30, change:  4.08, changePercent:  0.70, volume: 298700 },
  { id: 'QQQ',   name: 'Invesco QQQ',  price: 449.20, change:  6.15, changePercent:  1.39, volume: 245300 },
  { id: 'VTI',   name: 'Vanguard VTI', price: 272.50, change:  1.85, changePercent:  0.68, volume: 189400 },
  { id: 'ARKK',  name: 'ARK Innovation', price: 52.30, change:  2.10, changePercent:  4.19, volume: 143200 },
  { id: 'IWM',   name: 'iShares Russell 2000', price: 209.80, change:  3.20, changePercent:  1.55, volume: 121800 },
]

// TODO: replace with GET /api/watchlist
export const mockWatchlistTW: WatchlistStock[] = [
  { id: '0050',   name: '元大台灣50',   price: 178.35, change:  3.45, changePercent:  1.97 },
  { id: '2330',   name: '台積電',       price: 2310.0, change: 60.00, changePercent:  2.67 },
  { id: '2454',   name: '聯發科',       price:  910.0, change: -18.0, changePercent: -1.94 },
  { id: '2317',   name: '鴻海',         price:  198.5, change:  2.50, changePercent:  1.27 },
]

export const mockWatchlistUS: WatchlistStock[] = [
  { id: 'AAPL',   name: 'Apple',        price: 189.30, change:  2.45, changePercent:  1.31 },
  { id: 'MSFT',   name: 'Microsoft',    price: 415.20, change:  6.80, changePercent:  1.66 },
  { id: 'GOOGL',  name: 'Alphabet',     price: 171.50, change: -1.20, changePercent: -0.69 },
  { id: 'AMZN',   name: 'Amazon',       price: 198.75, change:  3.10, changePercent:  1.58 },
  { id: 'META',   name: 'Meta',         price: 512.40, change: 11.20, changePercent:  2.24 },
  { id: 'TSLA',   name: 'Tesla',        price: 248.90, change: -4.30, changePercent: -1.70 },
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
  { id: '0050',  name: '元大台灣50', type: '現股', shares: 100, totalValue: 17835, totalCost: 15200, pnl:  2635, pnlPercent: 17.34 },
  { id: '2330',  name: '台積電',     type: '現股', shares:  10, totalValue: 23100, totalCost: 19500, pnl:  3600, pnlPercent: 18.46 },
  { id: '2454',  name: '聯發科',     type: '現股', shares:   5, totalValue:  4550, totalCost:  5200, pnl:  -650, pnlPercent: -12.50 },
]

export const mockPortfolioSummary = {
  totalValue: 45485,
  totalCost:  39900,
  totalPnl:    5585,
  totalPnlPercent: 14.0,
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

// ── 類股 ──
export interface SectorItem {
  name: string
  changePercent: number
  advance: number
  decline: number
}

export const mockSectors: SectorItem[] = [
  { name: 'AI／雲端概念', changePercent:  3.12, advance:  8, decline: 1 },
  { name: '半導體',       changePercent:  2.34, advance: 17, decline: 3 },
  { name: '電子零組件',   changePercent:  1.85, advance: 12, decline: 5 },
  { name: '航運',         changePercent:  1.23, advance:  5, decline: 4 },
  { name: '傳產',         changePercent:  0.67, advance:  8, decline: 3 },
  { name: '金融',         changePercent:  0.45, advance:  6, decline: 4 },
  { name: '營建',         changePercent: -0.34, advance:  4, decline: 6 },
  { name: '生技醫療',     changePercent: -0.82, advance:  3, decline: 8 },
  { name: '面板',         changePercent: -1.47, advance:  2, decline: 9 },
]

// ── 個股概念群組 ──
export const mockConceptGroups: Record<string, string[]> = {
  '2330':  ['AI晶片', 'CoWoS供應鏈', 'HBM題材'],
  '2454':  ['AI晶片', '無線通訊', '聯發科生態圈'],
  '2317':  ['AI伺服器', 'GB200組裝', '蘋果供應鏈'],
  '2344':  ['HBM記憶體', 'DRAM', 'AI相關'],
  '3481':  ['面板', '車用顯示'],
  '2308':  ['電源管理', '伺服器電源', 'AI供應鏈'],
  '2382':  ['AI伺服器', 'ODM', '雲端基礎設施'],
  '0050':  ['台股ETF', '指數型', '藍籌股'],
  '0056':  ['高息ETF', '存股族最愛'],
  '00878': ['高息ETF', 'ESG永續'],
  '006208':['台股ETF', '指數型'],
  'NVDA':  ['AI晶片', 'CUDA生態', '資料中心'],
  'AAPL':  ['蘋果生態', '消費電子', '服務收入'],
  'MSFT':  ['雲端運算', 'AI', 'Azure'],
  'TSLA':  ['電動車', '自動駕駛', '儲能'],
  'META':  ['社群媒體', 'AI廣告', 'AR/VR'],
  'AMZN':  ['電商', 'AWS雲端', 'AI基礎設施'],
  'GOOGL': ['搜尋廣告', 'Google Cloud', 'AI大模型'],
}

// ── 社群討論 ──
export interface ForumPost {
  platform: 'PTT' | '股討區'
  title: string
  author: string
  timeAgo: string
  heat: number
  sentiment: 'bull' | 'bear' | 'neutral'
}

export const mockForumPosts: Record<string, ForumPost[]> = {
  default: [
    { platform: 'PTT',  title: '今日盤中觀察與操作筆記', author: 'stockmaster88', timeAgo: '32分鐘前', heat: 142, sentiment: 'bull' },
    { platform: '股討區', title: '外資連續買超，後市怎麼看？', author: '投資小白鼠', timeAgo: '1小時前', heat: 98, sentiment: 'bull' },
    { platform: 'PTT',  title: '技術面分析－MACD即將翻多', author: 'ta_analyst', timeAgo: '2小時前', heat: 76, sentiment: 'bull' },
    { platform: '股討區', title: '法說會重點整理懶人包', author: '財經小編', timeAgo: '3小時前', heat: 210, sentiment: 'neutral' },
    { platform: 'PTT',  title: '今天沖太早跑掉真的哭哭', author: 'trader_cry', timeAgo: '4小時前', heat: 55, sentiment: 'bear' },
  ],
}

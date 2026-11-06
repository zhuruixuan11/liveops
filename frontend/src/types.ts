export interface User {
  id: number
  username: string
  role?: string
}

export interface Paginated<T> {
  items: T[]
  total: number
  page: number
  size: number
}

export interface Store {
  id: number
  name: string
  city: string
  address?: string
  status: 'closed' | 'opening' | 'opening_soon'
  phone?: string
  created_at?: string
}

export interface Category {
  id: number
  name: string
  parent_id?: number | null
  children?: Category[]
}

export interface Product {
  id: number
  name: string
  brand?: string
  category_id?: number
  price: number
  original_price?: number
  cover?: string
  images?: string[]
  sales?: number
  stock?: number
  skus?: Sku[]
  description?: string
}

export interface Sku {
  id: number
  spec: string
  price: number
  original_price?: number
  stock: number
  image?: string
}

export interface LiveSession {
  id: number
  store_id: number
  store?: Store
  title: string
  host?: string
  status: 'planned' | 'living' | 'ended'
  start_time?: string
  end_time?: string
  peak_viewer?: number
  current_viewer?: number
  gmv?: number
  conversion_rate?: number
  coupon_issued?: number
  product_ids?: number[]
}

export interface LiveDashboard {
  viewer_count: number
  peak_viewer: number
  coupon_issued: number
  gmv: number
  conversion_rate: number
  trending_viewers?: Array<{ time: string; count: number }>
  top_product?: Product & { sku_stock?: number }
}

export interface Coupon {
  id: number
  session_id: number
  type: 'discount' | 'threshold' | 'cash'
  threshold: number
  discount: number
  stock: number
  issued: number
  valid_from?: string
  valid_to?: string
}

export interface CouponIssuance {
  id: number
  coupon_id: number
  user_id?: number
  nickname?: string
  issued_at: string
  issued_by?: 'agent' | 'manual' | 'auto'
}

export interface Order {
  id: number
  session_id?: number
  store_id?: number
  status: 'pending' | 'paid' | 'cancelled' | 'refunded'
  total: number
  items?: OrderItem[]
  created_at?: string
}

export interface OrderItem {
  product_id: number
  product_name?: string
  sku_id?: number
  quantity: number
  price: number
}

export interface SalesDashboard {
  total_gmv: number
  order_count: number
  avg_order_value: number
  conversion_rate: number
  by_store?: Array<{ store_id: number; store_name: string; gmv: number; orders: number }>
  by_region?: Array<{ region: string; gmv: number; orders: number }>
  trend?: Array<{ date: string; gmv: number; orders: number }>
  anomalies?: Array<{ store_id: number; store_name: string; reason: string; metric: string; value: number }>
}

export interface DanmakuMessage {
  id: number | string
  session_id: number
  nickname: string
  content: string
  intent?: 'faq' | 'coupon' | 'stock' | 'human' | 'filter' | 'general' | string
  ai_reply?: string
  replied_by?: 'agent' | 'manual'
  handled_by?: string
  created_at: string
}

export interface AgentAction {
  id: number | string
  session_id: number
  action_time: string
  tool_name: string
  summary: string
  result?: string
  status?: 'success' | 'failed' | 'pending'
}

export interface MonitorEvent {
  id: number | string
  session_id: number
  event_type: string
  metric?: string
  value?: number
  response?: string
  status?: 'ok' | 'warn' | 'critical'
  created_at: string
}

export interface OperatorTicket {
  msg_id: number | string
  session_id: number
  nickname: string
  content: string
  intent: string
  priority: 'low' | 'medium' | 'high' | 'urgent'
  wait_seconds: number
  summary?: string
  status: 'pending' | 'claimed' | 'resolved' | 'closed'
  reply?: string
  created_at: string
}

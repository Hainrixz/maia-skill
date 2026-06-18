export interface ReportData {
  brand: string
  creator: string
  generated_at: string
  risk_profile: "conservative" | "moderate" | "aggressive"
  executive_summary: string
  macro_environment: MacroEnvironment
  portfolio_allocation: PortfolioAllocation
  cross_sector_insights: CrossSectorInsight[]
  risk_adjusted_picks: RiskAdjustedPick[]
  historical_accuracy: HistoricalAccuracy
  warnings: string[]
  sectors: Record<string, SectorData>
}

export interface MacroEnvironment {
  summary: string
  interest_rate_outlook: "rising" | "stable" | "falling"
  inflation_outlook: "rising" | "stable" | "falling"
  geopolitical_risk: "high" | "medium" | "low"
  key_factors: string[]
}

export type PortfolioAllocation = Record<string, number>

export interface CrossSectorInsight {
  insight: string
  implication: string
}

export interface RiskAdjustedPick {
  rank: number
  name: string
  symbol: string
  sector: string
  confidence: number
  risk_score: number
  risk_adjusted_score: number
  recommendation: "buy" | "hold" | "sell"
  reasoning: string
  position_size: string
}

export interface HistoricalAccuracy {
  previous_date: string | null
  calls_made: number
  calls_correct: number
  accuracy_pct: number
  notable: string
}

export interface SectorData {
  sector: string
  timestamp: string
  assets: Asset[]
  sector_summary: string
  sector_outlook: "bullish" | "bearish" | "neutral"
  top_pick: string
  top_pick_reasoning: string
  data_unavailable?: boolean
}

// Data Contract: monetary/numeric fields are numbers (or null when genuinely
// unavailable). Formatting ($, %, separators) happens only at render time via
// lib/utils formatters. change_* / ytd_change are signed percent numbers (2.3 = +2.3%).
export interface Asset {
  name: string
  symbol: string
  current_price: number | null
  price_unit?: string // "USD" | "USD/oz" | "USD/bbl" | "rate" | "index"
  change_24h: number | null
  change_7d: number | null
  change_30d: number | null
  ytd_change: number | null
  week_52_high: number | null
  week_52_low: number | null
  market_cap: number | null
  volume_24h: number | null
  // Freeform: real agent output exceeds simple enums (e.g. "cautiously optimistic").
  sentiment: string
  social_sentiment: string
  social_buzz: string
  confidence: number
  source_agreement: string
  data_source?: "api" | "api_alt" | "websearch" | "unavailable"
  sources_checked: string[]
  key_news: string[]
  social_highlights: string[]
  // Kept as an enum for internal sorting/filtering; relabeled analytically at render.
  recommendation: "buy" | "hold" | "sell"
  reasoning: string
}

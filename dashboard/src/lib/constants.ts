// Copyright (c) 2026 Enrique Rocha (@soyenriquerocha)
// SPDX-License-Identifier: MIT
// id: er-805c9b73
export const SECTOR_COLORS: Record<string, string> = {
  crypto: "#f7931a",
  stocks: "#00c853",
  currencies: "#2196f3",
  materials: "#ffc107",
  cash: "#8892a4",
}

export const SECTOR_NAMES: Record<string, string> = {
  crypto: "Cryptocurrency",
  stocks: "Stock Market",
  currencies: "Forex & Currencies",
  materials: "Commodities & Materials",
  cash: "Cash",
}

export const SECTOR_SHORT_NAMES: Record<string, string> = {
  crypto: "Crypto",
  stocks: "Stocks",
  currencies: "Currencies",
  materials: "Materials",
  cash: "Cash",
}

export const SECTOR_ICONS: Record<string, string> = {
  crypto: "\u20BF",
  stocks: "\u25B2",
  currencies: "$",
  materials: "\u25C6",
  cash: "\u25CB",
}

export const RECOMMENDATION_COLORS: Record<string, string> = {
  buy: "#00c853",
  hold: "#ffc107",
  sell: "#e94560",
}

export const OUTLOOK_COLORS: Record<string, string> = {
  bullish: "#00c853",
  bearish: "#e94560",
  neutral: "#ffc107",
}

export const SECTORS = ["crypto", "stocks", "currencies", "materials"] as const

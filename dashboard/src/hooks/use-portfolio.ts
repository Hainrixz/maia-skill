"use client"

import { useState, useEffect, useCallback } from "react"

export interface SoldEntry {
  id: string
  symbol: string
  name: string
  sector: string
  buyPrice: number
  buyDate: string
  quantity: number
  salePrice: number
  saleDate: string
  pnlAmount: number
  pnlPct: number
}

export interface PortfolioEntry {
  id: string
  symbol: string
  name: string
  sector: string
  buyPrice: number
  quantity: number
  buyDate: string // ISO 8601
  // Enriched by portfolio_fetch.py
  currentPrice?: number | null
  pnlPct?: number | null
  pnlAmount?: number | null
  rsi?: number | null
  trend?: string | null
  change1d?: number | null
  change7d?: number | null
  change30d?: number | null
  analystTarget?: number | null
  analystUpside?: number | null
  forwardPe?: number | null
  weekHigh52?: number | null
  weekLow52?: number | null
  updatedAt?: string | null
}

async function fetchPortfolio(): Promise<PortfolioEntry[]> {
  try {
    const res = await fetch("/api/portfolio", { cache: "no-store" })
    if (!res.ok) return []
    return res.json()
  } catch {
    return []
  }
}

async function fetchSold(): Promise<SoldEntry[]> {
  try {
    const res = await fetch("/api/portfolio-sold", { cache: "no-store" })
    if (!res.ok) return []
    return res.json()
  } catch {
    return []
  }
}

async function persistPortfolio(entries: PortfolioEntry[]) {
  try {
    await fetch("/api/portfolio", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(entries),
    })
  } catch {
    // fail silently — data already in React state
  }
}

export function usePortfolio() {
  const [entries, setEntries] = useState<PortfolioEntry[]>([])
  const [soldEntries, setSoldEntries] = useState<SoldEntry[]>([])

  // Load from server on mount
  useEffect(() => {
    fetchPortfolio().then(setEntries)
    fetchSold().then(setSoldEntries)
  }, [])

  const addEntry = useCallback(
    (
      pick: { symbol: string; name: string; sector: string },
      buyPrice: number,
      quantity: number
    ) => {
      const newEntry: PortfolioEntry = {
        id: `${pick.symbol}-${Date.now()}`,
        symbol: pick.symbol,
        name: pick.name,
        sector: pick.sector,
        buyPrice,
        quantity,
        buyDate: new Date().toISOString(),
      }
      setEntries((prev) => {
        const updated = [...prev, newEntry]
        persistPortfolio(updated)
        return updated
      })
    },
    []
  )

  const removeEntry = useCallback((id: string) => {
    setEntries((prev) => {
      const updated = prev.filter((e) => e.id !== id)
      persistPortfolio(updated)
      return updated
    })
  }, [])

  const sellEntry = useCallback(
    (id: string, salePrice: number, sellQty: number) => {
      setEntries((prev) => {
        const entry = prev.find((e) => e.id === id)
        if (!entry) return prev
        const qty = Math.min(Math.max(1, sellQty), entry.quantity)
        const pnlAmount = (salePrice - entry.buyPrice) * qty
        const pnlPct = ((salePrice - entry.buyPrice) / entry.buyPrice) * 100
        const soldRecord: SoldEntry = {
          id: entry.id,
          symbol: entry.symbol,
          name: entry.name,
          sector: entry.sector,
          buyPrice: entry.buyPrice,
          buyDate: entry.buyDate,
          quantity: qty,
          salePrice,
          saleDate: new Date().toISOString(),
          pnlAmount: Math.round(pnlAmount * 100) / 100,
          pnlPct: Math.round(pnlPct * 100) / 100,
        }
        fetch("/api/portfolio-sold", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(soldRecord),
        }).catch(() => {})
        setSoldEntries((s) => [...s, soldRecord])
        let updated: PortfolioEntry[]
        if (qty >= entry.quantity) {
          updated = prev.filter((e) => e.id !== id)
        } else {
          updated = prev.map((e) =>
            e.id === id ? { ...e, quantity: e.quantity - qty } : e
          )
        }
        persistPortfolio(updated)
        return updated
      })
    },
    []
  )

  const clearAll = useCallback(() => {
    setEntries([])
    persistPortfolio([])
  }, [])

  const hasSymbol = useCallback(
    (symbol: string) => entries.some((e) => e.symbol === symbol),
    [entries]
  )

  const countForSymbol = useCallback(
    (symbol: string) =>
      entries
        .filter((e) => e.symbol === symbol)
        .reduce((sum, e) => sum + e.quantity, 0),
    [entries]
  )

  return { entries, soldEntries, addEntry, removeEntry, sellEntry, clearAll, hasSymbol, countForSymbol }
}

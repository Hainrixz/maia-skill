"use client"

import { useState, useEffect, useCallback } from "react"

export interface PortfolioEntry {
  id: string
  symbol: string
  name: string
  sector: string
  buyPrice: number
  quantity: number
  buyDate: string // ISO 8601
}

const STORAGE_KEY = "tododeia_portfolio"

function loadFromStorage(): PortfolioEntry[] {
  if (typeof window === "undefined") return []
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return []
    return JSON.parse(raw) as PortfolioEntry[]
  } catch {
    return []
  }
}

function saveToStorage(entries: PortfolioEntry[]) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(entries))
  } catch {
    // storage quota exceeded or private mode — fail silently
  }
}

export function usePortfolio() {
  const [entries, setEntries] = useState<PortfolioEntry[]>([])

  // Load once on mount (client-side only)
  useEffect(() => {
    setEntries(loadFromStorage())
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
        saveToStorage(updated)
        return updated
      })
    },
    []
  )

  const removeEntry = useCallback((id: string) => {
    setEntries((prev) => {
      const updated = prev.filter((e) => e.id !== id)
      saveToStorage(updated)
      return updated
    })
  }, [])

  const clearAll = useCallback(() => {
    setEntries([])
    saveToStorage([])
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

  return { entries, addEntry, removeEntry, clearAll, hasSymbol, countForSymbol }
}

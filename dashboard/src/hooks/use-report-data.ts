"use client"

import { useState, useEffect } from "react"
import type { ReportData, SectorData } from "@/types/report"

const REC_MAP: Record<string, "buy" | "hold" | "sell"> = {
  buy: "buy", comprar: "buy",
  sell: "sell", vender: "sell",
  dca: "hold", hold: "hold", wait: "hold", esperar: "hold", vigilancia: "hold",
}

function buildSectorsFromPicks(report: ReportData): Record<string, SectorData> {
  const picks = report.risk_adjusted_picks
  const result: Record<string, SectorData> = {}
  const sectorKeys = ["crypto", "stocks", "materials"] as const

  for (const key of sectorKeys) {
    const CRYPTO_SECTORS = ["crypto", "cripto"]
    const MATERIALS_SECTORS = ["materials", "materiales", "commodities"]
    const STOCK_SECTORS = ["stocks", "acciones", "energy", "technology", "healthcare", "finance", "financials", "payments", "industrials", "consumer"]
    const sp = picks.filter((p) => {
      if (key === "crypto") return CRYPTO_SECTORS.includes(p.sector)
      if (key === "materials") return MATERIALS_SECTORS.includes(p.sector)
      if (key === "stocks") return STOCK_SECTORS.includes(p.sector)
      return p.sector === key
    })
    if (sp.length === 0) continue
    const top = [...sp].sort((a, b) => b.risk_adjusted_score - a.risk_adjusted_score)[0]
    const buyCount = sp.filter((p) => REC_MAP[(p as any).recommendation] === "buy").length
    const outlook = buyCount > sp.length / 2 ? "bullish" : buyCount > 0 ? "neutral" : ("bearish" as const)

    result[key] = {
      sector: key,
      timestamp: report.generated_at,
      sector_summary: (top.reasoning ?? "").split(". ").slice(0, 2).join(". "),
      sector_outlook: outlook,
      top_pick: top.symbol,
      top_pick_reasoning: (top.reasoning ?? "").split(". ")[0],
      assets: sp.map((pick) => {
        const p = pick as any
        const fmt = (v: number) => v >= 1000 ? `$${(v / 1000).toFixed(1)}K` : `$${v}`
        const stop = p.stop_loss != null ? `-${fmt(p.stop_loss)}` : ""
        const target = p.target_12m != null ? `+${fmt(p.target_12m)}` : ""
        const rr = p.risk_reward_ratio ?? ""
        const score = p.risk_adjusted_score != null ? String(p.risk_adjusted_score) : ""
        const conf52 = pick.confidence != null ? String(pick.confidence) : ""
        const risk52 = p.risk_score != null ? String(p.risk_score) : ""
        return ({
        name: pick.name,
        symbol: pick.symbol,
        current_price: p.entry_price != null ? `$${Number(p.entry_price).toLocaleString()}` : "N/A",
        change_24h: stop, change_7d: target, change_30d: rr, ytd_change: score,
        week_52_high: conf52, week_52_low: risk52, market_cap: "", volume_24h: "",
        sentiment: (REC_MAP[(pick as any).recommendation] === "buy" ? "bullish" : "neutral") as "bullish" | "neutral" | "bearish",
        social_sentiment: (REC_MAP[(pick as any).recommendation] === "buy" ? "bullish" : "neutral") as "bullish" | "bearish" | "neutral" | "mixed",
        social_buzz: (pick.confidence >= 8 ? "high" : "medium") as "high" | "medium" | "low",
        source_agreement: (pick.confidence >= 8 ? "high" : pick.confidence >= 6 ? "medium" : "low") as "high" | "medium" | "low",
        confidence: pick.confidence,
        sources_checked: [],
        key_news: (pick.reasoning ?? "").split(". ").filter((s) => s.trim().length > 10).slice(0, 4),
        social_highlights: [],
        recommendation: REC_MAP[(pick as any).recommendation] ?? "hold",
        reasoning: pick.reasoning ?? "",
      })
      }),
    }
  }
  return result
}

function sanitizeReportData(report: ReportData): ReportData {
  const { currencies: _removedAllocation, ...portfolioAllocation } = report.portfolio_allocation as ReportData["portfolio_allocation"] & {
    currencies?: number
  }
  const rawSectors = report.sectors ?? {}
  const { currencies: _removedSector, ...strippedSectors } = rawSectors as typeof rawSectors & { currencies?: unknown }
  const hasSectors = Object.keys(strippedSectors).length > 0
  const sectors = hasSectors ? strippedSectors : buildSectorsFromPicks(report)

  const rawAcc = (report as any).historical_accuracy as Record<string, any> ?? {}
  const tracking: Array<Record<string, any>> = rawAcc.picks_tracking ?? []
  // Prefer direct integer fields from Strategy Agent output (calls_made, calls_correct, accuracy_pct).
  // Fall back to picks_tracking array computation for legacy report formats.
  const callsMade = rawAcc.calls_made ?? tracking.length
  const callsCorrect = rawAcc.calls_correct ?? tracking.filter((t) => typeof t.change_pct === "number" && t.change_pct >= 0).length
  const accuracyPct = rawAcc.accuracy_pct ?? (callsMade > 0 ? Math.round((callsCorrect / callsMade) * 100) : 0)
  const historical_accuracy = {
    previous_date: rawAcc.previous_date ?? (rawAcc.previous_timestamp ? rawAcc.previous_timestamp.split("T")[0] : (rawAcc.previous_report ?? null)),
    calls_made: callsMade,
    calls_correct: callsCorrect,
    accuracy_pct: accuracyPct,
    notable: rawAcc.notable ?? rawAcc.market_note ?? "",
  }

  return {
    ...report,
    warnings: (report as any).warnings ?? [],
    portfolio_allocation: portfolioAllocation,
    risk_adjusted_picks: report.risk_adjusted_picks.filter((pick) => pick.sector !== "currencies"),
    sectors,
    historical_accuracy,
  }
}

export function useReportData() {
  const [data, setData] = useState<ReportData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setLoading(true)
    setError(null)

    fetch("/data/report.json")
      .then((res) => {
        if (!res.ok) throw new Error(`Failed to load report data: ${res.status}`)
        return res.json()
      })
      .then((report) => setData(sanitizeReportData(report)))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  return { data, loading, error }
}

"use client"

import { useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { useLanguage } from "@/hooks/use-language"
import { usePortfolio, type PortfolioEntry, type SoldEntry } from "@/hooks/use-portfolio"
import type { ReportData } from "@/types/report"
import { SECTOR_COLORS } from "@/lib/constants"

interface PortfolioTabProps {
  data: ReportData
}

function parsePriceNumber(priceStr: string): number | null {
  if (!priceStr) return null
  const cleaned = priceStr.replace(/[$,]/g, "")
  const hasK = priceStr.includes("K")
  const n = parseFloat(cleaned.replace("K", ""))
  if (isNaN(n)) return null
  return hasK ? n * 1000 : n
}

function getCurrentPrice(symbol: string, data: ReportData): number | null {
  for (const sectorData of Object.values(data.sectors)) {
    const asset = sectorData?.assets?.find((a) => a.symbol === symbol)
    if (asset?.current_price) return parsePriceNumber(asset.current_price)
  }
  return null
}

function formatCurrency(n: number): string {
  if (Math.abs(n) >= 1000) return `$${n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
  return `$${n.toFixed(2)}`
}

function formatDate(isoDate: string): string {
  try {
    return new Date(isoDate).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })
  } catch {
    return isoDate
  }
}

interface RowPnL {
  currentPrice: number | null
  pnlAmount: number | null
  pnlPct: number | null
  totalCost: number
}

function computeRowPnL(entry: PortfolioEntry, data: ReportData): RowPnL {
  const totalCost = entry.buyPrice * entry.quantity

  // Prefer pre-fetched fields stored directly in portfolio.json
  if (entry.currentPrice != null) {
    const currentPrice = entry.currentPrice
    const pnlAmount = (currentPrice - entry.buyPrice) * entry.quantity
    const pnlPct = ((currentPrice - entry.buyPrice) / entry.buyPrice) * 100
    return { currentPrice, pnlAmount, pnlPct, totalCost }
  }

  // Fallback: look up in today's report sectors (covers tickers screened today)
  const currentPrice = getCurrentPrice(entry.symbol, data)
  if (currentPrice == null) return { currentPrice: null, pnlAmount: null, pnlPct: null, totalCost }
  const pnlAmount = (currentPrice - entry.buyPrice) * entry.quantity
  const pnlPct = ((currentPrice - entry.buyPrice) / entry.buyPrice) * 100
  return { currentPrice, pnlAmount, pnlPct, totalCost }
}

export function PortfolioTab({ data }: PortfolioTabProps) {
  const { t } = useLanguage()
  const { entries, soldEntries, removeEntry, sellEntry, clearAll } = usePortfolio()
  const [sellOpenId, setSellOpenId] = useState<string | null>(null)
  const [sellQty, setSellQty] = useState(1)

  const rowData = entries.map((e) => ({ entry: e, ...computeRowPnL(e, data) }))
  const totalCost = rowData.reduce((s, r) => s + r.totalCost, 0)
  const totalPnl = rowData.reduce((s, r) => s + (r.pnlAmount ?? 0), 0)
  const totalPnlPct = totalCost > 0 ? (totalPnl / totalCost) * 100 : 0
  const totalPnlPositive = totalPnl >= 0

  return (
    <motion.section
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
    >
      <div className="mb-5 flex items-center justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-[#8B8B85]">
            {t("portfolio.kicker")}
          </p>
          <h2 className="text-2xl font-bold tracking-tight text-[#252420]">
            {t("portfolio.title")}
          </h2>
        </div>
        {entries.length > 0 && (
          <button
            onClick={() => { if (window.confirm(t("portfolio.clearConfirm"))) clearAll() }}
            className="rounded-md border border-red-200 px-3 py-1.5 text-xs font-semibold text-red-500 transition-colors hover:bg-red-50"
          >
            {t("portfolio.clearAll")}
          </button>
        )}
      </div>

      {entries.length === 0 ? (
        <div className="rounded-xl border border-[#E6E6E4] bg-[#FCFCFB] p-10 text-center">
          <p className="text-2xl mb-2">📭</p>
          <p className="text-sm font-medium text-[#4D4A44]">{t("portfolio.empty")}</p>
          <p className="mt-1 text-xs text-[#8B8B85]">{t("portfolio.emptyHint")}</p>
        </div>
      ) : (
        <>
          {/* Summary bar */}
          <div className="mb-4 grid grid-cols-3 gap-3">
            <div className="rounded-xl border border-[#E6E6E4] bg-[#FCFCFB] p-4">
              <p className="text-[10px] font-semibold uppercase tracking-wider text-[#8B8B85]">{t("portfolio.positions")}</p>
              <p className="mt-1 text-2xl font-bold text-[#252420]">{entries.length}</p>
            </div>
            <div className="rounded-xl border border-[#E6E6E4] bg-[#FCFCFB] p-4">
              <p className="text-[10px] font-semibold uppercase tracking-wider text-[#8B8B85]">{t("portfolio.invested")}</p>
              <p className="mt-1 text-2xl font-bold text-[#252420]">{formatCurrency(totalCost)}</p>
            </div>
            <div className={`rounded-xl border p-4 ${totalPnlPositive ? "border-green-200 bg-green-50" : "border-red-200 bg-red-50"}`}>
              <p className="text-[10px] font-semibold uppercase tracking-wider text-[#8B8B85]">{t("portfolio.totalPnl")}</p>
              <p className={`mt-1 text-2xl font-bold ${totalPnlPositive ? "text-green-600" : "text-red-600"}`}>
                {totalPnlPositive ? "+" : ""}{formatCurrency(totalPnl)}
              </p>
              <p className={`text-xs font-medium ${totalPnlPositive ? "text-green-500" : "text-red-500"}`}>
                {totalPnlPositive ? "+" : ""}{totalPnlPct.toFixed(2)}%
              </p>
            </div>
          </div>

          {/* Table */}
          <div className="overflow-x-auto rounded-xl border border-[#E6E6E4]">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[#E6E6E4] bg-[#F7F7F5]">
                  <th className="px-4 py-3 text-left text-[10px] font-semibold uppercase tracking-wider text-[#8B8B85]">{t("portfolio.col.asset")}</th>
                  <th className="px-4 py-3 text-left text-[10px] font-semibold uppercase tracking-wider text-[#8B8B85]">{t("portfolio.col.date")}</th>
                  <th className="px-4 py-3 text-right text-[10px] font-semibold uppercase tracking-wider text-[#8B8B85]">{t("portfolio.col.qty")}</th>
                  <th className="px-4 py-3 text-right text-[10px] font-semibold uppercase tracking-wider text-[#8B8B85]">{t("portfolio.col.buyPrice")}</th>
                  <th className="px-4 py-3 text-right text-[10px] font-semibold uppercase tracking-wider text-[#8B8B85]">{t("portfolio.col.cost")}</th>
                  <th className="px-4 py-3 text-right text-[10px] font-semibold uppercase tracking-wider text-[#8B8B85]">{t("portfolio.col.current")}</th>
                  <th className="px-4 py-3 text-right text-[10px] font-semibold uppercase tracking-wider text-[#8B8B85]">{t("portfolio.col.pnl")}</th>
                  <th className="px-4 py-3 text-right text-[10px] font-semibold uppercase tracking-wider text-[#8B8B85]">{t("portfolio.col.pnlPct")}</th>
                  <th className="px-4 py-3"></th>
                </tr>
              </thead>
              <tbody>
                <AnimatePresence>
                  {rowData.map(({ entry, currentPrice, pnlAmount, pnlPct, totalCost: rowCost }) => {
                    const positive = (pnlAmount ?? 0) >= 0
                    const sectorColor = SECTOR_COLORS[entry.sector] ?? "#8B8B85"
                    return (
                      <motion.tr
                        key={entry.id}
                        initial={{ opacity: 0, x: -8 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: 8 }}
                        transition={{ duration: 0.15 }}
                        className="border-b border-[#F0F0ED] bg-[#FCFCFB] last:border-0 hover:bg-[#F7F7F5]"
                      >
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2">
                            <span className="h-2 w-2 rounded-full shrink-0" style={{ backgroundColor: sectorColor }} />
                            <div>
                              <p className="font-semibold text-[#252420]">{entry.symbol}</p>
                              <p className="text-[11px] text-[#8B8B85] truncate max-w-[140px]">{entry.name}</p>
                            </div>
                          </div>
                        </td>
                        <td className="px-4 py-3 text-[#4D4A44]">{formatDate(entry.buyDate)}</td>
                        <td className="px-4 py-3 text-right font-medium text-[#252420]">{entry.quantity}</td>
                        <td className="px-4 py-3 text-right text-[#4D4A44]">{formatCurrency(entry.buyPrice)}</td>
                        <td className="px-4 py-3 text-right text-[#4D4A44]">{formatCurrency(rowCost)}</td>
                        <td className="px-4 py-3 text-right font-medium text-[#252420]">
                          {currentPrice != null ? formatCurrency(currentPrice) : <span className="text-[#8B8B85]">—</span>}
                        </td>
                        <td className={`px-4 py-3 text-right font-semibold ${pnlAmount == null ? "text-[#8B8B85]" : positive ? "text-green-600" : "text-red-600"}`}>
                          {pnlAmount == null ? "—" : `${positive ? "+" : ""}${formatCurrency(pnlAmount)}`}
                        </td>
                        <td className={`px-4 py-3 text-right font-semibold ${pnlPct == null ? "text-[#8B8B85]" : positive ? "text-green-600" : "text-red-600"}`}>
                          {pnlPct == null ? "—" : `${positive ? "+" : ""}${pnlPct.toFixed(2)}%`}
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center justify-end gap-1">
                            {sellOpenId === entry.id ? (
                              <>
                                <button
                                  onClick={() => setSellQty((q) => Math.max(1, q - 1))}
                                  className="flex h-6 w-6 items-center justify-center rounded border border-[#E6E6E4] bg-white text-xs font-bold text-[#252420] hover:bg-[#F7F7F5]"
                                >−</button>
                                <input
                                  type="number"
                                  min={1}
                                  max={entry.quantity}
                                  value={sellQty}
                                  onChange={(e) => {
                                    const v = parseInt(e.target.value)
                                    if (!isNaN(v)) setSellQty(Math.min(Math.max(1, v), entry.quantity))
                                  }}
                                  className="w-10 rounded border border-[#E6E6E4] bg-white px-1 py-0.5 text-center text-xs font-medium text-[#252420] focus:border-[#37352F] focus:outline-none"
                                />
                                <button
                                  onClick={() => setSellQty((q) => Math.min(q + 1, entry.quantity))}
                                  className="flex h-6 w-6 items-center justify-center rounded border border-[#E6E6E4] bg-white text-xs font-bold text-[#252420] hover:bg-[#F7F7F5]"
                                >+</button>
                                {currentPrice != null && (
                                  <button
                                    onClick={() => {
                                      sellEntry(entry.id, currentPrice, sellQty)
                                      setSellOpenId(null)
                                      setSellQty(1)
                                    }}
                                    className="rounded bg-green-500 px-2 py-0.5 text-[11px] font-semibold text-white hover:bg-green-600"
                                  >OK</button>
                                )}
                                <button
                                  onClick={() => { setSellOpenId(null); setSellQty(1) }}
                                  className="rounded px-1 py-0.5 text-xs text-[#8B8B85] hover:text-[#252420]"
                                >✕</button>
                              </>
                            ) : (
                              <>
                                {currentPrice != null && (
                                  <button
                                    onClick={() => { setSellOpenId(entry.id); setSellQty(1) }}
                                    aria-label="Sell position"
                                    className="rounded p-1 text-[#C0C0BB] transition-colors hover:bg-green-50 hover:text-green-500"
                                  >
                                    <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                                      <circle cx="7" cy="7" r="6" stroke="currentColor" strokeWidth="1.2" />
                                      <path d="M7 4v6M5 8.5l2 2 2-2" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" />
                                    </svg>
                                  </button>
                                )}
                                <button
                                  onClick={() => removeEntry(entry.id)}
                                  aria-label="Remove position"
                                  className="rounded p-1 text-[#C0C0BB] transition-colors hover:bg-red-50 hover:text-red-400"
                                >
                                  <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                                    <path d="M1 3h12M5 3V2h4v1M2 3l1 9h8l1-9" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" />
                                  </svg>
                                </button>
                              </>
                            )}
                          </div>
                        </td>
                      </motion.tr>
                    )
                  })}
                </AnimatePresence>
              </tbody>
            </table>
          </div>

          {/* Sold history */}
          {soldEntries.length > 0 && (
            <div className="mt-8">
              <h3 className="mb-3 text-sm font-semibold uppercase tracking-wider text-[#8B8B85]">Historial de Ventas</h3>
              <div className="overflow-x-auto rounded-xl border border-[#E6E6E4]">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-[#E6E6E4] bg-[#F7F7F5]">
                      <th className="px-4 py-3 text-left text-[10px] font-semibold uppercase tracking-wider text-[#8B8B85]">Activo</th>
                      <th className="px-4 py-3 text-left text-[10px] font-semibold uppercase tracking-wider text-[#8B8B85]">Fecha Compra</th>
                      <th className="px-4 py-3 text-left text-[10px] font-semibold uppercase tracking-wider text-[#8B8B85]">Fecha Venta</th>
                      <th className="px-4 py-3 text-right text-[10px] font-semibold uppercase tracking-wider text-[#8B8B85]">Cant.</th>
                      <th className="px-4 py-3 text-right text-[10px] font-semibold uppercase tracking-wider text-[#8B8B85]">P. Compra</th>
                      <th className="px-4 py-3 text-right text-[10px] font-semibold uppercase tracking-wider text-[#8B8B85]">P. Venta</th>
                      <th className="px-4 py-3 text-right text-[10px] font-semibold uppercase tracking-wider text-[#8B8B85]">P&L $</th>
                      <th className="px-4 py-3 text-right text-[10px] font-semibold uppercase tracking-wider text-[#8B8B85]">P&L %</th>
                    </tr>
                  </thead>
                  <tbody>
                    {soldEntries.map((sold: SoldEntry) => {
                      const positive = sold.pnlAmount >= 0
                      const sectorColor = SECTOR_COLORS[sold.sector] ?? "#8B8B85"
                      return (
                        <tr key={`${sold.id}-${sold.saleDate}`} className="border-b border-[#F0F0ED] bg-[#FCFCFB] last:border-0">
                          <td className="px-4 py-3">
                            <div className="flex items-center gap-2">
                              <span className="h-2 w-2 rounded-full shrink-0" style={{ backgroundColor: sectorColor }} />
                              <div>
                                <p className="font-semibold text-[#252420]">{sold.symbol}</p>
                                <p className="text-[11px] text-[#8B8B85] truncate max-w-[120px]">{sold.name}</p>
                              </div>
                            </div>
                          </td>
                          <td className="px-4 py-3 text-[#4D4A44]">{formatDate(sold.buyDate)}</td>
                          <td className="px-4 py-3 text-[#4D4A44]">{formatDate(sold.saleDate)}</td>
                          <td className="px-4 py-3 text-right font-medium text-[#252420]">{sold.quantity}</td>
                          <td className="px-4 py-3 text-right text-[#4D4A44]">{formatCurrency(sold.buyPrice)}</td>
                          <td className="px-4 py-3 text-right text-[#4D4A44]">{formatCurrency(sold.salePrice)}</td>
                          <td className={`px-4 py-3 text-right font-semibold ${positive ? "text-green-600" : "text-red-600"}`}>
                            {positive ? "+" : ""}{formatCurrency(sold.pnlAmount)}
                          </td>
                          <td className={`px-4 py-3 text-right font-semibold ${positive ? "text-green-600" : "text-red-600"}`}>
                            {positive ? "+" : ""}{sold.pnlPct.toFixed(2)}%
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </motion.section>
  )
}

"use client"

import { useState, useRef, useEffect } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { useLanguage } from "@/hooks/use-language"
import { usePortfolio } from "@/hooks/use-portfolio"
import type { RiskAdjustedPick, SectorData } from "@/types/report"
import { SECTOR_COLORS } from "@/lib/constants"

interface PickCardProps { pick: RiskAdjustedPick; sectors: Record<string, SectorData> }

const recStyles: Record<string, string> = {
  buy: "bg-green-50 text-green-700 border-green-200",
  hold: "bg-amber-50 text-amber-700 border-amber-200",
  sell: "bg-red-50 text-red-700 border-red-200",
}

function parsePriceNumber(priceStr: string): number | null {
  if (!priceStr) return null
  const cleaned = priceStr.replace(/[$,K]/g, "")
  const n = parseFloat(cleaned)
  if (isNaN(n)) return null
  // handle "K" suffix
  if (priceStr.includes("K")) return n * 1000
  return n
}

export function PickCard({ pick, sectors }: PickCardProps) {
  const { t } = useLanguage()
  const { addEntry, hasSymbol, countForSymbol } = usePortfolio()
  const score = pick.risk_adjusted_score ?? pick.confidence
  const scorePercent = Math.min(score * 10, 100)
  const scoreColor = score >= 7 ? "#00c853" : score >= 4 ? "#ffc107" : "#e94560"
  const confLabel = pick.risk_adjusted_score ? t("picks.riskAdj") : t("picks.confidence")
  // Search all sectors for the asset — pick.sector key may not match the sector object keys
  const asset = Object.values(sectors).flatMap((s) => s?.assets ?? []).find((a) => a.symbol === pick.symbol)
  const price = asset?.current_price ?? ((pick as any).entry_price != null ? `$${Number((pick as any).entry_price).toLocaleString()}` : "")
  const priceNum = parsePriceNumber(price) ?? ((pick as any).entry_price != null ? Number((pick as any).entry_price) : null)

  const [formOpen, setFormOpen] = useState(false)
  const [quantity, setQuantity] = useState(1)
  const [confirmed, setConfirmed] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  const alreadyOwned = hasSymbol(pick.symbol)
  const ownedQty = countForSymbol(pick.symbol)

  // Focus input when form opens
  useEffect(() => {
    if (formOpen) inputRef.current?.focus()
  }, [formOpen])

  function handleConfirm() {
    if (!priceNum || quantity < 1) return
    addEntry({ symbol: pick.symbol, name: pick.name, sector: pick.sector }, priceNum, quantity)
    setConfirmed(true)
    setFormOpen(false)
    setTimeout(() => setConfirmed(false), 3000)
    setQuantity(1)
  }

  function handleQtyChange(val: string) {
    const n = parseInt(val, 10)
    if (!isNaN(n) && n >= 1) setQuantity(n)
    else if (val === "") setQuantity(1)
  }

  return (
    <motion.div layout initial={{ opacity: 0, scale: 0.97 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.97 }} transition={{ duration: 0.2 }} className="group relative rounded-xl border border-[#E6E6E4] bg-[#FCFCFB] p-5 transition-all hover:border-[#D0D0CE] hover:shadow-md">
      <div className="absolute right-4 top-4 flex h-8 w-8 items-center justify-center rounded-full bg-[#37352F] text-xs font-bold text-white">#{pick.rank}</div>
      <span className="mb-2 inline-block rounded-full px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider" style={{ backgroundColor: `${SECTOR_COLORS[pick.sector]}15`, color: SECTOR_COLORS[pick.sector] }}>
        {t(`sector.${pick.sector}.short`)}
      </span>
      <div className="text-lg font-bold text-[#252420]">{pick.name}</div>
      <div className="mb-2 text-sm text-[#8B8B85]">{pick.symbol}</div>
      {price && <div className="mb-2 text-2xl font-bold text-[#252420]">{price}</div>}
      <div className="mb-3 flex flex-wrap gap-1.5">
        <span className={`inline-block rounded-full border px-3 py-0.5 text-xs font-semibold uppercase ${recStyles[pick.recommendation]}`}>{pick.recommendation}</span>
        {pick.risk_score != null && <span className="inline-block rounded-full border border-[#E6E6E4] bg-[#F7F7F5] px-3 py-0.5 text-xs text-[#8B8B85]">{t("picks.risk")} {pick.risk_score}/10</span>}
        {pick.position_size && <span className="inline-block rounded-full border border-blue-200 bg-blue-50 px-3 py-0.5 text-xs text-blue-700">{pick.position_size}</span>}
      </div>
      <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-[#F0F0ED]">
        <motion.div initial={{ width: 0 }} animate={{ width: `${scorePercent}%` }} transition={{ delay: 0.3, duration: 0.6 }} className="h-full rounded-full" style={{ backgroundColor: scoreColor }} />
      </div>
      <div className="mt-1 flex justify-between text-[11px] text-[#8B8B85]">
        <span>{confLabel}</span>
        <span className="font-medium">{score}/10</span>
      </div>
      <p className="mt-3 text-sm leading-relaxed text-[#4D4A44]">{pick.reasoning}</p>

      {/* TP / SL pills */}
      {(pick.stop_loss != null || pick.target_12m != null) && (
        <div className="mt-3 flex flex-wrap gap-2 border-t border-[#F0F0ED] pt-3">
          {pick.target_12m != null && (
            <span className="inline-flex items-center gap-1 rounded-full border border-green-200 bg-green-50 px-2.5 py-0.5 text-xs font-semibold text-green-700">
              🎯 ${pick.target_12m.toLocaleString()}
            </span>
          )}
          {pick.stop_loss != null && (
            <span className="inline-flex items-center gap-1 rounded-full border border-red-200 bg-red-50 px-2.5 py-0.5 text-xs font-semibold text-red-700">
              🛑 ${pick.stop_loss.toLocaleString()}
            </span>
          )}
          {pick.risk_reward_ratio != null && (
            <span className="inline-flex items-center gap-1 rounded-full border border-[#E6E6E4] bg-[#F7F7F5] px-2.5 py-0.5 text-xs text-[#4D4A44]">
              R/R {pick.risk_reward_ratio}x
            </span>
          )}
        </div>
      )}

      {/* Portfolio section */}
      {priceNum != null && (
        <div className="mt-4 border-t border-[#F0F0ED] pt-3">
          <AnimatePresence mode="wait">
            {formOpen ? (
              <motion.div
                key="form"
                initial={{ opacity: 0, y: -4 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -4 }}
                transition={{ duration: 0.15 }}
                className="flex items-center gap-2"
              >
                <span className="text-xs text-[#8B8B85] shrink-0">{t("portfolio.qty")}</span>
                <button
                  onClick={() => setQuantity((q) => Math.max(1, q - 1))}
                  className="flex h-7 w-7 items-center justify-center rounded-md border border-[#E6E6E4] bg-white text-sm font-bold text-[#252420] hover:bg-[#F7F7F5] active:scale-95"
                >−</button>
                <input
                  ref={inputRef}
                  type="number"
                  min={1}
                  value={quantity}
                  onChange={(e) => handleQtyChange(e.target.value)}
                  onKeyDown={(e) => { if (e.key === "Enter") handleConfirm(); if (e.key === "Escape") setFormOpen(false) }}
                  className="w-14 rounded-md border border-[#E6E6E4] bg-white px-2 py-1 text-center text-sm font-medium text-[#252420] focus:border-[#37352F] focus:outline-none"
                />
                <button
                  onClick={() => setQuantity((q) => q + 1)}
                  className="flex h-7 w-7 items-center justify-center rounded-md border border-[#E6E6E4] bg-white text-sm font-bold text-[#252420] hover:bg-[#F7F7F5] active:scale-95"
                >+</button>
                <button
                  onClick={handleConfirm}
                  className="ml-1 rounded-md bg-[#37352F] px-3 py-1 text-xs font-semibold text-white hover:bg-[#1a1916] active:scale-95"
                >{t("portfolio.confirm")}</button>
                <button
                  onClick={() => { setFormOpen(false); setQuantity(1) }}
                  className="rounded-md px-2 py-1 text-xs text-[#8B8B85] hover:text-[#252420]"
                >✕</button>
              </motion.div>
            ) : confirmed ? (
              <motion.div
                key="confirmed"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="flex items-center gap-1.5 text-xs font-semibold text-green-600"
              >
                <span>✓</span>
                <span>{t("portfolio.added")}</span>
              </motion.div>
            ) : (
              <motion.div
                key="button"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="flex items-center gap-2"
              >
                <button
                  onClick={() => setFormOpen(true)}
                  className="rounded-md border border-[#E6E6E4] bg-white px-3 py-1.5 text-xs font-semibold text-[#4D4A44] transition-colors hover:border-[#37352F] hover:text-[#252420] active:scale-95"
                >
                  + {t("portfolio.addBtn")}
                </button>
                {alreadyOwned && (
                  <span className="text-xs text-[#8B8B85]">
                    ✓ {ownedQty} {t("portfolio.owned")}
                  </span>
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )}
    </motion.div>
  )
}

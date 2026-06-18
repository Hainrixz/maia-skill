"use client"

import { motion } from "framer-motion"
import { useLanguage } from "@/hooks/use-language"
import type { RiskAdjustedPick, SectorData } from "@/types/report"
import { SECTOR_COLORS } from "@/lib/constants"
import { formatPrice } from "@/lib/utils"

interface PickCardProps { pick: RiskAdjustedPick; sectors: Record<string, SectorData> }

const recStyles: Record<string, string> = {
  buy: "bg-green-50 text-green-700 border-green-200",
  hold: "bg-amber-50 text-amber-700 border-amber-200",
  sell: "bg-red-50 text-red-700 border-red-200",
}

export function PickCard({ pick, sectors }: PickCardProps) {
  const { t, lang } = useLanguage()
  const score = pick.risk_adjusted_score ?? pick.confidence
  const scorePercent = Math.min(score * 10, 100)
  const scoreColor = score >= 7 ? "#00c853" : score >= 4 ? "#ffc107" : "#e94560"
  const confLabel = pick.risk_adjusted_score ? t("picks.riskAdj") : t("picks.confidence")
  const sectorData = sectors[pick.sector]
  const asset = sectorData?.assets?.find((a) => a.symbol === pick.symbol)
  const price = formatPrice(asset?.current_price ?? null, asset?.price_unit, lang)

  return (
    <motion.div layout initial={{ opacity: 0, scale: 0.97 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.97 }} transition={{ duration: 0.2 }} className="group relative rounded-xl border border-[#E6E6E4] bg-[#FCFCFB] p-5 transition-all hover:border-[#D0D0CE] hover:shadow-md">
      <div className="absolute right-4 top-4 flex h-8 w-8 items-center justify-center rounded-full bg-[#37352F] text-xs font-bold text-white">#{pick.rank}</div>
      <span className="mb-2 inline-block rounded-full px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider" style={{ backgroundColor: `${SECTOR_COLORS[pick.sector]}15`, color: SECTOR_COLORS[pick.sector] }}>
        {t(`sector.${pick.sector}.short`)}
      </span>
      <div className="text-lg font-bold text-[#252420]">{pick.name}</div>
      <div className="mb-2 text-sm text-[#8B8B85]">{pick.symbol}</div>
      {asset?.current_price != null && <div className="mb-2 text-2xl font-bold text-[#252420]">{price}</div>}
      <div className="mb-3 flex flex-wrap gap-1.5">
        <span className={`inline-block rounded-full border px-3 py-0.5 text-xs font-semibold uppercase ${recStyles[pick.recommendation]}`}>{t(`rec.${pick.recommendation}`)}</span>
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
    </motion.div>
  )
}

"use client"

import { motion } from "framer-motion"
import { useLanguage } from "@/hooks/use-language"
import type { SectorData } from "@/types/report"
import { SECTOR_COLORS, SECTOR_ICONS, SECTORS } from "@/lib/constants"

const outlookStyles: Record<string, string> = {
  bullish: "bg-green-50 text-green-700", bearish: "bg-red-50 text-red-700", neutral: "bg-amber-50 text-amber-700",
}
// Glyph so outlook is not conveyed by color alone (WCAG 1.4.1).
const outlookGlyph: Record<string, string> = { bullish: "▲", bearish: "▼", neutral: "◆" }

interface SectorOverviewProps { sectors: Record<string, SectorData>; onSectorClick?: (sector: string) => void }

export function SectorOverview({ sectors, onSectorClick }: SectorOverviewProps) {
  const { t } = useLanguage()
  return (
    <motion.section initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5 }}>
      <p className="mb-2 text-xs font-semibold uppercase tracking-[0.16em] text-[#8B8B85]">{t("sectors.kicker")}</p>
      <h2 className="mb-4 text-2xl font-bold tracking-tight text-[#252420]">{t("sectors.title")}</h2>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {SECTORS.map((key, i) => {
          const s = sectors[key]
          if (!s) return null
          if (s.data_unavailable) return (
            <div key={key} className="rounded-xl border border-[#E6E6E4] bg-[#FCFCFB] p-5">
              <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-lg text-lg" style={{ backgroundColor: `${SECTOR_COLORS[key]}12` }}>{SECTOR_ICONS[key]}</div>
              <h3 className="text-sm font-semibold text-[#252420]">{t(`sector.${key}`)}</h3>
              <p className="mt-1 text-xs italic text-[#8B8B85]">{t("sectors.dataUnavailable")}</p>
            </div>
          )
          return (
            <motion.div key={key} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.55 + i * 0.04 }} role="button" tabIndex={0} aria-label={t(`sector.${key}`)} onClick={() => onSectorClick?.(key)} onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); onSectorClick?.(key) } }} className="cursor-pointer rounded-xl border border-[#E6E6E4] bg-[#FCFCFB] p-5 transition-all hover:border-[#D0D0CE] hover:shadow-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#37352F] focus-visible:ring-offset-2">
              <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-lg text-lg" style={{ backgroundColor: `${SECTOR_COLORS[key]}12`, color: SECTOR_COLORS[key] }}>{SECTOR_ICONS[key]}</div>
              <h3 className="mb-1 text-sm font-semibold text-[#252420]">{t(`sector.${key}`)}</h3>
              <span className={`mb-2 inline-block rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase ${outlookStyles[s.sector_outlook] ?? ""}`}><span aria-hidden="true">{outlookGlyph[s.sector_outlook] ?? ""}</span> {t(`outlook.${s.sector_outlook}`)}</span>
              <p className="line-clamp-2 text-xs leading-relaxed text-[#8B8B85]">{s.sector_summary}</p>
              <div className="mt-3 border-t border-[#E6E6E4] pt-2 text-xs text-[#8B8B85]">{t("picks.topPick")} <strong className="text-[#37352F]">{s.top_pick || t("picks.na")}</strong></div>
            </motion.div>
          )
        })}
      </div>
    </motion.section>
  )
}

"use client"

import { useState, useCallback } from "react"
import { motion } from "framer-motion"
import { useLanguage } from "@/hooks/use-language"
import type { SectorData, Asset } from "@/types/report"
import { SECTOR_COLORS, SECTORS } from "@/lib/constants"
import { formatPrice, formatPercent, percentClass, formatRange52w } from "@/lib/utils"

function ChangeCell({ value, lang }: { value: number | null; lang: string }) {
  return <span className={percentClass(value)}>{formatPercent(value, lang)}</span>
}

type SortKey = "name" | "price" | "24h" | "7d" | "30d" | "ytd" | "signal"

const colAccessor: Record<SortKey, (a: Asset) => string | number> = {
  name: (a) => a.name, price: (a) => a.current_price ?? Number.NEGATIVE_INFINITY,
  "24h": (a) => a.change_24h ?? Number.NEGATIVE_INFINITY, "7d": (a) => a.change_7d ?? Number.NEGATIVE_INFINITY,
  "30d": (a) => a.change_30d ?? Number.NEGATIVE_INFINITY, ytd: (a) => a.ytd_change ?? Number.NEGATIVE_INFINITY,
  signal: (a) => ({ buy: 3, hold: 2, sell: 1 }[a.recommendation] ?? 0),
}

// Hoisted to module scope (stable identity; avoids react-hooks/static-components).
function Th({ label }: { label: string }) {
  return <th className="whitespace-nowrap border-b-2 border-[#E6E6E4] px-3 py-2 text-left text-[11px] font-semibold uppercase tracking-wider text-[#8B8B85]">{label}</th>
}

function ThSort({ label, col, sortKey, sortDir, onSort }: { label: string; col: SortKey; sortKey: SortKey; sortDir: "asc" | "desc"; onSort: (c: SortKey) => void }) {
  const active = sortKey === col
  const activate = () => onSort(col)
  return (
    <th
      role="button"
      tabIndex={0}
      aria-sort={active ? (sortDir === "asc" ? "ascending" : "descending") : "none"}
      className="cursor-pointer select-none whitespace-nowrap border-b-2 border-[#E6E6E4] px-3 py-2 text-left text-[11px] font-semibold uppercase tracking-wider text-[#8B8B85] hover:text-[#37352F] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#37352F] focus-visible:ring-offset-1"
      onClick={(e) => { e.stopPropagation(); activate() }}
      onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); e.stopPropagation(); activate() } }}
    >
      {label} <span className={`text-[10px] ${active ? "text-[#fa8625]" : "opacity-30"}`}>{active && sortDir === "desc" ? "▼" : "▲"}</span>
    </th>
  )
}

const badgeClass = (value: string, type: "source" | "buzz" | "rec") => {
  const s: Record<string, Record<string, string>> = {
    source: { high: "bg-green-50 text-green-700", medium: "bg-amber-50 text-amber-700", low: "bg-red-50 text-red-700" },
    buzz: { high: "bg-red-50 text-red-600", medium: "bg-amber-50 text-amber-700", low: "bg-zinc-100 text-zinc-500" },
    rec: { buy: "bg-green-50 text-green-700", hold: "bg-amber-50 text-amber-700", sell: "bg-red-50 text-red-700" },
  }
  return `inline-block rounded-full px-2 py-0.5 text-[10px] font-semibold ${s[type][value] ?? "bg-zinc-100 text-zinc-500"}`
}

function SortableTable({ assets }: { assets: Asset[] }) {
  const { t, lang } = useLanguage()
  const [sortKey, setSortKey] = useState<SortKey>("name")
  const [sortDir, setSortDir] = useState<"asc" | "desc">("asc")
  const handleSort = useCallback((key: SortKey) => { setSortKey((prevKey) => { if (prevKey === key) setSortDir(d => d === "asc" ? "desc" : "asc"); else setSortDir("asc"); return key }) }, [])
  const sorted = [...assets].sort((a, b) => { const va = colAccessor[sortKey](a), vb = colAccessor[sortKey](b); const cmp = typeof va === "number" && typeof vb === "number" ? va - vb : String(va).localeCompare(String(vb)); return sortDir === "desc" ? -cmp : cmp })

  return (
    <div className="overflow-x-auto">
      <table className="mb-4 w-full border-collapse text-sm">
        <thead><tr>
          <ThSort label={t("table.asset")} col="name" sortKey={sortKey} sortDir={sortDir} onSort={handleSort} />
          <ThSort label={t("table.price")} col="price" sortKey={sortKey} sortDir={sortDir} onSort={handleSort} />
          <ThSort label={t("table.24h")} col="24h" sortKey={sortKey} sortDir={sortDir} onSort={handleSort} />
          <ThSort label={t("table.7d")} col="7d" sortKey={sortKey} sortDir={sortDir} onSort={handleSort} />
          <ThSort label={t("table.30d")} col="30d" sortKey={sortKey} sortDir={sortDir} onSort={handleSort} />
          <ThSort label={t("table.ytd")} col="ytd" sortKey={sortKey} sortDir={sortDir} onSort={handleSort} />
          <Th label={t("table.52w")} />
          <Th label={t("table.sources")} />
          <Th label={t("table.social")} />
          <ThSort label={t("table.signal")} col="signal" sortKey={sortKey} sortDir={sortDir} onSort={handleSort} />
        </tr></thead>
        <tbody>
          {sorted.map((a) => (
            <tr key={a.symbol} className="hover:bg-[#F7F7F5]">
              <td className="whitespace-nowrap border-b border-[#F0F0ED] px-3 py-2.5"><strong className="text-[#252420]">{a.name}</strong><br /><span className="text-xs text-[#8B8B85]">{a.symbol}</span></td>
              <td className="whitespace-nowrap border-b border-[#F0F0ED] px-3 py-2.5 font-medium">{formatPrice(a.current_price, a.price_unit, lang)}</td>
              <td className="whitespace-nowrap border-b border-[#F0F0ED] px-3 py-2.5 text-xs"><ChangeCell value={a.change_24h} lang={lang} /></td>
              <td className="whitespace-nowrap border-b border-[#F0F0ED] px-3 py-2.5 text-xs"><ChangeCell value={a.change_7d} lang={lang} /></td>
              <td className="whitespace-nowrap border-b border-[#F0F0ED] px-3 py-2.5 text-xs"><ChangeCell value={a.change_30d} lang={lang} /></td>
              <td className="whitespace-nowrap border-b border-[#F0F0ED] px-3 py-2.5 text-xs"><ChangeCell value={a.ytd_change} lang={lang} /></td>
              <td className="whitespace-nowrap border-b border-[#F0F0ED] px-3 py-2.5 text-xs text-[#8B8B85]">{formatRange52w(a.week_52_high, a.week_52_low, a.price_unit, lang)}</td>
              <td className="whitespace-nowrap border-b border-[#F0F0ED] px-3 py-2.5"><span className={badgeClass(a.source_agreement, "source")}>{a.source_agreement}</span></td>
              <td className="whitespace-nowrap border-b border-[#F0F0ED] px-3 py-2.5"><span className={badgeClass(a.social_buzz, "buzz")}>{a.social_sentiment} ({a.social_buzz})</span></td>
              <td className="whitespace-nowrap border-b border-[#F0F0ED] px-3 py-2.5"><span className={badgeClass(a.recommendation, "rec")}>{t(`rec.${a.recommendation}`)}</span></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

interface DetailedAnalysisProps { sectors: Record<string, SectorData>; openSectors?: string[] }

export function DetailedAnalysis({ sectors, openSectors = [] }: DetailedAnalysisProps) {
  const { t } = useLanguage()
  const [openKeys, setOpenKeys] = useState<Set<string>>(new Set(openSectors))
  const toggle = useCallback((key: string) => { setOpenKeys(prev => { const next = new Set(prev); if (next.has(key)) next.delete(key); else next.add(key); return next }) }, [])
  const effectiveOpen = new Set([...openKeys, ...openSectors])

  return (
    <motion.section initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.55 }}>
      <p className="mb-2 text-xs font-semibold uppercase tracking-[0.16em] text-[#8B8B85]">{t("analysis.kicker")}</p>
      <h2 className="mb-4 text-2xl font-bold tracking-tight text-[#252420]">{t("analysis.title")}</h2>
      <div className="space-y-3">
        {SECTORS.map((key) => {
          const s = sectors[key]; if (!s || s.data_unavailable) return null
          const isOpen = effectiveOpen.has(key)
          const newsItems = (s.assets || []).flatMap(a => (a.key_news || []).map(n => n))
          const socialItems = (s.assets || []).flatMap(a => (a.social_highlights || []).map(h => h))
          return (
            <div key={key} id={`sector-${key}`} className="overflow-hidden rounded-xl border border-[#E6E6E4] bg-[#FCFCFB]">
              <div role="button" tabIndex={0} aria-expanded={isOpen} aria-label={t(`sector.${key}`)} className="flex cursor-pointer select-none items-center justify-between px-5 py-4 hover:bg-[#F7F7F5] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-[#37352F]" onClick={() => toggle(key)} onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); toggle(key) } }}>
                <h3 className="flex items-center gap-2.5 text-sm font-semibold text-[#252420]">
                  <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ backgroundColor: SECTOR_COLORS[key] }} />
                  {t(`sector.${key}`)}
                </h3>
                <span className="text-sm text-[#8B8B85] transition-transform duration-300" style={{ transform: isOpen ? "rotate(180deg)" : "rotate(0)" }}>&#9660;</span>
              </div>
              <div className="overflow-hidden transition-all duration-300 ease-in-out" style={{ maxHeight: isOpen ? "3000px" : "0" }}>
                <div className="border-t border-[#E6E6E4] px-5 pb-5 pt-4">
                  <SortableTable assets={s.assets} />
                  <div className="mt-4 grid gap-4 sm:grid-cols-2">
                    {newsItems.length > 0 && <div><h4 className="mb-2 text-xs font-semibold uppercase tracking-wider text-[#8B8B85]">{t("analysis.news")}</h4>{newsItems.slice(0, 8).map((n, i) => <div key={i} className="border-b border-[#F0F0ED] py-1.5 text-sm text-[#4D4A44]">{n}</div>)}</div>}
                    {socialItems.length > 0 && <div><h4 className="mb-2 text-xs font-semibold uppercase tracking-wider text-[#8B8B85]">{t("analysis.social")}</h4>{socialItems.slice(0, 6).map((h, i) => <div key={i} className="border-b border-[#F0F0ED] py-1.5 text-sm italic text-[#8B8B85]">{h}</div>)}</div>}
                  </div>
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </motion.section>
  )
}

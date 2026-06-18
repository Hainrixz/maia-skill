"use client"

import { motion } from "framer-motion"
import { useLanguage } from "@/hooks/use-language"
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  ResponsiveContainer, PieChart, Pie, Cell, ScatterChart, Scatter,
  XAxis, YAxis, ZAxis, Tooltip, BarChart, Bar, CartesianGrid, Legend,
} from "recharts"
import type { SectorData, RiskAdjustedPick, PortfolioAllocation } from "@/types/report"
import { SECTOR_COLORS, SECTORS } from "@/lib/constants"

interface ChartsSectionProps { sectors: Record<string, SectorData>; picks: RiskAdjustedPick[]; allocation: PortfolioAllocation }

function ConfidenceRadar({ sectors }: { sectors: Record<string, SectorData> }) {
  const { t } = useLanguage()
  const data = SECTORS.map(key => { const s = sectors[key]; if (!s?.assets || s.assets.length === 0) return { sector: t(`sector.${key}`), confidence: 0 }; return { sector: t(`sector.${key}`), confidence: Math.round(s.assets.reduce((sum, a) => sum + a.confidence, 0) / s.assets.length * 10) / 10 } })
  return <ResponsiveContainer width="100%" height={260}><RadarChart data={data}><PolarGrid stroke="#E6E6E4" /><PolarAngleAxis dataKey="sector" tick={{ fill: "#4D4A44", fontSize: 11 }} /><PolarRadiusAxis domain={[0, 10]} tickCount={6} tick={{ fill: "#8B8B85", fontSize: 10 }} axisLine={false} /><Radar dataKey="confidence" stroke="#fa8625" fill="#fa8625" fillOpacity={0.15} strokeWidth={2} dot={{ r: 5, fill: "#fa8625" }} /></RadarChart></ResponsiveContainer>
}

function RiskBubbleChart({ picks }: { picks: RiskAdjustedPick[] }) {
  const { t } = useLanguage()
  return (
    <ResponsiveContainer width="100%" height={260}>
      <ScatterChart margin={{ top: 10, right: 20, bottom: 20, left: 10 }}>
        <CartesianGrid stroke="#F0F0ED" />
        <XAxis dataKey="x" type="number" domain={[0, 10]} tick={{ fill: "#8B8B85", fontSize: 10 }} label={{ value: t("charts.riskScore"), position: "bottom", fill: "#8B8B85", fontSize: 11 }} />
        <YAxis dataKey="y" type="number" domain={[0, 10]} tick={{ fill: "#8B8B85", fontSize: 10 }} label={{ value: t("charts.adjScore"), angle: -90, position: "insideLeft", fill: "#8B8B85", fontSize: 11 }} />
        <ZAxis dataKey="z" range={[40, 400]} />
        <Tooltip content={({ payload }) => { if (!payload?.[0]) return null; const d = payload[0].payload; return <div className="rounded-lg border border-[#E6E6E4] bg-white px-3 py-2 text-xs shadow-md"><span className="font-bold" style={{ color: d.color }}>{d.name}</span><br />{t("charts.riskScore")}: {d.x} | {t("charts.adjScore")}: {d.y}</div> }} />
        <Legend wrapperStyle={{ fontSize: 10 }} iconType="circle" iconSize={8} />
        {picks.map(p => <Scatter key={p.symbol} name={p.symbol} data={[{ x: p.risk_score || 5, y: p.risk_adjusted_score || p.confidence || 5, z: (p.confidence || 5) * 1.5 + 3, name: p.symbol, color: SECTOR_COLORS[p.sector] || "#888" }]} fill={`${SECTOR_COLORS[p.sector] || "#888"}40`} stroke={SECTOR_COLORS[p.sector] || "#888"} strokeWidth={2} />)}
      </ScatterChart>
    </ResponsiveContainer>
  )
}

function AllocationDoughnut({ allocation }: { allocation: PortfolioAllocation }) {
  const { t } = useLanguage()
  const data = Object.entries(allocation).filter(([, v]) => v > 0).map(([key, value]) => ({ name: t(`sector.${key}.short`), value, color: SECTOR_COLORS[key] ?? "#8B8B85" }))
  return <ResponsiveContainer width="100%" height={260}><PieChart><Pie data={data} cx="50%" cy="50%" innerRadius={55} outerRadius={90} paddingAngle={2} dataKey="value" strokeWidth={2}>{data.map(e => <Cell key={e.name} fill={`${e.color}80`} stroke={e.color} />)}</Pie><Tooltip content={({ payload }) => { if (!payload?.[0]) return null; const d = payload[0].payload; return <div className="rounded-lg border border-[#E6E6E4] bg-white px-3 py-2 text-xs shadow-md"><span style={{ color: d.color }}>{d.name}</span>: {d.value}%</div> }} /><Legend layout="vertical" align="right" verticalAlign="middle" wrapperStyle={{ fontSize: 11 }} iconType="rect" iconSize={10} /></PieChart></ResponsiveContainer>
}

function SocialBuzzBar({ sectors }: { sectors: Record<string, SectorData> }) {
  const { t } = useLanguage()
  const buzzScore = (raw: string | null | undefined): number => { const v = (raw || "").toLowerCase(); if (v.includes("high")) return 3; if (v.includes("med")) return 2; if (v.includes("low")) return 1; return 1 }
  const data = SECTORS.map(key => { const s = sectors[key]; if (!s?.assets || s.assets.length === 0) return { sector: t(`sector.${key}.short`), buzz: 0, fill: SECTOR_COLORS[key] }; return { sector: t(`sector.${key}.short`), buzz: Math.round(s.assets.reduce((sum, a) => sum + buzzScore(a.social_buzz), 0) / s.assets.length * 10) / 10, fill: SECTOR_COLORS[key] } })
  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={data} margin={{ top: 10, right: 10, bottom: 10, left: 10 }}>
        <CartesianGrid stroke="#F0F0ED" vertical={false} />
        <XAxis dataKey="sector" tick={{ fill: "#4D4A44", fontSize: 10 }} axisLine={false} />
        <YAxis domain={[0, 3]} ticks={[1, 2, 3]} tickFormatter={(v: number) => v === 1 ? t("charts.low") : v === 2 ? t("charts.med") : v === 3 ? t("charts.high") : ""} tick={{ fill: "#8B8B85", fontSize: 10 }} axisLine={false} />
        <Tooltip content={({ payload }) => { if (!payload?.[0]) return null; const d = payload[0].payload; const label = d.buzz >= 2.5 ? t("charts.high") : d.buzz >= 1.5 ? t("charts.medium") : t("charts.low"); return <div className="rounded-lg border border-[#E6E6E4] bg-white px-3 py-2 text-xs shadow-md"><span style={{ color: d.fill }}>{d.sector}</span>: {label}</div> }} />
        <Bar dataKey="buzz" radius={[6, 6, 0, 0]} strokeWidth={2}>{data.map(e => <Cell key={e.sector} fill={`${e.fill}30`} stroke={e.fill} />)}</Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

export function ChartsSection({ sectors, picks, allocation }: ChartsSectionProps) {
  const { t } = useLanguage()
  const charts = [
    { title: t("charts.confidence"), aria: t("charts.aria.confidence"), chart: <ConfidenceRadar sectors={sectors} /> },
    { title: t("charts.risk"), aria: t("charts.aria.risk"), chart: <RiskBubbleChart picks={picks} /> },
    { title: t("charts.allocation"), aria: t("charts.aria.allocation"), chart: <AllocationDoughnut allocation={allocation} /> },
    { title: t("charts.buzz"), aria: t("charts.aria.buzz"), chart: <SocialBuzzBar sectors={sectors} /> },
  ]
  return (
    <motion.section initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.65 }} className="print-break-before">
      <p className="mb-2 text-xs font-semibold uppercase tracking-[0.16em] text-[#8B8B85]">{t("charts.kicker")}</p>
      <h2 className="mb-4 text-2xl font-bold tracking-tight text-[#252420]">{t("charts.title")}</h2>
      <div className="grid gap-4 sm:grid-cols-2">
        {charts.map((c, i) => (
          <motion.div key={c.title} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.7 + i * 0.04 }} className="rounded-xl border border-[#E6E6E4] bg-[#FCFCFB] p-5">
            <h3 className="mb-3 text-sm font-semibold text-[#252420]">{c.title}</h3>
            <div className="h-[260px]" role="img" aria-label={c.aria}>{c.chart}</div>
          </motion.div>
        ))}
      </div>
    </motion.section>
  )
}

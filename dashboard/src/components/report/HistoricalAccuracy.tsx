"use client"

import { motion } from "framer-motion"
import { PieChart, Pie, Cell, ResponsiveContainer } from "recharts"
import { useLanguage } from "@/hooks/use-language"
import type { HistoricalAccuracy as AccuracyType } from "@/types/report"

export function HistoricalAccuracy({ accuracy }: { accuracy: AccuracyType }) {
  const { t } = useLanguage()

  if (!accuracy || accuracy.calls_made === 0) {
    return (
      <motion.section initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.6 }}>
        <p className="mb-2 text-xs font-semibold uppercase tracking-[0.16em] text-[#8B8B85]">{t("accuracy.kicker")}</p>
        <h2 className="mb-4 text-2xl font-bold tracking-tight text-[#252420]">{t("accuracy.title")}</h2>
        <div className="rounded-xl border border-[#E6E6E4] bg-[#FCFCFB] p-6 text-center text-sm italic text-[#8B8B85]">{t("accuracy.empty")}</div>
      </motion.section>
    )
  }

  const pct = accuracy.accuracy_pct
  const color = pct >= 60 ? "#00c853" : pct >= 40 ? "#ffc107" : "#e94560"
  const data = [{ name: t("accuracy.correct"), value: pct }, { name: t("accuracy.remaining"), value: 100 - pct }]

  return (
    <motion.section initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.6 }}>
      <p className="mb-2 text-xs font-semibold uppercase tracking-[0.16em] text-[#8B8B85]">{t("accuracy.kicker")}</p>
      <h2 className="mb-4 text-2xl font-bold tracking-tight text-[#252420]">{t("accuracy.title")}</h2>
      <div className="flex flex-col items-center gap-8 rounded-xl border border-[#E6E6E4] bg-[#FCFCFB] p-6 sm:flex-row">
        <div className="relative h-28 w-28 shrink-0" role="img" aria-label={`${t("accuracy.aria")}: ${pct}%`}>
          <ResponsiveContainer width="100%" height="100%">
            <PieChart><Pie data={data} cx="50%" cy="50%" innerRadius={35} outerRadius={50} dataKey="value" startAngle={90} endAngle={-270} strokeWidth={0}><Cell fill={color} /><Cell fill="#F0F0ED" /></Pie></PieChart>
          </ResponsiveContainer>
          <div className="absolute inset-0 flex flex-col items-center justify-center"><span className="text-xl font-bold" style={{ color }}>{pct}%</span></div>
        </div>
        <div className="flex-1">
          <div className="mb-3 flex flex-wrap gap-6">
            <div><span className="text-lg font-bold text-[#252420]">{accuracy.calls_made}</span><p className="text-[10px] font-semibold uppercase tracking-wider text-[#8B8B85]">{t("accuracy.callsMade")}</p></div>
            <div><span className="text-lg font-bold" style={{ color }}>{accuracy.calls_correct}</span><p className="text-[10px] font-semibold uppercase tracking-wider text-[#8B8B85]">{t("accuracy.correct")}</p></div>
            {accuracy.previous_date && <div><span className="text-lg font-bold text-[#252420]">{accuracy.previous_date}</span><p className="text-[10px] font-semibold uppercase tracking-wider text-[#8B8B85]">{t("accuracy.since")}</p></div>}
          </div>
          {accuracy.notable && <div className="border-t border-[#E6E6E4] pt-2 text-sm text-[#4D4A44]">{accuracy.notable}</div>}
        </div>
      </div>
    </motion.section>
  )
}

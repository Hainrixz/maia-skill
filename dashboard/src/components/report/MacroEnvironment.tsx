"use client"

import { motion } from "framer-motion"
import { useLanguage } from "@/hooks/use-language"
import type { MacroEnvironment as MacroType } from "@/types/report"

const valueColors: Record<string, string> = {
  rising: "text-red-600", falling: "text-green-600", stable: "text-amber-600",
  high: "text-red-600", medium: "text-amber-600", low: "text-green-600",
}

export function MacroEnvironment({ macro }: { macro: MacroType }) {
  const { t } = useLanguage()
  const indicators = [
    { label: t("macro.rates"), value: macro.interest_rate_outlook },
    { label: t("macro.inflation"), value: macro.inflation_outlook },
    { label: t("macro.georisk"), value: macro.geopolitical_risk },
  ]

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.25 }} className="rounded-xl border border-[#E6E6E4] bg-[#FCFCFB] p-6">
      <h3 className="mb-4 text-base font-semibold text-[#252420]">{t("macro.title")}</h3>
      <div className="mb-4 flex flex-wrap gap-3">
        {indicators.map((ind) => (
          <div key={ind.label} className="flex flex-col items-center gap-1 rounded-lg bg-[#F7F7F5] px-5 py-2.5">
            <span className="text-[10px] font-semibold uppercase tracking-[0.16em] text-[#8B8B85]">{ind.label}</span>
            <span className={`text-sm font-bold ${valueColors[ind.value] ?? "text-[#4D4A44]"}`}>{ind.value ? t(`macro.${ind.value}`) : "N/A"}</span>
          </div>
        ))}
      </div>
      <p className="mb-3.5 text-sm leading-relaxed text-[#4D4A44]">{macro.summary}</p>
      {macro.key_factors.length > 0 && (
        <ul className="space-y-0">
          {macro.key_factors.map((factor, i) => (
            <li key={i} className="border-b border-[#F0F0ED] py-1.5 text-sm text-[#4D4A44]">
              <span className="mr-1.5 text-[#fa8625]">&#8227;</span>{factor}
            </li>
          ))}
        </ul>
      )}
    </motion.div>
  )
}

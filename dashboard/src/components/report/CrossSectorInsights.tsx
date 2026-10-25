// Copyright (c) 2026 Enrique Rocha (@soyenriquerocha)
// SPDX-License-Identifier: MIT
// id: er-805c9b73
"use client"

import { motion } from "framer-motion"
import { useLanguage } from "@/hooks/use-language"
import type { CrossSectorInsight } from "@/types/report"

export function CrossSectorInsights({ insights }: { insights: CrossSectorInsight[] }) {
  const { t } = useLanguage()
  if (!insights || insights.length === 0) return null
  return (
    <motion.section initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.35 }}>
      <p className="mb-2 text-xs font-semibold uppercase tracking-[0.16em] text-[#8B8B85]">{t("insights.kicker")}</p>
      <h2 className="mb-4 text-2xl font-bold tracking-tight text-[#252420]">{t("insights.title")}</h2>
      <div className="grid gap-4 sm:grid-cols-2">
        {insights.map((item, i) => (
          <motion.div key={i} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 + i * 0.04 }} className="rounded-xl border border-[#E6E6E4] bg-[#FCFCFB] p-5">
            <p className="mb-2 text-sm font-semibold text-[#37352F]">{item.insight}</p>
            <p className="text-sm leading-relaxed text-[#8B8B85]">{item.implication}</p>
          </motion.div>
        ))}
      </div>
    </motion.section>
  )
}

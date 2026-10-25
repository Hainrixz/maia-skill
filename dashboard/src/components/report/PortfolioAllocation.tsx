// Copyright (c) 2026 Enrique Rocha (@soyenriquerocha)
// SPDX-License-Identifier: MIT
// id: er-805c9b73
"use client"

import { motion } from "framer-motion"
import { useLanguage } from "@/hooks/use-language"
import type { PortfolioAllocation as AllocationType } from "@/types/report"
import { SECTOR_COLORS } from "@/lib/constants"

export function PortfolioAllocation({ allocation }: { allocation: AllocationType }) {
  const { t } = useLanguage()
  const entries = Object.entries(allocation)
  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} className="rounded-xl border border-[#E6E6E4] bg-[#FCFCFB] p-6">
      <h3 className="mb-4 text-base font-semibold text-[#252420]">{t("allocation.title")}</h3>
      <div className="space-y-3">
        {entries.map(([key, value], i) => (
          <div key={key} className="flex items-center gap-3">
            <span className="w-20 text-sm font-medium capitalize text-[#4D4A44]">{t(`sector.${key}.short`)}</span>
            <div className="relative h-6 flex-1 overflow-hidden rounded-full bg-[#F0F0ED]">
              <motion.div initial={{ width: 0 }} animate={{ width: `${value}%` }} transition={{ delay: 0.4 + i * 0.08, duration: 0.6, ease: "easeOut" }} className="flex h-full min-w-[40px] items-center justify-end rounded-full pr-2.5 text-xs font-bold text-white" style={{ backgroundColor: SECTOR_COLORS[key] ?? "#8B8B85" }}>
                {value}%
              </motion.div>
            </div>
          </div>
        ))}
      </div>
    </motion.div>
  )
}

// Copyright (c) 2026 Enrique Rocha (@soyenriquerocha)
// SPDX-License-Identifier: MIT
// id: er-805c9b73
"use client"

import { AnimatePresence, motion } from "framer-motion"
import { useLanguage } from "@/hooks/use-language"
import type { RiskAdjustedPick, SectorData } from "@/types/report"
import { PickCard } from "./PickCard"

interface TopPicksGridProps {
  picks: RiskAdjustedPick[]
  sectors: Record<string, SectorData>
}

export function TopPicksGrid({ picks, sectors }: TopPicksGridProps) {
  const { t } = useLanguage()

  return (
    <motion.section initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.45 }}>
      <h2 className="mb-5 text-2xl font-bold tracking-tight text-[#252420]">{t("picks.title")}</h2>
      <div className="grid gap-[18px]" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))" }}>
        <AnimatePresence mode="popLayout">
          {picks.map((pick) => <PickCard key={pick.symbol} pick={pick} sectors={sectors} />)}
        </AnimatePresence>
      </div>
    </motion.section>
  )
}

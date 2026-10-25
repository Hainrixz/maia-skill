// Copyright (c) 2026 Enrique Rocha (@soyenriquerocha)
// SPDX-License-Identifier: MIT
// id: er-805c9b73
"use client"

import { motion } from "framer-motion"
import { useLanguage } from "@/hooks/use-language"

export function ExecutiveSummary({ summary }: { summary: string }) {
  const { t } = useLanguage()
  return (
    <motion.section
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.2 }}
      className="rounded-xl border border-[#E6E6E4] bg-[#FCFCFB] p-6"
    >
      <p className="mb-2 text-xs font-semibold uppercase tracking-[0.16em] text-[#8B8B85]">
        {t("executive.label")}
      </p>
      <p className="text-[15px] leading-7 text-[#4D4A44]">{summary}</p>
    </motion.section>
  )
}

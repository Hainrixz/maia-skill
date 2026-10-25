// Copyright (c) 2026 Enrique Rocha (@soyenriquerocha)
// SPDX-License-Identifier: MIT
// id: er-805c9b73
"use client"

import { motion } from "framer-motion"

export function Warnings({ warnings }: { warnings: string[] }) {
  if (!warnings || warnings.length === 0) return null

  return (
    <motion.section
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.4 }}
      className="space-y-2"
    >
      {warnings.map((warning, i) => (
        <div
          key={i}
          className="flex items-start gap-2.5 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800"
        >
          <span className="mt-0.5 shrink-0">&#9888;</span>
          <span>{warning}</span>
        </div>
      ))}
    </motion.section>
  )
}

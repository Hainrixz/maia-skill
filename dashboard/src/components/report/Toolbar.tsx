// Copyright (c) 2026 Enrique Rocha (@soyenriquerocha)
// SPDX-License-Identifier: MIT
// id: er-805c9b73
"use client"

import { useState } from "react"
import { motion } from "framer-motion"
import { useLanguage } from "@/hooks/use-language"

interface ToolbarProps {
  activeFilter: string
  onFilterChange: (filter: string) => void
  onSearchChange: (query: string) => void
}

export function Toolbar({ activeFilter, onFilterChange, onSearchChange }: ToolbarProps) {
  const { t } = useLanguage()
  const [search, setSearch] = useState("")

  const filters = [
    { label: t("toolbar.all"), value: "all" },
    { label: t("toolbar.buy"), value: "buy" },
    { label: t("toolbar.hold"), value: "hold" },
    { label: t("toolbar.sell"), value: "sell" },
  ]

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay: 0.15 }}
      className="no-print my-5 flex flex-col items-stretch gap-3 rounded-xl border border-[#E6E6E4] bg-[#FCFCFB] px-4 py-3 sm:flex-row sm:flex-wrap sm:items-center"
      role="toolbar"
      aria-label={t("toolbar.filter")}
    >
      <span className="text-xs font-semibold uppercase tracking-[0.12em] text-[#8B8B85]">{t("toolbar.filter")}</span>
      <div className="flex gap-2" role="group" aria-label={t("toolbar.filter")}>
        {filters.map((f) => (
          <button
            key={f.value}
            onClick={() => onFilterChange(f.value)}
            className={`rounded-full px-4 py-1.5 text-xs font-medium transition-all ${
              activeFilter === f.value
                ? "bg-[#37352F] text-white shadow-sm"
                : "border border-[#E6E6E4] bg-white text-[#4D4A44] hover:bg-[#F7F7F5]"
            }`}
            aria-pressed={activeFilter === f.value}
          >
            {f.label}
          </button>
        ))}
      </div>
      <input
        type="text"
        placeholder={t("toolbar.search")}
        value={search}
        onChange={(e) => { setSearch(e.target.value); onSearchChange(e.target.value) }}
        className="ml-0 w-full rounded-full border border-[#E6E6E4] bg-white px-4 py-1.5 text-sm text-[#37352F] placeholder:text-[#8B8B85] focus:border-[#37352F] focus:outline-none sm:ml-auto sm:w-48"
        aria-label={t("toolbar.search")}
      />
      <button
        onClick={() => window.print()}
        className="rounded-full border border-[#E6E6E4] bg-white px-4 py-1.5 text-xs font-medium text-[#4D4A44] transition-colors hover:bg-[#F7F7F5]"
      >
        {t("toolbar.print")}
      </button>
    </motion.div>
  )
}

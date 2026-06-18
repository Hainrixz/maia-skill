"use client"

import { motion } from "framer-motion"
import { useLanguage } from "@/hooks/use-language"
import { localeFor } from "@/lib/utils"
import type { ReportData } from "@/types/report"

const profileStyles: Record<string, string> = {
  conservative: "bg-blue-50 text-blue-700 border-blue-200",
  moderate: "bg-amber-50 text-amber-700 border-amber-200",
  aggressive: "bg-red-50 text-red-700 border-red-200",
}
// Icon so the risk profile is not conveyed by color alone (WCAG 1.4.1).
const profileGlyph: Record<string, string> = { conservative: "🛡", moderate: "⚖", aggressive: "🚀" }

export function ReportHeader({ data }: { data: ReportData }) {
  const { t, lang } = useLanguage()
  const date = new Date(data.generated_at).toLocaleDateString(localeFor(lang), {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  })

  return (
    <motion.header
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="border-b border-[#E6E6E4] pb-6 pt-8"
    >
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-4xl font-semibold tracking-tight text-[#252420] sm:text-5xl">
            tododeia.
          </h1>
          <p className="mt-1 text-sm text-[#8B8B85]">
            {t("header.subtitle")} {data.creator}
          </p>
        </div>
        <div className="text-left sm:text-right">
          <p className="text-sm text-[#8B8B85]">
            <strong className="block text-base font-semibold text-[#37352F]">{date}</strong>
            {t("header.report")}
          </p>
          <span className={`mt-2 inline-block rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-wider ${profileStyles[data.risk_profile]}`}>
            <span aria-hidden="true">{profileGlyph[data.risk_profile] ?? ""}</span> {t(`profile.${data.risk_profile}`)} {t("header.profile")}
          </span>
        </div>
      </div>
    </motion.header>
  )
}

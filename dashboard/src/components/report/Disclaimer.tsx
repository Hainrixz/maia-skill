"use client"

import { motion } from "framer-motion"
import { useLanguage } from "@/hooks/use-language"

// "banner" renders the prominent, above-the-report educational notice;
// "footnote" is the smaller closing reminder at the bottom of the report.
export function Disclaimer({ variant = "footnote" }: { variant?: "banner" | "footnote" }) {
  const { t } = useLanguage()

  if (variant === "banner") {
    return (
      <div role="note" className="rounded-xl border border-amber-300 bg-amber-50 px-5 py-3 text-sm leading-relaxed text-amber-900">
        <strong>⚠️ {t("ack.title")}.</strong> {t("disclaimer.banner")}
      </div>
    )
  }

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.75 }} className="rounded-xl border border-[#E6E6E4] bg-[#FCFCFB] px-5 py-4 text-xs leading-relaxed text-[#8B8B85]">
      <strong className="text-[#37352F]">{t("disclaimer.label")}</strong> {t("disclaimer.text")}
    </motion.div>
  )
}

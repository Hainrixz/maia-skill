"use client"

import { motion } from "framer-motion"
import { useLanguage } from "@/hooks/use-language"

export function Footer({ generatedAt }: { generatedAt: string }) {
  const { t } = useLanguage()
  const timestamp = new Date(generatedAt).toLocaleString()
  return (
    <motion.footer initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.8 }} className="flex flex-wrap items-center justify-between gap-2 border-t border-[#E6E6E4] pb-10 pt-5 text-xs text-[#8B8B85]">
      <div>tododeia. by <span className="font-medium text-[#37352F]">@quebert</span> &mdash; {t("footer.tagline")}</div>
      <div>{t("footer.generated")} {timestamp}</div>
    </motion.footer>
  )
}

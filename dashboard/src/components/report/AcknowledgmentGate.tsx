"use client"

import { useEffect, useRef } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { useLanguage } from "@/hooks/use-language"

// One-time educational gate shown before the report. Intentionally has no
// Escape-to-dismiss: the user must acknowledge that this is not financial advice.
export function AcknowledgmentGate() {
  const { showAck, acknowledge, t } = useLanguage()
  const btnRef = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    if (showAck) btnRef.current?.focus()
  }, [showAck])

  return (
    <AnimatePresence>
      {showAck && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-6 backdrop-blur-sm"
          role="dialog"
          aria-modal="true"
          aria-labelledby="ack-title"
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 10 }}
            transition={{ duration: 0.25, ease: "easeOut" }}
            className="mx-4 w-full max-w-md rounded-2xl border border-amber-200 bg-white p-8 shadow-xl"
          >
            <div className="mb-3 text-2xl" aria-hidden="true">⚠️</div>
            <h2 id="ack-title" className="text-lg font-semibold tracking-tight text-[#252420]">
              {t("ack.title")}
            </h2>
            <p className="mt-3 text-sm leading-relaxed text-[#6b6b6b]">{t("ack.text")}</p>
            <button
              ref={btnRef}
              type="button"
              onClick={acknowledge}
              className="mt-6 w-full rounded-full bg-[#37352F] px-6 py-3 text-sm font-medium text-white transition-all hover:bg-[#252420] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#37352F] focus-visible:ring-offset-2"
            >
              {t("ack.button")}
            </button>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}

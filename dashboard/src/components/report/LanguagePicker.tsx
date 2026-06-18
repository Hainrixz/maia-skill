"use client"

import { useEffect, useRef } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { useLanguage } from "@/hooks/use-language"

export function LanguagePicker() {
  const { showPicker, setLang, dismissPicker, t } = useLanguage()
  const dialogRef = useRef<HTMLDivElement>(null)
  const firstBtnRef = useRef<HTMLButtonElement>(null)

  const handleSelect = (lang: "en" | "es") => {
    setLang(lang)
    dismissPicker()
  }

  // Focus management + Escape + simple focus trap (WCAG 2.4.3).
  useEffect(() => {
    if (!showPicker) return
    firstBtnRef.current?.focus()
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") { dismissPicker(); return }
      if (e.key !== "Tab") return
      const focusables = dialogRef.current?.querySelectorAll<HTMLElement>("button")
      if (!focusables || focusables.length === 0) return
      const first = focusables[0]
      const last = focusables[focusables.length - 1]
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus() }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus() }
    }
    document.addEventListener("keydown", onKeyDown)
    return () => document.removeEventListener("keydown", onKeyDown)
  }, [showPicker, dismissPicker])

  return (
    <AnimatePresence>
      {showPicker && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm"
          role="dialog"
          aria-modal="true"
          aria-labelledby="lang-title"
        >
          <motion.div
            ref={dialogRef}
            initial={{ opacity: 0, scale: 0.95, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 10 }}
            transition={{ duration: 0.25, ease: "easeOut" }}
            className="mx-4 w-full max-w-sm rounded-2xl border border-[#E6E6E4] bg-white p-8 shadow-xl"
          >
            <div className="text-center">
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-[#8B8B85]">
                tododeia.
              </p>
              <h2 id="lang-title" className="mt-4 text-xl font-semibold tracking-tight text-[#252420]">
                {t("lang.title")}
              </h2>
              <p className="mt-1 text-sm text-[#8B8B85]">
                {t("lang.subtitle")}
              </p>
            </div>

            <div className="mt-8 flex flex-col gap-3">
              <button
                ref={firstBtnRef}
                onClick={() => handleSelect("en")}
                className="flex w-full items-center justify-center gap-2 rounded-full border border-[#E6E6E4] bg-white px-6 py-3 text-sm font-medium text-[#37352F] transition-all hover:border-[#D0D0CE] hover:bg-[#F7F7F5] hover:shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#37352F] focus-visible:ring-offset-2"
              >
                <span className="text-lg" aria-hidden="true">🇺🇸</span>
                English
              </button>
              <button
                onClick={() => handleSelect("es")}
                className="flex w-full items-center justify-center gap-2 rounded-full bg-[#37352F] px-6 py-3 text-sm font-medium text-white transition-all hover:bg-[#252420] hover:shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#37352F] focus-visible:ring-offset-2"
              >
                <span className="text-lg" aria-hidden="true">🇲🇽</span>
                Español
              </button>
            </div>

            <p className="mt-6 text-center text-[10px] text-[#8B8B85]">
              Investment research by @soyenriquerocha
            </p>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}

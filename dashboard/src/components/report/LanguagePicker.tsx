"use client"

import { motion, AnimatePresence } from "framer-motion"
import { useLanguage } from "@/hooks/use-language"

export function LanguagePicker() {
  const { showPicker, setLang, dismissPicker } = useLanguage()

  const handleSelect = (lang: "en" | "es") => {
    setLang(lang)
    dismissPicker()
  }

  return (
    <AnimatePresence>
      {showPicker && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm"
        >
          <motion.div
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
              <h2 className="mt-4 text-xl font-semibold tracking-tight text-[#252420]">
                Choose your language
              </h2>
              <p className="mt-1 text-sm text-[#8B8B85]">
                Elige tu idioma
              </p>
            </div>

            <div className="mt-8 flex flex-col gap-3">
              <button
                onClick={() => handleSelect("en")}
                className="flex w-full items-center justify-center gap-2 rounded-full border border-[#E6E6E4] bg-white px-6 py-3 text-sm font-medium text-[#37352F] transition-all hover:border-[#D0D0CE] hover:bg-[#F7F7F5] hover:shadow-sm"
              >
                <span className="text-lg">🇺🇸</span>
                English
              </button>
              <button
                onClick={() => handleSelect("es")}
                className="flex w-full items-center justify-center gap-2 rounded-full bg-[#37352F] px-6 py-3 text-sm font-medium text-white transition-all hover:bg-[#252420] hover:shadow-sm"
              >
                <span className="text-lg">🇲🇽</span>
                Español
              </button>
            </div>

            <p className="mt-6 text-center text-[10px] text-[#8B8B85]">
              Investment research by @quebert
            </p>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}

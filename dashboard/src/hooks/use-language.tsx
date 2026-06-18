"use client"

import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from "react"
import { TRANSLATIONS, type Language } from "@/lib/translations"

const STORAGE_KEY = "tododeia-lang-v2"
const ACK_KEY = "tododeia-ack-v1"

interface LanguageContextValue {
  lang: Language
  setLang: (lang: Language) => void
  t: (key: string) => string
  showPicker: boolean
  dismissPicker: () => void
  showAck: boolean
  acknowledge: () => void
}

const LanguageContext = createContext<LanguageContextValue | null>(null)

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Language>("en")
  const [showPicker, setShowPicker] = useState(false)
  // Default acknowledged=true so the gate never flashes during SSR/first paint;
  // the real value is read from localStorage on mount.
  const [acknowledged, setAcknowledged] = useState(true)
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
    const stored = localStorage.getItem(STORAGE_KEY) as Language | null
    if (stored === "en" || stored === "es") setLangState(stored)
    else setShowPicker(true)
    setAcknowledged(!!localStorage.getItem(ACK_KEY))
  }, [])

  // Keep <html lang> in sync for screen readers and SEO (client-only; SSR stays "en").
  useEffect(() => {
    if (mounted) document.documentElement.lang = lang
  }, [lang, mounted])

  const setLang = useCallback((newLang: Language) => {
    setLangState(newLang)
    localStorage.setItem(STORAGE_KEY, newLang)
  }, [])

  const dismissPicker = useCallback(() => setShowPicker(false), [])

  const acknowledge = useCallback(() => {
    setAcknowledged(true)
    localStorage.setItem(ACK_KEY, "1")
  }, [])

  const t = useCallback(
    (key: string): string => TRANSLATIONS[lang][key] ?? TRANSLATIONS.en[key] ?? key,
    [lang]
  )

  const effectiveShowPicker = mounted && showPicker
  // Show the educational acknowledgment after a language is chosen, before the report.
  const showAck = mounted && !effectiveShowPicker && !acknowledged

  return (
    <LanguageContext.Provider value={{ lang, setLang, t, showPicker: effectiveShowPicker, dismissPicker, showAck, acknowledge }}>
      {children}
    </LanguageContext.Provider>
  )
}

export function useLanguage(): LanguageContextValue {
  const ctx = useContext(LanguageContext)
  if (!ctx) {
    throw new Error("useLanguage must be used within a LanguageProvider")
  }
  return ctx
}

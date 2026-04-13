"use client"

import { createContext, useContext, useCallback, type ReactNode } from "react"
import { TRANSLATIONS, type Language } from "@/lib/translations"

interface LanguageContextValue {
  lang: Language
  setLang: (lang: Language) => void
  t: (key: string) => string
  showPicker: boolean
  dismissPicker: () => void
}

const LanguageContext = createContext<LanguageContextValue | null>(null)

export function LanguageProvider({ children }: { children: ReactNode }) {
  const lang: Language = "en"

  const setLang = useCallback((_newLang: Language) => {
    // Spanish removed — always English
  }, [])

  const dismissPicker = useCallback(() => {}, [])

  const t = useCallback(
    (key: string): string => {
      return TRANSLATIONS[lang][key] ?? TRANSLATIONS.en[key] ?? key
    },
    [lang]
  )

  return (
    <LanguageContext.Provider value={{ lang, setLang, t, showPicker: false, dismissPicker }}>
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

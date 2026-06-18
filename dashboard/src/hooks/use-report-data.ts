"use client"

import { useState, useEffect } from "react"
import type { ReportData } from "@/types/report"
import type { Language } from "@/lib/translations"

export function useReportData(lang: Language = "en") {
  const [data, setData] = useState<ReportData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [usedFallback, setUsedFallback] = useState(false)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    setUsedFallback(false)

    const file = lang === "es" ? "/data/report-es.json" : "/data/report.json"

    fetch(file)
      .then((res) => {
        if (!res.ok) {
          if (lang === "es" && res.status === 404) {
            // Spanish report missing — surface a (dismissible) notice instead of silently swapping.
            return fetch("/data/report.json").then((fallback) => {
              if (!fallback.ok) throw new Error(`Failed to load report data: ${fallback.status}`)
              if (!cancelled) setUsedFallback(true)
              return fallback.json()
            })
          }
          throw new Error(`Failed to load report data: ${res.status}`)
        }
        return res.json()
      })
      .then((d) => { if (!cancelled) setData(d) })
      .catch((err) => { if (!cancelled) setError(err.message) })
      .finally(() => { if (!cancelled) setLoading(false) })

    return () => { cancelled = true }
  }, [lang])

  return { data, loading, error, usedFallback }
}

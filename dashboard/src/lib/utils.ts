import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// ---- Locale-aware, format-on-render layer (single source of formatting) ----
// Values arrive as raw numbers per the data contract; these are the ONLY place
// where currency symbols, percent signs, separators, and locale rules are applied.

function bcp47(lang?: string): string {
  return lang === "es" ? "es-MX" : "en-US"
}

function na(lang?: string): string {
  return lang === "es" ? "N/D" : "N/A"
}

/** Price as currency/rate/index depending on unit. null → N/A. */
export function formatPrice(value: number | null | undefined, unit?: string | null, lang: string = "en"): string {
  if (value == null || Number.isNaN(value)) return na(lang)
  const locale = bcp47(lang)
  if (unit === "rate") {
    return new Intl.NumberFormat(locale, { minimumFractionDigits: 2, maximumFractionDigits: 4 }).format(value)
  }
  if (unit === "index") {
    return new Intl.NumberFormat(locale, { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(value)
  }
  const formatted = new Intl.NumberFormat(locale, {
    style: "currency", currency: "USD", minimumFractionDigits: 2, maximumFractionDigits: 2,
  }).format(value)
  // "USD/oz", "USD/bbl" → append the per-unit suffix.
  if (unit && unit.startsWith("USD/")) return `${formatted}/${unit.slice(4)}`
  return formatted
}

/** Compact magnitude for market cap / volume ($1.3T, $28B). English-style suffixes for ticker consistency. */
export function formatCompact(value: number | null | undefined, lang: string = "en"): string {
  if (value == null || Number.isNaN(value)) return na(lang)
  return new Intl.NumberFormat("en-US", {
    style: "currency", currency: "USD", notation: "compact", maximumFractionDigits: 2,
  }).format(value)
}

/** Signed percent string, e.g. "+3.04%" / "-1.50%". null → "—". */
export function formatPercent(value: number | null | undefined, lang: string = "en"): string {
  if (value == null || Number.isNaN(value)) return "—"
  const sign = value > 0 ? "+" : ""
  return `${sign}${new Intl.NumberFormat(bcp47(lang), { minimumFractionDigits: 1, maximumFractionDigits: 2 }).format(value)}%`
}

/** Tailwind text color class from the sign of a percentage number. */
export function percentClass(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "text-[#8B8B85]"
  return value > 0 ? "text-green-600" : value < 0 ? "text-red-600" : "text-[#8B8B85]"
}

/** "high / low" range using the asset's price unit. */
export function formatRange52w(high: number | null | undefined, low: number | null | undefined, unit?: string | null, lang: string = "en"): string {
  return `${formatPrice(high, unit, lang)} / ${formatPrice(low, unit, lang)}`
}

/** Map the app language to a BCP-47 locale for Intl date/number APIs. */
export function localeFor(lang?: string): string {
  return bcp47(lang)
}

"use client"

import { motion, AnimatePresence } from "framer-motion"
import { useState, useEffect } from "react"
import { GlossaryModal } from "@/components/ui/GlossaryModal"

// ─── Types ────────────────────────────────────────────────────────────────────

interface PortfolioPosition {
  symbol: string
  name?: string
  current_price?: number | null
  buy_price?: number
  quantity?: number
  pnl_pct?: number | null
  action: "HOLD" | "TRIM" | "STOP_LOSS" | "SELL" | "ADD"
  urgency: "high" | "medium" | "low"
  stop_loss_price: number | null
  take_profit_price: number | null
  trim_price: number | null
  add_price: number | null
  exit_full?: boolean
  position_health: "strong" | "neutral" | "weak" | "critical"
  thesis_status: string
  micro_sentiment?: string
  macro_impact?: string
  key_risks: string[]
  key_catalysts: string[]
  reasoning: string
  headline_insight?: string
  altman_z?: { score?: number; zone?: string } | null
  piotroski?: { score?: number; strength?: string; signals?: string[] } | null
}

interface PortfolioSummary {
  total_positions: number
  total_cost: number
  total_current_value: number
  total_pnl: number
  total_pnl_pct: number
  macro_summary?: string
  overall_health: "strong" | "neutral" | "weak" | "critical"
  immediate_actions_needed: number
}

interface CrossPositionInsight {
  // shape from write_portfolio_report.py output
  type?: string
  description?: string
  symbols?: string[]
  severity?: string
  recommendation?: string
  // legacy shape
  insight?: string
  implication?: string
}

interface PortfolioWarning {
  type?: string
  severity?: string
  message?: string
  symbols?: string[]
}

interface PriorityAttention {
  symbol?: string
  urgency?: string
  action?: string
  reason?: string
}

interface PortfolioAnalysisReport {
  generated_at: string
  portfolio_summary: PortfolioSummary
  positions: PortfolioPosition[]
  cross_position_insights: CrossPositionInsight[]
  priority_attention: (string | PriorityAttention)[]
  warnings: (string | PortfolioWarning)[]
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

const ACTION_CONFIG: Record<string, { label: string; bg: string; text: string; border: string }> = {
  HOLD:      { label: "Hold",      bg: "bg-blue-50",   text: "text-blue-700",  border: "border-blue-200" },
  TRIM:      { label: "Trim",      bg: "bg-yellow-50", text: "text-yellow-700",border: "border-yellow-200" },
  STOP_LOSS: { label: "Stop Loss", bg: "bg-orange-50", text: "text-orange-700",border: "border-orange-200" },
  SELL:      { label: "Sell",      bg: "bg-red-50",    text: "text-red-700",   border: "border-red-200" },
  ADD:       { label: "Add",       bg: "bg-green-50",  text: "text-green-700", border: "border-green-200" },
}

const HEALTH_CONFIG: Record<string, { dot: string; label: string }> = {
  strong:   { dot: "bg-green-500",  label: "Strong" },
  neutral:  { dot: "bg-blue-400",   label: "Neutral" },
  weak:     { dot: "bg-yellow-500", label: "Weak" },
  critical: { dot: "bg-red-500",    label: "Critical" },
}

const URGENCY_CONFIG: Record<string, { bg: string; text: string; label: string }> = {
  high:   { bg: "bg-red-100",    text: "text-red-600",    label: "Urgent" },
  medium: { bg: "bg-yellow-100", text: "text-yellow-700", label: "Watch" },
  low:    { bg: "bg-[#F0F0ED]",  text: "text-[#8B8B85]",  label: "Low" },
}

function fmt(n: number | null | undefined, prefix = "$"): string {
  if (n == null) return "—"
  return `${prefix}${Math.abs(n).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

function fmtDate(iso: string): string {
  try { return new Date(iso).toLocaleString("en-US", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" }) }
  catch { return iso }
}

function healthBadgeTone(zone?: string | null): string {
  if (zone === "safe") return "bg-green-50 text-green-700 border-green-200"
  if (zone === "gray") return "bg-yellow-50 text-yellow-700 border-yellow-200"
  if (zone === "distress") return "bg-red-50 text-red-700 border-red-200"
  return "bg-[#F0F0ED] text-[#8B8B85] border-[#E6E6E4]"
}

function piotroskiTone(strength?: string | null): string {
  if (strength === "strong") return "bg-green-50 text-green-700 border-green-200"
  if (strength === "neutral") return "bg-blue-50 text-blue-700 border-blue-200"
  if (strength === "weak") return "bg-red-50 text-red-700 border-red-200"
  return "bg-[#F0F0ED] text-[#8B8B85] border-[#E6E6E4]"
}

// ─── Position Card (attention-needed) ────────────────────────────────────────

function AttentionCard({ pos }: { pos: PortfolioPosition }) {
  const [expanded, setExpanded] = useState(false)
  const [glossaryOpen, setGlossaryOpen] = useState(false)
  const action = ACTION_CONFIG[pos.action] ?? ACTION_CONFIG.HOLD
  const health = HEALTH_CONFIG[pos.position_health] ?? HEALTH_CONFIG.neutral
  const urgency = URGENCY_CONFIG[pos.urgency] ?? URGENCY_CONFIG.low
  const pnlPositive = (pos.pnl_pct ?? 0) >= 0

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className={`rounded-xl border-2 ${action.border} bg-white p-5 shadow-sm`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <span className={`h-2.5 w-2.5 rounded-full shrink-0 ${health.dot}`} />
          <div>
            <p className="text-lg font-bold text-[#252420] leading-tight">{pos.symbol}</p>
            <p className="text-xs text-[#8B8B85] truncate max-w-[140px]">{pos.name}</p>
          </div>
        </div>
        <div className="flex flex-col items-end gap-1.5">
          <button
            onClick={() => setGlossaryOpen(true)}
            className="mb-0.5 flex h-6 w-6 items-center justify-center self-end rounded-full border border-[#E6E6E4] bg-white text-[10px] text-[#8B8B85] transition-colors hover:border-[#37352F] hover:text-[#252420]"
            title="Ver glosario de términos"
            aria-label="Ver glosario de términos"
          >ⓘ</button>
          <span className={`rounded-full px-3 py-1 text-xs font-bold border ${action.bg} ${action.text} ${action.border}`}>
            {action.label}
          </span>
          <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ${urgency.bg} ${urgency.text}`}>
            {urgency.label}
          </span>
        </div>
      </div>

      <div className="mt-4 grid grid-cols-3 gap-3">
        <div>
          <p className="text-[10px] uppercase tracking-wider text-[#8B8B85] font-semibold">Buy</p>
          <p className="text-sm font-semibold text-[#252420]">{fmt(pos.buy_price)}</p>
        </div>
        <div>
          <p className="text-[10px] uppercase tracking-wider text-[#8B8B85] font-semibold">Current</p>
          <p className="text-sm font-semibold text-[#252420]">{fmt(pos.current_price)}</p>
        </div>
        <div>
          <p className="text-[10px] uppercase tracking-wider text-[#8B8B85] font-semibold">P&L</p>
          <p className={`text-sm font-bold ${pnlPositive ? "text-green-600" : "text-red-600"}`}>
            {pos.pnl_pct != null ? `${pnlPositive ? "+" : ""}${pos.pnl_pct.toFixed(2)}%` : "—"}
          </p>
        </div>
      </div>

      <div className="mt-3 flex flex-wrap gap-2">
        <span className={`rounded-full border px-2.5 py-1 text-[10px] font-semibold ${healthBadgeTone(pos.altman_z?.zone)}`}>
          Altman Z: {pos.altman_z?.score != null ? `${pos.altman_z.score} (${pos.altman_z.zone})` : "N/A"}
        </span>
        <span className={`rounded-full border px-2.5 py-1 text-[10px] font-semibold ${piotroskiTone(pos.piotroski?.strength)}`}>
          Piotroski: {pos.piotroski?.score != null ? `${pos.piotroski.score}/9 (${pos.piotroski.strength})` : "N/A"}
        </span>
      </div>

      {/* Stop-loss / Take-profit / Trim row */}
      <div className="mt-3 grid grid-cols-3 gap-3 rounded-lg bg-[#F7F7F5] p-3">
        <div>
          <p className="text-[10px] uppercase tracking-wider text-[#8B8B85] font-semibold">Stop Loss</p>
          <p className={`text-sm font-bold ${pos.stop_loss_price ? "text-orange-600" : "text-[#8B8B85]"}`}>
            {pos.stop_loss_price ? fmt(pos.stop_loss_price) : "—"}
          </p>
        </div>
        <div>
          <p className="text-[10px] uppercase tracking-wider text-[#8B8B85] font-semibold">Take Profit</p>
          <p className={`text-sm font-bold ${pos.take_profit_price ? "text-green-600" : "text-[#8B8B85]"}`}>
            {pos.take_profit_price ? fmt(pos.take_profit_price) : "—"}
          </p>
        </div>
        <div>
          <p className="text-[10px] uppercase tracking-wider text-[#8B8B85] font-semibold">Trim At</p>
          <p className={`text-sm font-bold ${pos.trim_price ? "text-yellow-600" : "text-[#8B8B85]"}`}>
            {pos.trim_price ? fmt(pos.trim_price) : "—"}
          </p>
        </div>
      </div>

      <p className="mt-3 text-xs text-[#4D4A44] leading-relaxed">{pos.reasoning}</p>

      {pos.headline_insight && (
        <p className="mt-2 text-[11px] italic text-[#8B8B85]">📰 {pos.headline_insight}</p>
      )}

      <button
        onClick={() => setExpanded((e) => !e)}
        className="mt-3 text-[11px] font-semibold text-[#8B8B85] hover:text-[#4D4A44] transition-colors"
      >
        {expanded ? "▲ Less detail" : "▼ More detail"}
      </button>

      <GlossaryModal open={glossaryOpen} onClose={() => setGlossaryOpen(false)} />

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden"
          >
            <div className="mt-3 grid grid-cols-2 gap-3">
              {(pos.key_risks?.length ?? 0) > 0 && (
                <div>
                  <p className="text-[10px] font-semibold uppercase tracking-wider text-red-500 mb-1">Key Risks</p>
                  <ul className="space-y-0.5">
                    {(pos.key_risks ?? []).map((r, i) => (
                      <li key={i} className="text-[11px] text-[#4D4A44] flex gap-1"><span>•</span>{r}</li>
                    ))}
                  </ul>
                </div>
              )}
              {(pos.key_catalysts?.length ?? 0) > 0 && (
                <div>
                  <p className="text-[10px] font-semibold uppercase tracking-wider text-green-600 mb-1">Catalysts</p>
                  <ul className="space-y-0.5">
                    {(pos.key_catalysts ?? []).map((c, i) => (
                      <li key={i} className="text-[11px] text-[#4D4A44] flex gap-1"><span>•</span>{c}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
            <div className="mt-2 flex flex-wrap gap-2">
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#F0F0ED] text-[#4D4A44]">
                Thesis: <strong>{pos.thesis_status}</strong>
              </span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#F0F0ED] text-[#4D4A44]">
                Sentiment: <strong>{pos.micro_sentiment ?? "N/A"}</strong>
              </span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#F0F0ED] text-[#4D4A44]">
                Macro: <strong>{pos.macro_impact ?? "N/A"}</strong>
              </span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

// ─── Full positions table ─────────────────────────────────────────────────────

function PositionsTable({ positions }: { positions: PortfolioPosition[] }) {
  return (
    <div className="overflow-x-auto rounded-xl border border-[#E6E6E4]">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-[#E6E6E4] bg-[#F7F7F5]">
            {["Asset", "P&L", "Action", "Altman Z", "Piotroski", "Stop Loss", "Take Profit", "Urgency", "Thesis", "Sentiment"].map((h) => (
              <th key={h} className="px-3 py-3 text-left text-[10px] font-semibold uppercase tracking-wider text-[#8B8B85] whitespace-nowrap">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {positions.map((pos) => {
            const action = ACTION_CONFIG[pos.action] ?? ACTION_CONFIG.HOLD
            const health = HEALTH_CONFIG[pos.position_health] ?? HEALTH_CONFIG.neutral
            const urgency = URGENCY_CONFIG[pos.urgency] ?? URGENCY_CONFIG.low
            const pnlPos = (pos.pnl_pct ?? 0) >= 0
            return (
              <tr key={pos.symbol} className="border-b border-[#F0F0ED] bg-[#FCFCFB] last:border-0 hover:bg-[#F7F7F5] transition-colors">
                <td className="px-3 py-3">
                  <div className="flex items-center gap-2">
                    <span className={`h-2 w-2 rounded-full shrink-0 ${health.dot}`} />
                    <div>
                      <p className="font-bold text-[#252420]">{pos.symbol}</p>
                      <p className="text-[10px] text-[#8B8B85] truncate max-w-[100px]">{pos.name}</p>
                    </div>
                  </div>
                </td>
                <td className={`px-3 py-3 font-semibold ${pnlPos ? "text-green-600" : "text-red-600"}`}>
                  {pos.pnl_pct != null ? `${pnlPos ? "+" : ""}${pos.pnl_pct.toFixed(2)}%` : "—"}
                </td>
                <td className="px-3 py-3">
                  <span className={`rounded-full px-2.5 py-1 text-[11px] font-bold border ${action.bg} ${action.text} ${action.border}`}>
                    {action.label}
                  </span>
                </td>
                <td className="px-3 py-3">
                  <span className={`rounded-full border px-2 py-0.5 text-[10px] font-semibold ${healthBadgeTone(pos.altman_z?.zone)}`}>
                    {pos.altman_z?.score != null ? `${pos.altman_z.score} (${pos.altman_z.zone})` : "N/A"}
                  </span>
                </td>
                <td className="px-3 py-3">
                  <span className={`rounded-full border px-2 py-0.5 text-[10px] font-semibold ${piotroskiTone(pos.piotroski?.strength)}`}>
                    {pos.piotroski?.score != null ? `${pos.piotroski.score}/9` : "N/A"}
                  </span>
                </td>
                <td className={`px-3 py-3 font-semibold ${pos.stop_loss_price ? "text-orange-600" : "text-[#8B8B85]"}`}>
                  {pos.stop_loss_price ? fmt(pos.stop_loss_price) : "—"}
                </td>
                <td className={`px-3 py-3 font-semibold ${pos.take_profit_price ? "text-green-600" : "text-[#8B8B85]"}`}>
                  {pos.take_profit_price ? fmt(pos.take_profit_price) : "—"}
                </td>
                <td className="px-3 py-3">
                  <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ${urgency.bg} ${urgency.text}`}>
                    {urgency.label}
                  </span>
                </td>
                <td className="px-3 py-3 text-xs text-[#4D4A44] capitalize">{pos.thesis_status}</td>
                <td className="px-3 py-3 text-xs text-[#4D4A44] capitalize">{pos.micro_sentiment ?? "n/a"}</td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

// ─── Empty state ──────────────────────────────────────────────────────────────

function EmptyState() {
  return (
    <div className="rounded-xl border border-[#E6E6E4] bg-[#FCFCFB] p-12 text-center">
      <p className="text-3xl mb-3">📊</p>
      <p className="text-sm font-semibold text-[#4D4A44]">No portfolio analysis yet</p>
      <p className="mt-1 text-xs text-[#8B8B85] max-w-xs mx-auto">
        Run <code className="bg-[#F0F0ED] px-1 py-0.5 rounded text-[11px]">analiza portfolio tododeia</code> to generate stop-loss levels, take-profit targets, and position recommendations.
      </p>
    </div>
  )
}

// ─── Main component ───────────────────────────────────────────────────────────

export function PortfolioAnalysisTab() {
  const [report, setReport] = useState<PortfolioAnalysisReport | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch("/api/portfolio-report", { cache: "no-store" })
      .then((r) => r.json())
      .then((data) => { setReport(data); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="space-y-4 animate-pulse">
        {[1, 2, 3].map((i) => <div key={i} className="h-32 rounded-xl bg-[#F0F0ED]" />)}
      </div>
    )
  }

  if (!report) return <EmptyState />

  const summary = report.portfolio_summary
  const pnlPos = summary.total_pnl_pct >= 0
  const healthColor: Record<string, string> = {
    strong: "text-green-600", neutral: "text-blue-600", weak: "text-yellow-600", critical: "text-red-600",
  }

  // Sort: attention positions first (SELL/STOP_LOSS/TRIM) then by urgency
  const urgencyOrder = { high: 0, medium: 1, low: 2 }
  const actionOrder  = { SELL: 0, STOP_LOSS: 1, TRIM: 2, HOLD: 3, ADD: 4 }
  const sorted = [...report.positions].sort((a, b) => {
    const ao = (actionOrder[a.action] ?? 9) - (actionOrder[b.action] ?? 9)
    if (ao !== 0) return ao
    return (urgencyOrder[a.urgency] ?? 9) - (urgencyOrder[b.urgency] ?? 9)
  })

  const attentionPositions = sorted.filter((p) => p.action !== "HOLD" || p.urgency === "high")
  const allPositions = sorted

  return (
    <motion.section
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className="space-y-8"
    >
      {/* Header */}
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-[#8B8B85]">Portfolio Analysis</p>
        <h2 className="text-2xl font-bold tracking-tight text-[#252420]">Position Management</h2>
        <p className="mt-1 text-xs text-[#8B8B85]">Generated {fmtDate(report.generated_at)}</p>
      </div>

      {/* Summary bar */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <div className="rounded-xl border border-[#E6E6E4] bg-[#FCFCFB] p-4">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#8B8B85]">Positions</p>
          <p className="mt-1 text-2xl font-bold text-[#252420]">{summary.total_positions}</p>
        </div>
        <div className="rounded-xl border border-[#E6E6E4] bg-[#FCFCFB] p-4">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#8B8B85]">Invested</p>
          <p className="mt-1 text-2xl font-bold text-[#252420]">{fmt(summary.total_cost)}</p>
        </div>
        <div className={`rounded-xl border p-4 ${pnlPos ? "border-green-200 bg-green-50" : "border-red-200 bg-red-50"}`}>
          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#8B8B85]">Total P&L</p>
          <p className={`mt-1 text-2xl font-bold ${pnlPos ? "text-green-600" : "text-red-600"}`}>
            {pnlPos ? "+" : ""}{fmt(summary.total_pnl)}
          </p>
          <p className={`text-xs font-medium ${pnlPos ? "text-green-500" : "text-red-500"}`}>
            {pnlPos ? "+" : ""}{summary.total_pnl_pct.toFixed(2)}%
          </p>
        </div>
        <div className={`rounded-xl border p-4 ${summary.immediate_actions_needed > 0 ? "border-orange-200 bg-orange-50" : "border-[#E6E6E4] bg-[#FCFCFB]"}`}>
          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#8B8B85]">Need Attention</p>
          <p className={`mt-1 text-2xl font-bold ${summary.immediate_actions_needed > 0 ? "text-orange-600" : "text-[#252420]"}`}>
            {summary.immediate_actions_needed}
          </p>
          <p className={`text-xs font-semibold capitalize ${healthColor[summary.overall_health] ?? "text-[#4D4A44]"}`}>
            Health: {summary.overall_health}
          </p>
        </div>
      </div>

      {/* Macro summary */}
      {summary.macro_summary && (
        <div className="rounded-xl border border-[#E6E6E4] bg-[#F7F7F5] px-5 py-4">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#8B8B85] mb-1">Macro Context</p>
          <p className="text-sm text-[#4D4A44]">{summary.macro_summary}</p>
        </div>
      )}

      {/* Warnings */}
      {report.warnings.length > 0 && (
        <div className="space-y-2">
          {report.warnings.map((w, i) => {
            const msg = typeof w === "string" ? w : (w as PortfolioWarning).message ?? JSON.stringify(w)
            const sev = typeof w === "string" ? "medium" : (w as PortfolioWarning).severity ?? "medium"
            const borderCls = sev === "high" ? "border-red-200 bg-red-50" : "border-orange-200 bg-orange-50"
            return (
            <div key={i} className={`flex gap-3 rounded-lg border px-4 py-3 ${borderCls}`}>
              <span className="shrink-0 text-orange-500">⚠</span>
              <p className="text-xs text-[#4D4A44]">{msg}</p>
            </div>
            )
          })}
        </div>
      )}

      {/* Attention cards */}
      {attentionPositions.length > 0 && (
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-[#8B8B85] mb-3">
            Requires Attention ({attentionPositions.length})
          </p>
          <div className="grid gap-4 sm:grid-cols-2">
            {attentionPositions.map((pos) => (
              <AttentionCard key={pos.symbol} pos={pos} />
            ))}
          </div>
        </div>
      )}

      {/* Cross-position insights */}
      {report.cross_position_insights.length > 0 && (
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-[#8B8B85] mb-3">Cross-Position Insights</p>
          <div className="space-y-3">
            {report.cross_position_insights.map((ins, i) => {
              const title = ins.description ?? ins.insight ?? ""
              const sub = ins.recommendation ?? ins.implication ?? ""
              const syms = ins.symbols?.join(", ")
              return (
              <div key={i} className="rounded-xl border border-[#E6E6E4] bg-[#FCFCFB] px-5 py-4">
                <p className="text-sm font-semibold text-[#252420]">{title}</p>
                {syms && <p className="mt-1 text-[10px] font-semibold text-[#8B8B85] uppercase tracking-wider">{syms}</p>}
                <p className="mt-1 text-xs text-[#8B8B85]">{sub}</p>
              </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Full positions table */}
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-[#8B8B85] mb-3">All Positions</p>
        <PositionsTable positions={allPositions} />
      </div>
    </motion.section>
  )
}

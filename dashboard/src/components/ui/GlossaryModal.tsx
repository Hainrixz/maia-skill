"use client"

import { useEffect } from "react"
import { motion, AnimatePresence } from "framer-motion"

interface GlossaryModalProps {
  open: boolean
  onClose: () => void
}

const terms: {
  group: string
  items: {
    label: string
    badge: string
    desc: string
    formula?: string
    example?: string
    sub?: { key: string; val: string }[]
  }[]
}[] = [
  {
    group: "Recomendaciones",
    items: [
      { label: "BUY", badge: "bg-green-100 text-green-700 border-green-200", desc: "Nueva posición — no tienes este activo. Compra." },
      { label: "ADD", badge: "bg-green-100 text-green-700 border-green-200", desc: "Ya tienes este activo. Agrega más acciones a tu posición existente." },
      { label: "HOLD", badge: "bg-amber-100 text-amber-700 border-amber-200", desc: "Ya tienes este activo. Mantén sin cambios — la tesis sigue vigente pero no hay catalizador para agregar." },
      { label: "TRIM", badge: "bg-orange-100 text-orange-700 border-orange-200", desc: "Ya tienes este activo. Vende una parte (30–50%) para reducir exposición, por ejemplo cuando está sobrecomprado (RSI alto)." },
      { label: "SELL", badge: "bg-red-100 text-red-700 border-red-200", desc: "Vende toda la posición — la tesis se invalidó o el riesgo supera el perfil moderado." },
    ],
  },
  {
    group: "Scores (escala 0–10)",
    items: [
      {
        label: "Confidence",
        badge: "bg-[#F7F7F5] text-[#4D4A44] border-[#E6E6E4]",
        desc: "Certeza del agente en el pick. 10 = máxima convicción basada en fundamentales, noticias y técnico.",
      },
      {
        label: "Risk Score",
        badge: "bg-[#F7F7F5] text-[#8B8B85] border-[#E6E6E4]",
        desc: "Riesgo intrínseco del activo (volatilidad, deuda, incertidumbre de negocio). 10 = máximo riesgo. Un score alto no significa mala inversión, solo mayor volatilidad.",
      },
      {
        label: "Risk-Adj Score",
        badge: "bg-[#F7F7F5] text-[#252420] border-[#E6E6E4]",
        desc: "Score final de ranking que balancea retorno esperado vs. riesgo. Es el número principal para comparar picks entre sí.",
        formula: "Risk-Adj = Confidence − (Risk × 0.3)",
        example: "Ej: Confidence=8.2, Risk=3.0 → 8.2 − 0.9 = 7.7",
      },
    ],
  },
  {
    group: "Precios y Niveles",
    items: [
      {
        label: "🎯 Target 12m",
        badge: "bg-green-50 text-green-700 border-green-200",
        desc: "Precio objetivo a 12 meses estimado por el agente basado en la tesis fundamental.",
      },
      {
        label: "🛑 Stop Loss",
        badge: "bg-red-50 text-red-700 border-red-200",
        desc: "Precio de salida si la tesis se rompe. Si el precio cae aquí, vende para limitar pérdidas. Es una protección de capital, no una predicción.",
      },
      {
        label: "R/R",
        badge: "bg-[#F7F7F5] text-[#4D4A44] border-[#E6E6E4]",
        desc: "Risk/Reward ratio — cuánto puedes ganar por cada unidad que arriesgas.",
        formula: "R/R = (Target − Entry) ÷ (Entry − Stop)",
        example: "Ej: R/R 3.93x → por cada $1 en riesgo, el potencial de ganancia es $3.93",
      },
    ],
  },
  {
    group: "Sizing y Portafolio",
    items: [
      {
        label: "Position Size %",
        badge: "bg-blue-50 text-blue-700 border-blue-200",
        desc: "Porcentaje del portafolio total sugerido para este activo. Para perfil moderado, máximo 10% por posición.",
      },
    ],
  },
  {
    group: "Salud Financiera",
    items: [
      {
        label: "Altman Z-Score",
        badge: "bg-[#F7F7F5] text-[#4D4A44] border-[#E6E6E4]",
        desc: "Modelo cuantitativo de predicción de quiebra empresarial basado en ratios financieros.",
        sub: [
          { key: "Safe (Z > 2.99)", val: "Balance sheet sólido, bajo riesgo financiero." },
          { key: "Gray (1.81–2.99)", val: "Zona de incertidumbre — monitorear de cerca." },
          { key: "Distress (< 1.81)", val: "Riesgo elevado — el agente reduce el tamaño de posición." },
        ],
      },
      {
        label: "Piotroski F-Score",
        badge: "bg-[#F7F7F5] text-[#4D4A44] border-[#E6E6E4]",
        desc: "Score 0–9 que mide la salud operativa de una empresa (rentabilidad, apalancamiento, eficiencia).",
        sub: [
          { key: "7–9 (Strong)", val: "Fundamentales en mejora — el agente sube confianza +1." },
          { key: "3–6 (Neutral)", val: "Situación mixta, sin impacto en score." },
          { key: "0–2 (Weak)", val: "Deterioro operativo — el agente penaliza confianza −1." },
        ],
      },
    ],
  },
]

export function GlossaryModal({ open, onClose }: GlossaryModalProps) {
  useEffect(() => {
    if (!open) return
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose()
    }
    window.addEventListener("keydown", handler)
    return () => window.removeEventListener("keydown", handler)
  }, [open, onClose])

  return (
    <AnimatePresence>
      {open && (
        <>
          <motion.div
            key="backdrop"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm"
            onClick={onClose}
          />
          <motion.div
            key="modal"
            initial={{ opacity: 0, y: 16, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 16, scale: 0.97 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-x-4 top-1/2 z-50 mx-auto max-h-[85vh] max-w-lg -translate-y-1/2 overflow-y-auto rounded-2xl border border-[#E6E6E4] bg-[#FCFCFB] shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="sticky top-0 flex items-center justify-between border-b border-[#E6E6E4] bg-[#FCFCFB] px-5 py-4">
              <div>
                <h2 className="text-base font-bold text-[#252420]">Glosario de términos</h2>
                <p className="text-xs text-[#8B8B85]">Cómo leer las tarjetas de análisis</p>
              </div>
              <button
                onClick={onClose}
                className="flex h-8 w-8 items-center justify-center rounded-full border border-[#E6E6E4] bg-white text-[#8B8B85] transition-colors hover:border-[#37352F] hover:text-[#252420]"
                aria-label="Cerrar glosario"
              >
                ✕
              </button>
            </div>

            {/* Body */}
            <div className="divide-y divide-[#F0F0ED] px-5 py-2">
              {terms.map((group) => (
                <div key={group.group} className="py-4">
                  <h3 className="mb-3 text-[11px] font-semibold uppercase tracking-wider text-[#8B8B85]">
                    {group.group}
                  </h3>
                  <div className="space-y-3">
                    {group.items.map((item) => (
                      <div key={item.label} className="flex gap-3">
                        <span
                          className={`mt-0.5 inline-block shrink-0 rounded-full border px-2.5 py-0.5 text-xs font-semibold ${item.badge}`}
                        >
                          {item.label}
                        </span>
                        <div className="min-w-0">
                          <p className="text-sm leading-relaxed text-[#4D4A44]">{item.desc}</p>
                          {item.formula && (
                            <p className="mt-1.5 rounded-md bg-[#F0F0ED] px-2.5 py-1.5 font-mono text-xs text-[#37352F]">
                              {item.formula}
                            </p>
                          )}
                          {item.example && (
                            <p className="mt-1 text-xs text-[#8B8B85]">{item.example}</p>
                          )}
                          {item.sub && (
                            <ul className="mt-1.5 space-y-1">
                              {item.sub.map((s) => (
                                <li key={s.key} className="text-xs text-[#4D4A44]">
                                  <span className="font-semibold text-[#252420]">{s.key}:</span> {s.val}
                                </li>
                              ))}
                            </ul>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            {/* Footer */}
            <div className="border-t border-[#E6E6E4] px-5 py-3 text-center text-[11px] text-[#8B8B85]">
              Tododeia — Not financial advice. For informational purposes only.
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}

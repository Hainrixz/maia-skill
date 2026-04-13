"use client"

import { useState, useCallback } from "react"
import { useReportData } from "@/hooks/use-report-data"
import { LanguageProvider, useLanguage } from "@/hooks/use-language"
import { ReportHeader } from "@/components/report/ReportHeader"
import { ExecutiveSummary } from "@/components/report/ExecutiveSummary"
import { MacroEnvironment } from "@/components/report/MacroEnvironment"
import { PortfolioAllocation } from "@/components/report/PortfolioAllocation"
import { CrossSectorInsights } from "@/components/report/CrossSectorInsights"
import { Warnings } from "@/components/report/Warnings"
import { TopPicksGrid } from "@/components/report/TopPicksGrid"
import { SectorOverview } from "@/components/report/SectorOverview"
import { DetailedAnalysis } from "@/components/report/DetailedAnalysis"
import { HistoricalAccuracy } from "@/components/report/HistoricalAccuracy"
import { ChartsSection } from "@/components/report/ChartsSection"
import { Disclaimer } from "@/components/report/Disclaimer"
import { Footer } from "@/components/report/Footer"
import { LoadingSkeleton } from "@/components/report/LoadingSkeleton"

function ReportContent() {
  const { lang } = useLanguage()
  const { data, loading, error } = useReportData(lang)
  const [openSectors, setOpenSectors] = useState<string[]>([])

  const handleSectorClick = useCallback((sector: string) => {
    setOpenSectors((prev) =>
      prev.includes(sector) ? prev : [...prev, sector]
    )
    setTimeout(() => {
      document
        .getElementById(`sector-${sector}`)
        ?.scrollIntoView({ behavior: "smooth", block: "start" })
    }, 100)
  }, [])

  if (loading) return <LoadingSkeleton />

  if (error || !data) {
    return (
      <div className="relative flex min-h-screen items-center justify-center bg-white">
        <div
          className="absolute inset-0 -z-10 h-full w-full bg-[radial-gradient(#e5e7eb_1px,transparent_1px)] [background-size:32px_32px]"
          aria-hidden="true"
        />
        <div className="text-center">
          <h1 className="text-3xl font-semibold tracking-tight text-[#252420]">
            tododeia.
          </h1>
          <p className="mt-3 text-sm text-[#8B8B85]">
            {error ?? "No report data found."}
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="relative min-h-screen bg-white">
      <div
        className="absolute inset-0 -z-10 h-full w-full bg-[radial-gradient(#e5e7eb_1px,transparent_1px)] [background-size:32px_32px]"
        aria-hidden="true"
      />
      <main id="main-content" className="mx-auto max-w-5xl px-4 pb-12 sm:px-6 lg:px-10">
        <ReportHeader data={data} />
        <div className="mt-6 space-y-8">
          <ExecutiveSummary summary={data.executive_summary} />
          <div className="grid gap-4 md:grid-cols-2">
            <MacroEnvironment macro={data.macro_environment} />
            <PortfolioAllocation allocation={data.portfolio_allocation} />
          </div>
          <CrossSectorInsights insights={data.cross_sector_insights} />
          <Warnings warnings={data.warnings} />
          <TopPicksGrid
            picks={data.risk_adjusted_picks}
            sectors={data.sectors}
          />
          <SectorOverview
            sectors={data.sectors}
            onSectorClick={handleSectorClick}
          />
          <DetailedAnalysis
            sectors={data.sectors}
            openSectors={openSectors}
          />
          <HistoricalAccuracy accuracy={data.historical_accuracy} />
          <ChartsSection
            sectors={data.sectors}
            picks={data.risk_adjusted_picks}
            allocation={data.portfolio_allocation}
          />
          <Disclaimer />
        </div>
        <Footer generatedAt={data.generated_at} />
      </main>
    </div>
  )
}

export default function ReportPage() {
  return (
    <LanguageProvider>
      <ReportContent />
    </LanguageProvider>
  )
}

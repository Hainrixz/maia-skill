export type Language = "en" | "es"

export const TRANSLATIONS: Record<Language, Record<string, string>> = {
  en: {
    // Header
    "header.subtitle": "Investment Analysis by",
    "header.report": "Investment Analysis Report",
    "header.profile": "profile",

    // Toolbar
    "toolbar.filter": "Filter",
    "toolbar.all": "All",
    "toolbar.buy": "Buy",
    "toolbar.hold": "Hold",
    "toolbar.sell": "Sell",
    "toolbar.search": "Search assets...",
    "toolbar.print": "Print / PDF",

    // Executive Summary
    "executive.label": "Executive Summary",

    // Macro Environment
    "macro.title": "Macro Environment",
    "macro.rates": "Rates",
    "macro.inflation": "Inflation",
    "macro.georisk": "Geo Risk",

    // Portfolio Allocation
    "allocation.title": "Recommended Portfolio Allocation",

    // Cross-Sector Insights
    "insights.kicker": "Cross-Sector",
    "insights.title": "Insights",

    // Top Picks
    "picks.title": "Risk-Adjusted Top Picks",
    "picks.empty": "No picks match the current filter.",
    "picks.riskAdj": "Risk-Adj Score",
    "picks.confidence": "Confidence",
    "picks.risk": "Risk",
    "picks.topPick": "Top pick:",
    "picks.na": "N/A",

    // Sector Overview
    "sectors.kicker": "Overview",
    "sectors.title": "Sectors",
    "sectors.dataUnavailable": "Data unavailable",

    // Detailed Analysis
    "analysis.kicker": "Analysis",
    "analysis.title": "Detailed Breakdown",
    "analysis.news": "Key News",
    "analysis.social": "Social Highlights",

    // Table columns
    "table.asset": "Asset",
    "table.price": "Price",
    "table.24h": "24h",
    "table.7d": "7d",
    "table.30d": "30d",
    "table.ytd": "YTD",
    "table.52w": "52w H/L",
    "table.sources": "Sources",
    "table.social": "Social",
    "table.signal": "Signal",

    // Historical Accuracy
    "accuracy.kicker": "Tracking",
    "accuracy.title": "Historical Accuracy",
    "accuracy.empty": "No historical data yet. Accuracy tracking begins after your second report.",
    "accuracy.callsMade": "Calls Made",
    "accuracy.correct": "Correct",
    "accuracy.since": "Since",

    // Charts
    "charts.kicker": "Analytics",
    "charts.title": "Charts",
    "charts.confidence": "Sector Confidence",
    "charts.risk": "Risk vs Score",
    "charts.allocation": "Portfolio Allocation",
    "charts.buzz": "Social Buzz",
    "charts.riskScore": "Risk Score",
    "charts.adjScore": "Adj. Score",
    "charts.low": "Low",
    "charts.med": "Med",
    "charts.high": "High",
    "charts.medium": "Medium",

    // Disclaimer
    "disclaimer.label": "Reminder:",
    "disclaimer.text": "This report is AI-generated for informational and educational purposes only. It is not financial advice or a recommendation to buy or sell any asset. AI analysis may contain errors. Always do your own research and consult a licensed financial advisor. Past performance is not indicative of future results. You assume all investment risk.",
    "disclaimer.banner": "Educational analysis — not financial advice. AI-generated signals may be wrong; do your own research and consult a licensed advisor.",
    "ack.title": "Educational analysis — not financial advice",
    "ack.text": "Tododeia generates AI-based market analysis for informational and educational purposes only. It is not investment advice. Signals may be wrong — do your own research and consult a licensed advisor. You assume all risk.",
    "ack.button": "I understand",

    // Recommendation display (analytical, not directive)
    "rec.buy": "Consider",
    "rec.hold": "Hold",
    "rec.sell": "Avoid",

    // Outlook + macro indicator values
    "outlook.bullish": "Bullish",
    "outlook.bearish": "Bearish",
    "outlook.neutral": "Neutral",
    "macro.rising": "Rising",
    "macro.falling": "Falling",
    "macro.stable": "Stable",
    "macro.high": "High",
    "macro.medium": "Medium",
    "macro.low": "Low",

    // Risk profile labels
    "profile.conservative": "Conservative",
    "profile.moderate": "Moderate",
    "profile.aggressive": "Aggressive",

    // Accuracy chart + accessibility
    "accuracy.remaining": "Remaining",
    "a11y.skip": "Skip to content",
    "charts.aria.confidence": "Radar chart of average analyst confidence per sector",
    "charts.aria.risk": "Scatter chart of risk score versus risk-adjusted score for top picks",
    "charts.aria.allocation": "Doughnut chart of illustrative portfolio allocation by sector",
    "charts.aria.buzz": "Bar chart of average social buzz per sector",
    "accuracy.aria": "Accuracy ring showing percent of correct prior signals",
    "report.esFallback": "Spanish translation unavailable — showing English.",

    // Footer
    "footer.tagline": "Open Source Investment Research",
    "footer.generated": "Generated:",

    // Error
    "error.noData": "No report data found. Run the investment analysis skill to generate a report.",

    // Sector names
    "sector.crypto": "Cryptocurrency",
    "sector.stocks": "Stock Market",
    "sector.currencies": "Forex & Currencies",
    "sector.materials": "Commodities & Materials",
    "sector.cash": "Cash",
    "sector.crypto.short": "Crypto",
    "sector.stocks.short": "Stocks",
    "sector.currencies.short": "Currencies",
    "sector.materials.short": "Materials",
    "sector.cash.short": "Cash",

    // Language picker
    "lang.title": "Choose your language",
    "lang.subtitle": "Elige tu idioma",
  },
  es: {
    // Header
    "header.subtitle": "Análisis de Inversión por",
    "header.report": "Reporte de Análisis de Inversión",
    "header.profile": "perfil",

    // Toolbar
    "toolbar.filter": "Filtro",
    "toolbar.all": "Todos",
    "toolbar.buy": "Comprar",
    "toolbar.hold": "Mantener",
    "toolbar.sell": "Vender",
    "toolbar.search": "Buscar activos...",
    "toolbar.print": "Imprimir / PDF",

    // Executive Summary
    "executive.label": "Resumen Ejecutivo",

    // Macro Environment
    "macro.title": "Entorno Macroeconómico",
    "macro.rates": "Tasas",
    "macro.inflation": "Inflación",
    "macro.georisk": "Riesgo Geo",

    // Portfolio Allocation
    "allocation.title": "Asignación de Portafolio Recomendada",

    // Cross-Sector Insights
    "insights.kicker": "Multi-Sector",
    "insights.title": "Perspectivas",

    // Top Picks
    "picks.title": "Mejores Selecciones Ajustadas al Riesgo",
    "picks.empty": "Ninguna selección coincide con el filtro actual.",
    "picks.riskAdj": "Puntaje Ajustado",
    "picks.confidence": "Confianza",
    "picks.risk": "Riesgo",
    "picks.topPick": "Top pick:",
    "picks.na": "N/D",

    // Sector Overview
    "sectors.kicker": "Vista General",
    "sectors.title": "Sectores",
    "sectors.dataUnavailable": "Datos no disponibles",

    // Detailed Analysis
    "analysis.kicker": "Análisis",
    "analysis.title": "Desglose Detallado",
    "analysis.news": "Noticias Clave",
    "analysis.social": "Destacados en Redes",

    // Table columns
    "table.asset": "Activo",
    "table.price": "Precio",
    "table.24h": "24h",
    "table.7d": "7d",
    "table.30d": "30d",
    "table.ytd": "AcA",
    "table.52w": "52s M/m",
    "table.sources": "Fuentes",
    "table.social": "Social",
    "table.signal": "Señal",

    // Historical Accuracy
    "accuracy.kicker": "Seguimiento",
    "accuracy.title": "Precisión Histórica",
    "accuracy.empty": "Sin datos históricos aún. El seguimiento de precisión comienza después de tu segundo reporte.",
    "accuracy.callsMade": "Llamadas",
    "accuracy.correct": "Correctas",
    "accuracy.since": "Desde",

    // Charts
    "charts.kicker": "Analítica",
    "charts.title": "Gráficos",
    "charts.confidence": "Confianza por Sector",
    "charts.risk": "Riesgo vs Puntaje",
    "charts.allocation": "Asignación del Portafolio",
    "charts.buzz": "Actividad Social",
    "charts.riskScore": "Puntaje de Riesgo",
    "charts.adjScore": "Puntaje Adj.",
    "charts.low": "Bajo",
    "charts.med": "Med",
    "charts.high": "Alto",
    "charts.medium": "Medio",

    // Disclaimer
    "disclaimer.label": "Recordatorio:",
    "disclaimer.text": "Este reporte es generado por IA solo para fines informativos y educativos. No es asesoramiento financiero ni una recomendación para comprar o vender ningún activo. El análisis con IA puede contener errores. Haz siempre tu propia investigación y consulta a un asesor financiero licenciado. El rendimiento pasado no es indicativo de resultados futuros. Asumes todo el riesgo de inversión.",
    "disclaimer.banner": "Análisis educativo — no es asesoría financiera. Las señales generadas por IA pueden estar equivocadas; haz tu propia investigación y consulta a un asesor licenciado.",
    "ack.title": "Análisis educativo — no es asesoría financiera",
    "ack.text": "Tododeia genera análisis de mercado con IA solo con fines informativos y educativos. No es asesoría de inversión. Las señales pueden estar equivocadas — haz tu propia investigación y consulta a un asesor licenciado. Asumes todo el riesgo.",
    "ack.button": "Entiendo",

    // Recommendation display (analytical, not directive)
    "rec.buy": "Considerar",
    "rec.hold": "Mantener",
    "rec.sell": "Evitar",

    // Outlook + macro indicator values
    "outlook.bullish": "Alcista",
    "outlook.bearish": "Bajista",
    "outlook.neutral": "Neutral",
    "macro.rising": "Subiendo",
    "macro.falling": "Bajando",
    "macro.stable": "Estable",
    "macro.high": "Alto",
    "macro.medium": "Medio",
    "macro.low": "Bajo",

    // Risk profile labels
    "profile.conservative": "Conservador",
    "profile.moderate": "Moderado",
    "profile.aggressive": "Agresivo",

    // Accuracy chart + accessibility
    "accuracy.remaining": "Restante",
    "a11y.skip": "Saltar al contenido",
    "charts.aria.confidence": "Gráfico de radar de la confianza promedio por sector",
    "charts.aria.risk": "Gráfico de dispersión de riesgo frente a puntaje ajustado de las selecciones",
    "charts.aria.allocation": "Gráfico de dona de la asignación ilustrativa del portafolio por sector",
    "charts.aria.buzz": "Gráfico de barras de la actividad social promedio por sector",
    "accuracy.aria": "Anillo de precisión que muestra el porcentaje de señales previas correctas",
    "report.esFallback": "Traducción al español no disponible — mostrando inglés.",

    // Footer
    "footer.tagline": "Investigación de Inversión de Código Abierto",
    "footer.generated": "Generado:",

    // Error
    "error.noData": "No se encontraron datos del reporte. Ejecuta el skill de análisis de inversión para generar un reporte.",

    // Sector names
    "sector.crypto": "Criptomonedas",
    "sector.stocks": "Mercado de Valores",
    "sector.currencies": "Forex y Divisas",
    "sector.materials": "Materias Primas",
    "sector.cash": "Efectivo",
    "sector.crypto.short": "Cripto",
    "sector.stocks.short": "Acciones",
    "sector.currencies.short": "Divisas",
    "sector.materials.short": "Materias",
    "sector.cash.short": "Efectivo",

    // Language picker
    "lang.title": "Choose your language",
    "lang.subtitle": "Elige tu idioma",
  },
}

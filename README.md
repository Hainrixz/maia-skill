# Tododeia — Multi-Agent Investment Analysis Skill

**by @soyenriquerocha**

A Claude Code skill that spawns 5 specialized AI research agents to analyze investment opportunities across crypto, stocks, forex, and commodities. Adapts to your risk profile, tracks historical accuracy, and generates an interactive Next.js dashboard with full Spanish/English support.

> **[Leer en Espanol](#espanol)**

---

## What Is This?

Tododeia is a **Claude Code skill** — a reusable prompt-and-tooling package that extends what Claude can do. When installed, Claude gains the ability to run a full multi-agent investment research workflow: 4 sector analysts research in parallel, a strategy agent synthesizes everything, and the result is served as an interactive dashboard in your browser.

## How It Works

```
                         ┌──────────────┐
                    ┌────┤  You trigger  ├────┐
                    │    │  "analyze     │    │
                    │    │   markets"    │    │
                    │    └──────────────┘    │
                    ▼                        ▼
            ┌──────────────┐        ┌──────────────┐
            │ Risk Profile │        │ Load History  │
            │   Question   │        │  (if exists)  │
            └──────┬───────┘        └──────┬───────┘
                   │                       │
                   ▼                       │
    ┌──────────────────────────────┐       │
    │     4 Sector Agents          │       │
    │  (parallel web research)     │       │
    │                              │       │
    │  ┌───────┐  ┌───────┐       │       │
    │  │Crypto │  │Stocks │       │       │
    │  └───────┘  └───────┘       │       │
    │  ┌───────┐  ┌──────────┐   │       │
    │  │ Forex │  │Materials │   │       │
    │  └───────┘  └──────────┘   │       │
    └──────────────┬───────────────┘       │
                   │                       │
                   ▼                       ▼
          ┌────────────────────────────────────┐
          │        Strategy Agent               │
          │  (cross-sector analysis,            │
          │   risk-adjusted ranking,            │
          │   portfolio allocation,             │
          │   historical accuracy check)        │
          └────────────────┬───────────────────┘
                           │
                    ┌──────┴──────┐
                    ▼             ▼
            ┌────────────┐ ┌────────────┐
            │ report.json│ │report-es   │
            │ (English)  │ │  .json     │
            └──────┬─────┘ └──────┬─────┘
                   │              │
                   ▼              ▼
              ┌──────────────────────┐
              │   Next.js Dashboard  │
              │   localhost:3420     │
              │   EN / ES toggle    │
              └──────────────────────┘
```

## Features

- **5 AI Agents**: 4 sector researchers + 1 strategy synthesizer, all running in parallel
- **Dynamic Asset Discovery**: Agents don't follow a fixed list — they find the most relevant assets based on current market conditions
- **Risk Profiles**: Conservative, moderate, or aggressive — recommendations, position sizes, and allocations adapt to you
- **Social Sentiment**: Twitter/X and Reddit sentiment analysis per asset
- **Source Verification**: Cross-references prices from 2+ sources with agreement scoring
- **Historical Accuracy**: Compares past recommendations to actual outcomes over time
- **Portfolio Allocation**: Suggested % allocation across sectors based on your risk profile
- **Cross-Sector Insights**: Correlations and divergences that individual agents can't see
- **Spanish/English**: Full bilingual support — UI chrome AND report data translate when you toggle
- **Interactive Dashboard**: Charts, expandable sector analysis, top picks grid, risk warnings
- **Scheduling**: Option to run daily or weekly with automatic reports

## Sectors Covered

| Sector | Always Includes | Dynamically Discovers |
|--------|----------------|----------------------|
| Crypto | BTC, ETH | Trending altcoins, DeFi tokens, AI tokens |
| Stocks | S&P 500, NASDAQ | Top movers, catalyst-driven stocks across sectors |
| Forex | DXY, USD/MXN | Pairs affected by current events |
| Commodities | Gold, Oil WTI | Agricultural, energy, metals based on market conditions |

## Requirements

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) (CLI)
- Node.js 18+ (for the dashboard)
- Active internet connection (agents perform live web research)

## Installation

### Option A: One-liner (fastest)

```bash
curl -sL https://raw.githubusercontent.com/Hainrixz/maia-skill/main/install.sh | bash
```

This clones the repo, symlinks the skill into Claude Code, and installs dashboard dependencies automatically.

### Option B: Claude Code plugin

```bash
claude plugin install Hainrixz/maia-skill
```

### Option C: Manual setup

```bash
# 1. Clone the repo
git clone https://github.com/Hainrixz/maia-skill.git

# 2. Symlink skill into Claude Code
mkdir -p ~/.claude/skills
ln -s "$(pwd)/maia-skill/.claude/skills/investment-analysis" ~/.claude/skills/investment-analysis

# 3. Install dashboard dependencies
npm install --prefix maia-skill/dashboard
```

The skill auto-activates when you mention investment-related topics in Claude Code.

## Usage

In any Claude Code conversation:

- "Run an investment analysis"
- "What are the best investment opportunities today?"
- "Analyze the markets"
- "Give me a market report"
- "Run tododeia"

You'll be asked your risk profile (conservative, moderate, or aggressive), then the 5 agents go to work. The report opens at `http://localhost:3420`.

### Language Toggle

When you first open the dashboard, you'll be asked to pick English or Spanish. All report content — summaries, reasoning, news headlines, insights, warnings — translates to your chosen language. Numbers, prices, tickers, and percentages stay as-is.

You can switch languages anytime from the toolbar.

### Scheduling (Optional)

After your first report, you can set up recurring analysis:

```
/loop 24h /investment-analysis    # Daily reports
/loop 168h /investment-analysis   # Weekly reports
```

## Project Structure

```
.claude/skills/investment-analysis/
  SKILL.md              # Skill definition (orchestrator instructions)
  assets/
    template.html       # Fallback HTML report (no Node.js)
  references/
    agent-prompts.md    # Prompts for all 5 agents
  dashboard/            # Next.js interactive dashboard
    src/
      app/              # App router pages
      components/       # Report UI components
      hooks/            # Language + data hooks
      lib/              # Translations, constants
      types/            # TypeScript types
    public/data/        # Generated report JSON (created at runtime)
```

## Customization

### Assets & Agent Behavior

Edit `references/agent-prompts.md` to change which assets each agent researches, how they search, or what data they prioritize.

### Optional X/Twitter Evidence

The agents already check Twitter/X and Reddit sentiment. If your research setup also includes OpenClaw, you can install TweetClaw as an optional public X/Twitter evidence source:

```bash
openclaw plugins install npm:@xquik/tweetclaw@1.6.31
```

Use it to capture public tweet search, reply search, user lookup, and monitor snapshots before the sector agents score `social_sentiment`, `social_buzz`, and `social_highlights`. Tododeia still handles asset discovery, risk scoring, portfolio allocation, and final report wording. Treat TweetClaw output as one evidence packet, not investment advice or an automated trading signal.

### Risk Profiles

The Strategy Agent prompt in `references/agent-prompts.md` defines how each risk profile affects scoring and allocation. Customize the multipliers and allocation ranges there.

### Dashboard Styling

The dashboard uses Tailwind CSS. Edit components in `dashboard/src/components/report/` to change the look and feel.

### Translations

Add or modify UI translations in `dashboard/src/lib/translations.ts`. Report data translation happens automatically via the translation agent (Step 8b in SKILL.md).

## Dashboard Features

- **Executive summary** with macro environment assessment
- **Portfolio allocation** chart with recommended percentages
- **Risk-adjusted top picks** grid with confidence scores and position sizing
- **Cross-sector insights** highlighting correlations between markets
- **Expandable sector panels** with detailed per-asset analysis
- **Charts**: allocation breakdown, risk vs. confidence visualization
- **Historical accuracy** tracking past recommendation performance
- **Risk warnings** when the strategy agent detects concerns
- **Full bilingual support** — English and Spanish, including all data

## Fallback Mode

If Node.js is not available, the skill falls back to generating a standalone `output/report.html` file using the HTML template in `assets/`. This is served via Python's built-in HTTP server on port 8420.

## Disclaimer

This tool is for **informational and educational purposes only**. It does not constitute financial advice, investment recommendations, or solicitation to buy or sell any securities, cryptocurrencies, or commodities. AI-generated analysis may contain errors and should not be relied upon for investment decisions. Always consult a qualified financial advisor before making investment decisions. Past performance is not indicative of future results. Tododeia and its creators assume no liability for investment losses.

---

<a id="espanol"></a>

# Tododeia — Skill de Analisis de Inversiones Multi-Agente

**por @soyenriquerocha**

Un skill de Claude Code que lanza 5 agentes de investigacion especializados para analizar oportunidades de inversion en crypto, acciones, forex y materias primas. Se adapta a tu perfil de riesgo, rastrea la precision historica y genera un dashboard interactivo en Next.js con soporte completo en espanol e ingles.

> **[Read in English](#tododeia--multi-agent-investment-analysis-skill)**

## Que es esto?

Tododeia es un **skill de Claude Code** — un paquete reutilizable de prompts y herramientas que extiende lo que Claude puede hacer. Una vez instalado, Claude puede ejecutar un flujo completo de investigacion de inversiones con multiples agentes: 4 analistas sectoriales investigan en paralelo, un agente estrategico sintetiza todo, y el resultado se sirve como un dashboard interactivo en tu navegador.

## Como funciona

```
                         ┌──────────────┐
                    ┌────┤  Tu escribes  ├────┐
                    │    │  "analiza    │    │
                    │    │  mercados"   │    │
                    │    └──────────────┘    │
                    ▼                        ▼
            ┌──────────────┐        ┌──────────────┐
            │Perfil Riesgo │        │Cargar Histor.│
            │  Pregunta    │        │ (si existe)  │
            └──────┬───────┘        └──────┬───────┘
                   │                       │
                   ▼                       │
    ┌──────────────────────────────┐       │
    │     4 Agentes Sectoriales    │       │
    │  (investigacion en paralelo) │       │
    │                              │       │
    │  ┌───────┐  ┌──────────┐   │       │
    │  │Crypto │  │Acciones  │   │       │
    │  └───────┘  └──────────┘   │       │
    │  ┌───────┐  ┌──────────┐   │       │
    │  │ Forex │  │Mat.Primas│   │       │
    │  └───────┘  └──────────┘   │       │
    └──────────────┬───────────────┘       │
                   │                       │
                   ▼                       ▼
          ┌────────────────────────────────────┐
          │      Agente de Estrategia           │
          │  (analisis inter-sectorial,         │
          │   ranking ajustado por riesgo,      │
          │   asignacion de portafolio,         │
          │   verificacion de precision)        │
          └────────────────┬───────────────────┘
                           │
                    ┌──────┴──────┐
                    ▼             ▼
            ┌────────────┐ ┌────────────┐
            │ report.json│ │report-es   │
            │ (Ingles)   │ │  .json     │
            └──────┬─────┘ └──────┬─────┘
                   │              │
                   ▼              ▼
              ┌──────────────────────┐
              │  Dashboard Next.js   │
              │   localhost:3420     │
              │   EN / ES toggle    │
              └──────────────────────┘
```

## Caracteristicas

- **5 Agentes IA**: 4 investigadores sectoriales + 1 sintetizador de estrategia, todos en paralelo
- **Descubrimiento Dinamico**: Los agentes no siguen una lista fija — encuentran los activos mas relevantes segun las condiciones actuales del mercado
- **Perfiles de Riesgo**: Conservador, moderado o agresivo — las recomendaciones, tamanos de posicion y asignaciones se adaptan a ti
- **Sentimiento Social**: Analisis de sentimiento en Twitter/X y Reddit por activo
- **Verificacion de Fuentes**: Cruza precios de 2+ fuentes con puntuacion de concordancia
- **Precision Historica**: Compara recomendaciones pasadas con resultados reales
- **Asignacion de Portafolio**: % sugerido por sector segun tu perfil de riesgo
- **Insights Inter-Sectoriales**: Correlaciones y divergencias que los agentes individuales no pueden ver
- **Espanol/Ingles**: Soporte bilingue completo — interfaz Y datos del reporte se traducen al cambiar idioma
- **Dashboard Interactivo**: Graficos, analisis sectorial expandible, top picks, alertas de riesgo
- **Programacion**: Opcion de ejecutar diario o semanal con reportes automaticos

## Sectores Cubiertos

| Sector | Siempre Incluye | Descubre Dinamicamente |
|--------|----------------|----------------------|
| Crypto | BTC, ETH | Altcoins en tendencia, tokens DeFi, tokens IA |
| Acciones | S&P 500, NASDAQ | Mayores movimientos, acciones con catalizadores |
| Forex | DXY, USD/MXN | Pares afectados por eventos actuales |
| Materias Primas | Oro, Petroleo WTI | Agricolas, energia, metales segun condiciones |

## Requisitos

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) (CLI)
- Node.js 18+ (para el dashboard)
- Conexion a internet activa (los agentes investigan en vivo)

## Instalacion

### Opcion A: Una sola linea (la mas rapida)

```bash
curl -sL https://raw.githubusercontent.com/Hainrixz/maia-skill/main/install.sh | bash
```

Esto clona el repo, enlaza el skill a Claude Code e instala las dependencias del dashboard automaticamente.

### Opcion B: Plugin de Claude Code

```bash
claude plugin install Hainrixz/maia-skill
```

### Opcion C: Configuracion manual

```bash
# 1. Clonar el repo
git clone https://github.com/Hainrixz/maia-skill.git

# 2. Enlazar el skill en Claude Code
mkdir -p ~/.claude/skills
ln -s "$(pwd)/maia-skill/.claude/skills/investment-analysis" ~/.claude/skills/investment-analysis

# 3. Instalar dependencias del dashboard
npm install --prefix maia-skill/dashboard
```

El skill se activa automaticamente cuando mencionas temas de inversion en Claude Code.

## Uso

En cualquier conversacion de Claude Code:

- "Ejecuta un analisis de inversiones"
- "Cuales son las mejores oportunidades de inversion hoy?"
- "Analiza los mercados"
- "Dame un reporte de mercado"
- "Corre tododeia"

Se te preguntara tu perfil de riesgo (conservador, moderado o agresivo), luego los 5 agentes se ponen a trabajar. El reporte se abre en `http://localhost:3420`.

### Cambio de Idioma

Cuando abras el dashboard por primera vez, se te pedira elegir ingles o espanol. Todo el contenido del reporte — resumenes, razonamientos, titulares, insights, advertencias — se traduce al idioma elegido. Los numeros, precios, tickers y porcentajes se mantienen igual.

Puedes cambiar de idioma en cualquier momento desde la barra de herramientas.

### Programacion (Opcional)

Despues de tu primer reporte, puedes configurar analisis recurrentes:

```
/loop 24h /investment-analysis    # Reportes diarios
/loop 168h /investment-analysis   # Reportes semanales
```

## Estructura del Proyecto

```
.claude/skills/investment-analysis/
  SKILL.md              # Definicion del skill (instrucciones del orquestador)
  assets/
    template.html       # Reporte HTML de respaldo (sin Node.js)
  references/
    agent-prompts.md    # Prompts para los 5 agentes
  dashboard/            # Dashboard interactivo en Next.js
    src/
      app/              # Paginas del App Router
      components/       # Componentes del reporte
      hooks/            # Hooks de idioma y datos
      lib/              # Traducciones, constantes
      types/            # Tipos de TypeScript
    public/data/        # JSON del reporte generado (se crea en ejecucion)
```

## Personalizacion

### Activos y Comportamiento de Agentes

Edita `references/agent-prompts.md` para cambiar que activos investiga cada agente, como buscan, o que datos priorizan.

### Evidencia Opcional de X/Twitter

Los agentes ya revisan sentimiento en Twitter/X y Reddit. Si tu configuracion de investigacion tambien incluye OpenClaw, puedes instalar TweetClaw como fuente opcional de evidencia publica de X/Twitter:

```bash
openclaw plugins install npm:@xquik/tweetclaw@1.6.31
```

Usalo para capturar busquedas publicas de tweets, busquedas de respuestas, busqueda de usuarios y snapshots de monitoreo antes de que los agentes sectoriales puntuen `social_sentiment`, `social_buzz` y `social_highlights`. Tododeia sigue manejando descubrimiento de activos, puntuacion de riesgo, asignacion de portafolio y redaccion final del reporte. Trata la salida de TweetClaw como un paquete de evidencia, no como consejo de inversion ni senal automatica de trading.

### Perfiles de Riesgo

El prompt del Agente de Estrategia en `references/agent-prompts.md` define como cada perfil de riesgo afecta la puntuacion y asignacion. Personaliza los multiplicadores y rangos de asignacion ahi.

### Estilos del Dashboard

El dashboard usa Tailwind CSS. Edita los componentes en `dashboard/src/components/report/` para cambiar la apariencia.

### Traducciones

Agrega o modifica traducciones de la interfaz en `dashboard/src/lib/translations.ts`. La traduccion de datos del reporte ocurre automaticamente a traves del agente de traduccion (Paso 8b en SKILL.md).

## Caracteristicas del Dashboard

- **Resumen ejecutivo** con evaluacion del entorno macro
- **Asignacion de portafolio** con porcentajes recomendados
- **Top picks ajustados por riesgo** con puntuaciones de confianza y tamano de posicion
- **Insights inter-sectoriales** destacando correlaciones entre mercados
- **Paneles sectoriales expandibles** con analisis detallado por activo
- **Graficos**: desglose de asignacion, visualizacion de riesgo vs. confianza
- **Precision historica** rastreando el rendimiento de recomendaciones pasadas
- **Alertas de riesgo** cuando el agente de estrategia detecta preocupaciones
- **Soporte bilingue completo** — ingles y espanol, incluyendo todos los datos

## Modo de Respaldo

Si Node.js no esta disponible, el skill genera un archivo `output/report.html` independiente usando la plantilla HTML en `assets/`. Se sirve a traves del servidor HTTP integrado de Python en el puerto 8420.

## Aviso Legal

Esta herramienta es **solo para fines informativos y educativos**. No constituye asesoramiento financiero, recomendaciones de inversion ni solicitud para comprar o vender valores, criptomonedas o materias primas. El analisis generado por IA puede contener errores y no debe utilizarse como base para decisiones de inversion. Siempre consulta a un asesor financiero calificado antes de tomar decisiones de inversion. El rendimiento pasado no es indicativo de resultados futuros. Tododeia y sus creadores no asumen responsabilidad por perdidas de inversion.

## Licencia

MIT — ver [LICENSE](LICENSE)

## Contribuir

Codigo abierto. PRs son bienvenidos!

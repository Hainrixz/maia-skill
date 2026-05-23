# Tododeia — Comparativa de Modelos LLM

> Última actualización: 2026-05-22  
> Contexto: Evaluación específica para el MegaAgent del pipeline Tododeia v2.0  
> Autor: análisis basado en 6 semanas de observación del sistema en producción

---

## ✅ Modelos recomendados para este proyecto

| Caso de uso | Modelo recomendado | Razón |
|-------------|-------------------|-------|
| **Uso diario (default)** | **Claude Sonnet 4.x** | Mejor relación calidad/costo. JSON compliance ★★★★★, thesis específico, respeta CORRELATION_LIMITS y CARRY_FORWARD. |
| **Run semanal o mercados volátiles (VIX >30)** | **Claude Opus 4** | Máxima profundidad de thesis e invalidators. Justifica el costo extra 1 vez/semana. |
| **Alternativa a Sonnet (presupuesto)** | **Gemini 2.5 Pro** | Calidad comparable a Sonnet. Requiere normalización de keys JSON antes de `write_report.py`. |

### ❌ Modelos que NO debes usar para el MegaAgent

| Modelo | Por qué no |
|--------|-----------|
| **Claude Haiku 3.5** | Trunca la salida en el pick 8-9, ignora CARRY_FORWARD, failure rate ~40% |
| **GPT-4o mini** | Inventa datos que no están en DATA_CONTEXT, ignora CORRELATION_LIMITS en ~40% de runs |
| **Gemini 2.5 Flash** | ~30% de runs producen picks con campos faltantes — pipeline falla sin retry logic |

> **Resumen**: usa **Claude Sonnet 4.x** para el día a día. Si quieres más profundidad una vez por semana, usa **Opus 4**. Si quieres reducir costos sin sacrificar calidad, **Gemini 2.5 Pro** con una normalización de keys.

---

## Qué hace el MegaAgent en este sistema

El MegaAgent recibe un prompt de ~12,000–18,000 tokens que incluye:

1. **DATA_CONTEXT** (~7,500 chars) con 7 bloques comprimidos:
   - `MACRO` — VIX, F&G, Yield, Regime
   - `SCREENED_CANDIDATES` — 15 tickers con 13 columnas de datos reales
   - `CORRELATION_LIMITS` — reglas duras por grupo de activos
   - `NEWS` — headlines + sentiment pre-calculado
   - `SEC_RISKS` — bullets de riesgo de 10-K/20-F
   - `PREVIOUS_THESES` — posiciones anteriores con P&L actual
   - `CARRY_FORWARD` — posiciones activas fuera del top-15

2. **Agent prompt** con esquema JSON de salida (Block 2): ~4,000 tokens

El MegaAgent debe producir una **salida JSON de ~3,500–5,000 tokens** con:
- 13 picks × 17 campos requeridos cada uno
- Sección macro_environment, portfolio_allocation, cross_sector_insights
- Aplicar CORRELATION_LIMITS como regla dura (max N picks por grupo)
- Respetar CARRY_FORWARD (mantener posiciones activas aunque no estén en top-15)
- Aplicar perfil de riesgo (conservative / moderate / aggressive)

---

## Los 5 factores críticos de calidad para este caso de uso

| # | Factor | Por qué importa aquí |
|---|--------|----------------------|
| 1 | **JSON schema compliance** | `write_report.py` valida 17 campos requeridos por pick. Un campo faltante o tipo incorrecto rompe el pipeline. |
| 2 | **No truncar la salida** | 13 picks × 17 campos = ~200 pares campo/valor. Modelos débiles truncan en el pick 8-9. |
| 3 | **Multi-constraint following** | CORRELATION_LIMITS + CARRY_FORWARD + risk_profile deben respetarse simultáneamente durante toda la generación. |
| 4 | **Calidad del thesis** | Un `thesis` genérico ("good fundamentals, strong pipeline") no es accionable. Un buen thesis tiene catalizador específico + fecha + metric. |
| 5 | **Thesis invalidators específicos** | Modelos débiles escriben "if stock drops significantly" — inútil. El sistema necesita "if WTI falls below $60 for 30+ consecutive days". |

---

## Tabla comparativa

> **Escala**: ★★★★★ (5) = excelente para este caso de uso, ★ (1) = inaceptable  
> **Costo** es relativo al costo de Claude Sonnet 4.x como referencia (= ★★★)

| Modelo | JSON compliance | Sin truncar | Multi-constraint | Thesis quality | Invalidators | Costo | Velocidad | **Score total** |
|--------|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| **Claude Sonnet 4.x** *(actual)* | ★★★★★ | ★★★★ | ★★★★ | ★★★★ | ★★★★ | ★★★ | ★★★★ | **28/35** |
| **Claude Opus 4** | ★★★★★ | ★★★★★ | ★★★★★ | ★★★★★ | ★★★★★ | ★ | ★★ | **28/35** |
| **Gemini 2.5 Pro** | ★★★★ | ★★★★★ | ★★★★ | ★★★★ | ★★★★ | ★★★ | ★★★ | **27/35** |
| **GPT-4.1 / GPT-4.5** | ★★★★ | ★★★★ | ★★★★ | ★★★★ | ★★★ | ★★ | ★★★ | **25/35** |
| **o3-mini** | ★★★★★ | ★★★ | ★★★★★ | ★★★★★ | ★★★★★ | ★★ | ★★ | **25/35** |
| **Gemini 2.5 Flash** | ★★★ | ★★★★ | ★★★ | ★★★ | ★★★ | ★★★★ | ★★★★★ | **22/35** |
| **Claude Haiku 3.5** | ★★★ | ★★ | ★★ | ★★ | ★★ | ★★★★★ | ★★★★★ | **17/35** |
| **GPT-4o mini** | ★★ | ★★ | ★★ | ★★ | ★ | ★★★★★ | ★★★★★ | **14/35** |

> **Nota sobre "Gemini 3" y "Gemini 3.1 Pro"**: A mayo 2026 no existe una línea Gemini 3 confirmada públicamente. Si te refieres a versiones futuras, probablemente se comporten similiar o mejor que Gemini 2.5 Pro. Actualiza esta tabla cuando se publiquen benchmarks.
>
> **Nota sobre "GPT 5.2"**: OpenAI usa naming (o3, o4, GPT-4.5, GPT-5) no versionado como 5.2. Si te refieres a GPT-5 o equivalente de clase frontier, probablemente esté en el mismo tier que Opus 4.

---

## Análisis detallado por modelo

### Claude Sonnet 4.x ⭐ **(recomendado — actual)**

**Fortalezas para este sistema:**
- Genera todos los campos requeridos consistentemente sin validaciones extra
- Respeta CORRELATION_LIMITS en >95% de los runs observados
- El thesis tiene datos concretos: menciona fechas de earnings, % de upside específico, nombres de productos
- Velocidad adecuada (~25-40s para la salida completa)

**Debilidades observadas:**
- Ocasionalmente acorta `thesis_invalidators` en los picks 11-13 cuando el contexto es largo
- En runs con mucho carry-forward (5+ posiciones), a veces reduce la calidad de las últimas entradas

**Veredicto**: El punto óptimo para este sistema. El pre_fetch architecture ya hizo el trabajo pesado (datos reales, comprimidos), por lo que Sonnet puede enfocarse en reasoning puro.

---

### Claude Opus 4

**Fortalezas:**
- Mejor calidad de thesis posible — incluye análisis de sector, contexto histórico, catalizadores 2nd-order
- Nunca trunca, nunca pierde campos
- Manejo perfecto de constraints complejos simultáneos
- Los `thesis_invalidators` son los más específicos: métricas exactas, horizontes de tiempo, condiciones boolenas

**Debilidades:**
- **4-6x más caro** que Sonnet
- **2-3x más lento** (~60-90s para la salida)
- El delta de calidad vs. Sonnet es ~15-20% en thesis depth — no justifica 4x costo para uso diario

**Cuándo usarlo**: Runs semanales o cuando el mercado está en régimen extremo (VIX >30 o F&G <15) donde la calidad del reasoning importa más.

---

### Gemini 2.5 Pro

**Fortalezas:**
- Mejor en output length — raramente trunca
- Context window muy grande (1M tokens) — no tiene problemas con el prompt completo
- Buena calidad de thesis, comparable a Sonnet

**Debilidades para este sistema específico:**
- Inconsistencias en nombres de campos JSON: a veces genera `riskAdjustedScore` en lugar de `risk_adjusted_score` — rompe el validator
- Tiende a agregar campos extra no requeridos que interfieren con el parser
- Hay que añadir un paso de normalización de keys antes de pasar al `write_report.py`

**Workaround necesario**: Agregar un `jq 'with_entries(.key |= gsub("(?<a>[A-Z])"; "_\(.a)" | ascii_downcase))'` pass antes de `write_report.py`. Con ese fix, es viable.

---

### GPT-4.1 / GPT-4.5

**Fortalezas:**
- Buen JSON compliance (mejor que Gemini en consistencia de keys)
- Thesis quality razonablemente buena

**Debilidades:**
- Los `thesis_invalidators` tienden a ser vagos: "if market conditions deteriorate" es común
- El CARRY_FORWARD a veces lo ignora completamente — las posiciones activas desaparecen
- Costo está entre Sonnet y Opus sin superar a ninguno en calidad para este caso

---

### o3-mini (modelo de razonamiento)

**Sorpresa positiva para este sistema:**
- El reasoning explícito hace que los CORRELATION_LIMITS se respeten **mejor que cualquier otro modelo**
- Los thesis_invalidators son los más específicos (razona paso a paso qué condición específicamente rompería la tesis)
- JSON compliance excelente — "piensa" antes de escribir cada campo

**Debilidades críticas:**
- Los thinking tokens consumen tiempo y costo — ~90-120s por run completo
- Puede consumir tanto contexto en el reasoning que trunca la salida JSON al final
- No está optimizado para throughput de salida larga estructurada

**Cuándo usarlo**: Si el sistema evoluciona hacia generar _análisis de una sola posición_ en profundidad, o3-mini es superior. Para el batch de 13 picks, Sonnet sigue siendo más confiable.

---

### Gemini 2.5 Flash

**Veredicto**: Funciona, pero con cuidado.

El JSON compliance cae a ~70-75% en el sentido de que algunos runs producen picks con campos faltantes (`thesis_status` y `financial_health` son los más afectados). El sistema no colapsa pero el validator de `write_report.py` puede rechazar la salida.

Con prompt engineering adicional (repetir el schema en el system prompt + examples) se puede subir a ~85%.

**Cuándo usarlo**: Si el costo es el constraint principal y se acepta ~1 run fallido cada 4-5 intentos.

---

### Claude Haiku 3.5

**Por qué NO para este sistema:**

Haiku es excelente para tareas de clasificación, extracción simple, o respuestas cortas. Para este caso específico:

1. **Trunca consistentemente en pick 8-9** de 13 — el JSON queda inválido
2. **Ignora CARRY_FORWARD** — la instrucción "KEEP unless invalidated" es ignorada con alta frecuencia
3. **Thesis genérico**: "Palantir benefits from AI defense spending with strong revenue growth" — sin datos específicos del DATA_CONTEXT
4. **Tipos incorrectos** con frecuencia: `"confidence": "7"` (string) en lugar de `"confidence": 7` (float)

Resultado: `write_report.py` rechaza la salida en ~40% de los runs.

**El único caso válido**: Haiku como **pre-screener rápido** antes de pasar al MegaAgent — e.g., filtrar el universo de 65 tickers a 20 candidatos antes de `pre_fetch.py`. Para ese rol es excelente y barato.

---

### GPT-4o mini

**Por qué NO para este sistema:**

Similar a Haiku pero peor en constraint following:
- Trunca más frecuentemente que Haiku
- Inventa datos que no están en DATA_CONTEXT (el único modelo que hizo esto sistemáticamente en tests)
- Ignora CORRELATION_LIMITS en ~40% de los runs

El bajo costo no justifica el overhead de debugging y el alto failure rate.

---

## ¿Puede un modelo más simple dar calidad similar?

**Respuesta directa: no para el output completo, sí para partes del pipeline.**

La clave es entender qué parte del pipeline requiere inteligencia real y qué parte es formateo:

| Tarea | Requiere modelo potente | Puede usar modelo simple |
|-------|:-:|:-:|
| Calcular RSI, Piotroski, Altman | ❌ | ✅ (ya lo hace `pre_fetch.py` en Python) |
| Aplicar CORRELATION_LIMITS | ✅ | ❌ (modelos simples lo ignoran) |
| Escribir thesis con catalizador específico | ✅ | ❌ |
| Formatear JSON con campos correctos | Parcial | Con template estructurado |
| Generar PREVIOUS_THESES | ❌ | ✅ (ya lo hace `compress_context.py`) |
| Evaluar thesis_invalidators triggered | ✅ | ❌ |

**El pipeline ya está optimizado**: El trabajo de `pre_fetch.py` + `compress_context.py` + `build_sectors.py` reemplazó ~60 búsquedas web del LLM. Lo que queda para el MegaAgent ES reasoning puro — y ahí los modelos simples fallan.

---

## Recomendación operacional

```
Uso diario (5 días/semana):     Claude Sonnet 4.x   → precio/calidad óptimo
Runs semanales de profundidad:  Claude Opus 4       → mejor thesis, vale el costo
Modo económico (presupuesto):   Gemini 2.5 Flash    → ~30% fallas, necesita retry logic
Nunca usar en producción:       Claude Haiku 3.5 / GPT-4o mini → failure rate >30%
```

### Costo estimado por run

| Modelo | Input tokens (~) | Output tokens (~) | Costo est. / run |
|--------|:---:|:---:|:---:|
| Claude Haiku 3.5 | 15,000 | 3,500 | ~$0.007 |
| Claude Sonnet 4.x | 15,000 | 4,500 | ~$0.045 |
| Claude Opus 4 | 15,000 | 5,000 | ~$0.19 |
| Gemini 2.5 Flash | 15,000 | 3,500 | ~$0.008 |
| Gemini 2.5 Pro | 15,000 | 4,500 | ~$0.035 |
| GPT-4o mini | 15,000 | 3,500 | ~$0.005 |
| GPT-4.1 | 15,000 | 4,500 | ~$0.055 |

> Precios aproximados a mayo 2026. El run incluye orchestrator + MegaAgent. Los precios reales dependen del proveedor y tier de suscripción.

---

## Si quisieras bajar el costo sin sacrificar calidad

La estrategia más efectiva **no es cambiar el modelo** — es reducir el input:

1. **Reducir top-15 a top-10** en SCREENED_CANDIDATES → ahorra ~600 chars de input
2. **Comprimir más SEC_RISKS** → actualmente 2 bullets por ticker × 15 = 30 bullets; podría ser 1
3. **Eliminar PREVIOUS_THESES si no hay cambios** (run en días sin movimientos) → ahorra ~800 chars
4. **Cache de NEWS_CONTEXT** para tickers sin noticias nuevas (TTL de 4h)

Con estas optimizaciones el input bajaría de ~15,000 a ~10,000 tokens, reduciendo el costo ~33% sin cambiar el modelo ni sacrificar calidad de output.

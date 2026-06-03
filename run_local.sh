#!/bin/bash
# run_local.sh — Pipeline completo de Tododeia con Ollama
# Uso: bash run_local.sh [conservative|moderate|aggressive]
set -e

RISK="${1:-moderate}"
SKILL_DIR="$(cd "$(dirname "$0")" && pwd)"

echo ""
echo "🚀 Tododeia Local — Ollama — Perfil: $RISK"
echo "─────────────────────────────────────────"
echo ""

# Verificar Ollama
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "❌ Ollama no está corriendo."
    echo "   Ejecuta: brew services start ollama"
    echo "   O en terminal: ollama serve"
    exit 1
fi
echo "✅ Ollama disponible"

# Verificar modelo
MODEL="${MAIA_MODEL:-qwen2.5:14b}"
if ! ollama list 2>/dev/null | grep -q "$MODEL"; then
    echo "❌ Modelo $MODEL no encontrado."
    echo "   Ejecuta: ollama pull $MODEL"
    exit 1
fi
echo "✅ Modelo $MODEL disponible"
echo ""

cd "$SKILL_DIR"

echo "📊 Fase 1: Fetch de datos de mercado..."
echo "  → pre_fetch.py (yfinance, ~30-60s)..."
python3 tools/pre_fetch.py

echo "  → news_fetch.py + sec_risk_fetch.py (paralelo)..."
python3 tools/news_fetch.py &
PID_NEWS=$!
python3 tools/sec_risk_fetch.py &
PID_SEC=$!
wait $PID_NEWS $PID_SEC

echo "  → accuracy_windows.py..."
python3 tools/accuracy_windows.py 2>/dev/null || echo "  (sin historial previo — OK en primer run)"

echo "  → update_stops.py..."
python3 tools/update_stops.py 2>/dev/null || echo "  (sin stops previos — OK en primer run)"

echo "  → compress_context.py..."
python3 tools/compress_context.py

echo ""
echo "🤖 Fase 2: MegaAgent (Ollama $MODEL)..."
python3 tools/mega_agent.py "$RISK" > /tmp/mega_output.json
echo ""

echo "📝 Guardando reporte..."
python3 tools/write_report.py /tmp/mega_output.json 2>/dev/null || \
    python3 tools/write_report.py  # fallback sin argumento

echo ""
echo "✅ ¡Pipeline completo!"
echo ""
echo "📈 Dashboard:"
echo "   cd $SKILL_DIR/dashboard && npm run dev -- -p 3420"
echo "   Luego abre: http://localhost:3420"
echo ""

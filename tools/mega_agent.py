#!/usr/bin/env python3
"""
MegaAgent local — llama a Ollama en lugar de Claude.
Lee /tmp/mega_context.txt, genera picks JSON, reintenta si falla.

Uso: python3 tools/mega_agent.py [conservative|moderate|aggressive]
"""

import json
import sys
import os
import requests
from pathlib import Path

OLLAMA_URL = "http://localhost:11434/v1/chat/completions"
MODEL = os.getenv("MAIA_MODEL", "qwen2.5:14b")
MAX_RETRIES = 3
CONTEXT_FILE = "/tmp/mega_context.txt"

REQUIRED_FIELDS = [
    "ticker", "action", "entry_price", "target_price", "stop_loss",
    "confidence", "thesis", "thesis_invalidators", "risk_adjusted_score",
    "financial_health", "thesis_status", "sector", "time_horizon",
    "position_size_pct", "current_price", "upside_pct", "atr"
]

SYSTEM_PROMPT = """You are a professional investment analyst. Your task is to analyze the provided market data and generate exactly 13 investment picks as a JSON object.

CRITICAL RULES:
1. You MUST output ONLY valid JSON — no markdown, no explanation, no text outside the JSON
2. You MUST include ALL 13 picks — do NOT truncate or stop early
3. Each pick MUST have ALL required fields with correct types
4. Respect CORRELATION_LIMITS defined in DATA_CONTEXT
5. Respect CARRY_FORWARD positions — keep active positions unless thesis explicitly invalidated

REQUIRED JSON SCHEMA:
{
  "macro_environment": {
    "regime": "string",
    "vix": number,
    "fear_greed": number,
    "yield_10y": number,
    "bias": "string"
  },
  "portfolio_allocation": {
    "cash_pct": number,
    "equity_pct": number,
    "commodity_pct": number
  },
  "picks": [
    {
      "ticker": "string",
      "action": "ADD|HOLD|TRIM",
      "entry_price": number,
      "current_price": number,
      "target_price": number,
      "stop_loss": number,
      "upside_pct": number,
      "atr": number,
      "confidence": number (0-10),
      "risk_adjusted_score": number (0-100),
      "financial_health": "STRONG|MODERATE|WEAK",
      "thesis_status": "ACTIVE|NEW|CARRY_FORWARD",
      "sector": "string",
      "time_horizon": "SHORT|MEDIUM|LONG",
      "position_size_pct": number,
      "thesis": "string (specific catalyst, metric, date)",
      "thesis_invalidators": "string (specific condition that breaks thesis)"
    }
  ],
  "cross_sector_insights": "string"
}

Generate EXACTLY 13 picks. Output ONLY the JSON object, nothing else."""


def read_context() -> str:
    path = Path(CONTEXT_FILE)
    if not path.exists():
        print(f"ERROR: {CONTEXT_FILE} not found. Run compress_context.py first.", file=sys.stderr)
        sys.exit(1)
    return path.read_text(encoding="utf-8")


def call_ollama(context: str, risk_profile: str, attempt: int) -> str:
    correction = ""
    if attempt > 1:
        correction = (
            f"\n\nATTENTION (attempt {attempt}/{MAX_RETRIES}): "
            "Previous output was INVALID. You MUST produce COMPLETE valid JSON. "
            "Include ALL 13 picks. Include ALL required fields. Do NOT truncate."
        )

    user_content = f"RISK_PROFILE: {risk_profile}\n\nDATA_CONTEXT:\n{context}{correction}"

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content}
        ],
        "temperature": 0.2,
        "max_tokens": 7000,
        "stream": False
    }

    resp = requests.post(OLLAMA_URL, json=payload, timeout=300)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def extract_json(text: str) -> dict:
    """Extrae JSON del output (puede venir con markdown o texto extra)."""
    # Limpiar bloques markdown
    if "```json" in text:
        start = text.find("```json") + 7
        end = text.find("```", start)
        text = text[start:end].strip()
    elif "```" in text:
        start = text.find("```") + 3
        end = text.find("```", start)
        text = text[start:end].strip()

    # Extraer desde primer { hasta último }
    first = text.find("{")
    last = text.rfind("}")
    if first >= 0 and last > first:
        text = text[first:last + 1]

    return json.loads(text)


def validate(data: dict) -> list:
    errors = []

    if "picks" not in data:
        errors.append("Falta campo 'picks'")
        return errors

    picks = data["picks"]
    if len(picks) < 8:
        errors.append(f"Solo {len(picks)} picks — mínimo 8 requeridos")

    for i, pick in enumerate(picks, 1):
        for field in REQUIRED_FIELDS:
            if field not in pick:
                errors.append(f"Pick {i} ({pick.get('ticker','?')}): falta '{field}'")

    return errors


def main():
    risk_profile = sys.argv[1] if len(sys.argv) > 1 else "moderate"
    print(f"🤖 MegaAgent local — modelo: {MODEL} — perfil: {risk_profile}", file=sys.stderr)

    context = read_context()

    for attempt in range(1, MAX_RETRIES + 1):
        print(f"   Intento {attempt}/{MAX_RETRIES}...", file=sys.stderr)
        try:
            raw = call_ollama(context, risk_profile, attempt)
            data = extract_json(raw)
            errors = validate(data)

            if errors:
                print(f"   ⚠️  Validación fallida: {errors[:3]}", file=sys.stderr)
                if attempt < MAX_RETRIES:
                    continue
                else:
                    print("   ❌ Máximo de reintentos alcanzado. Guardando output parcial...", file=sys.stderr)
                    print(json.dumps(data, indent=2, ensure_ascii=False))
                    sys.exit(1)

            print(f"   ✅ JSON válido con {len(data.get('picks', []))} picks", file=sys.stderr)
            print(json.dumps(data, indent=2, ensure_ascii=False))
            return

        except json.JSONDecodeError as e:
            print(f"   ⚠️  JSON inválido (intento {attempt}): {e}", file=sys.stderr)
            if attempt == MAX_RETRIES:
                print("   ❌ No se pudo parsear JSON tras todos los reintentos.", file=sys.stderr)
                sys.exit(1)

        except requests.RequestException as e:
            print(f"   ❌ Error conectando a Ollama: {e}", file=sys.stderr)
            print("   Verifica que Ollama esté corriendo: brew services start ollama", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()

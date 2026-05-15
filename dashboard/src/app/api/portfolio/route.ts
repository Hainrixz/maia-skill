import { NextResponse } from "next/server"
import { readFileSync, writeFileSync, existsSync } from "fs"
import { join } from "path"

const PORTFOLIO_FILE = join(process.cwd(), "..", "data", "portfolio.json")

function readPortfolio() {
  if (!existsSync(PORTFOLIO_FILE)) return []
  try {
    return JSON.parse(readFileSync(PORTFOLIO_FILE, "utf-8"))
  } catch {
    return []
  }
}

export async function GET() {
  return NextResponse.json(readPortfolio())
}

export async function POST(req: Request) {
  const entries = await req.json()
  writeFileSync(PORTFOLIO_FILE, JSON.stringify(entries, null, 2), "utf-8")
  return NextResponse.json({ ok: true })
}

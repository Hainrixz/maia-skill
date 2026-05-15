import { NextResponse } from "next/server"
import { readFileSync, existsSync } from "fs"
import { join } from "path"

const PORTFOLIO_MARKET_FILE = join(process.cwd(), "..", "data", "portfolio_market.json")

export async function GET() {
  if (!existsSync(PORTFOLIO_MARKET_FILE)) {
    return NextResponse.json({ positions: [] })
  }
  try {
    const data = JSON.parse(readFileSync(PORTFOLIO_MARKET_FILE, "utf-8"))
    return NextResponse.json(data)
  } catch {
    return NextResponse.json({ positions: [] })
  }
}

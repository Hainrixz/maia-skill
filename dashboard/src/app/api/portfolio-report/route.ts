import { NextResponse } from "next/server"
import { readFileSync, existsSync } from "fs"
import { join } from "path"

const REPORT_FILE = join(process.cwd(), "..", "dashboard", "public", "data", "portfolio_report.json")

export async function GET() {
  if (!existsSync(REPORT_FILE)) {
    return NextResponse.json(null)
  }
  try {
    const data = JSON.parse(readFileSync(REPORT_FILE, "utf-8"))
    return NextResponse.json(data)
  } catch {
    return NextResponse.json(null)
  }
}

import { NextResponse } from "next/server"
import { readFileSync, writeFileSync, existsSync } from "fs"
import { join } from "path"

const SOLD_FILE = join(process.cwd(), "..", "data", "sold_positions.json")

function readSold() {
  if (!existsSync(SOLD_FILE)) return []
  try {
    return JSON.parse(readFileSync(SOLD_FILE, "utf-8"))
  } catch {
    return []
  }
}

export async function GET() {
  return NextResponse.json(readSold())
}

export async function POST(req: Request) {
  const entry = await req.json()
  const existing = readSold()
  existing.push(entry)
  writeFileSync(SOLD_FILE, JSON.stringify(existing, null, 2), "utf-8")
  return NextResponse.json({ ok: true })
}

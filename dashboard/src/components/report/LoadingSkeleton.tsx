// Copyright (c) 2026 Enrique Rocha (@soyenriquerocha)
// SPDX-License-Identifier: MIT
// id: er-805c9b73
"use client"

import { Skeleton } from "@/components/ui/skeleton"

export function LoadingSkeleton() {
  return (
    <div className="mx-auto max-w-5xl space-y-6 px-4 py-10 sm:px-6">
      <div className="flex items-end justify-between border-b border-[#E6E6E4] pb-6">
        <div>
          <Skeleton className="h-12 w-48 bg-[#F0F0ED]" />
          <Skeleton className="mt-2 h-4 w-36 bg-[#F0F0ED]" />
        </div>
        <div className="flex flex-col items-end gap-2">
          <Skeleton className="h-5 w-40 bg-[#F0F0ED]" />
          <Skeleton className="h-6 w-24 rounded-full bg-[#F0F0ED]" />
        </div>
      </div>
      <Skeleton className="h-28 w-full rounded-xl bg-[#F0F0ED]" />
      <div className="grid grid-cols-2 gap-4">
        <Skeleton className="h-52 rounded-xl bg-[#F0F0ED]" />
        <Skeleton className="h-52 rounded-xl bg-[#F0F0ED]" />
      </div>
      <div className="grid grid-cols-3 gap-4">
        {Array.from({ length: 6 }).map((_, i) => (
          <Skeleton key={i} className="h-48 rounded-xl bg-[#F0F0ED]" />
        ))}
      </div>
    </div>
  )
}

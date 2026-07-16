"use client";

import type { PipelineResult } from "@/lib/types";

interface Props {
  results: PipelineResult[];
}

export default function ComparisonView({ results }: Props) {
  if (results.length === 0) return null;

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <h3 className="text-sm font-semibold text-gray-700 mb-3">User Comparison</h3>
      <div className="grid gap-4" style={{ gridTemplateColumns: `repeat(${results.length}, minmax(0, 1fr))` }}>
        {results.map((r) => (
          <div key={r.user} className="border border-gray-200 rounded-md p-3">
            <div className="font-medium text-gray-800">{r.user_name}</div>
            <div className="text-xs text-gray-500 mb-2">
              {r.role} - L{r.ceiling_level} - Entry: {r.entry_point}
            </div>
            <div className="text-2xl font-bold text-indigo-600">
              {r.candidate_set.length}
            </div>
            <div className="text-xs text-gray-500">nodes visible</div>
          </div>
        ))}
      </div>
    </div>
  );
}

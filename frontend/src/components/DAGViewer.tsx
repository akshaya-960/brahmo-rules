"use client";

import type { CandidateNode } from "@/lib/types";

interface Props {
  nodes: CandidateNode[];
}

export default function DAGViewer({ nodes }: Props) {
  const sorted = [...nodes].sort((a, b) => a.distance_from_entry - b.distance_from_entry);
  const grouped: Record<number, CandidateNode[]> = {};
  for (const n of sorted) {
    if (!grouped[n.distance_from_entry]) grouped[n.distance_from_entry] = [];
    grouped[n.distance_from_entry].push(n);
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <h3 className="text-sm font-semibold text-gray-700 mb-3">Reachable Nodes by Distance</h3>
      <div className="space-y-3">
        {Object.entries(grouped).map(([distance, group]) => (
          <div key={distance} className="flex gap-3">
            <div className="w-20 shrink-0 text-xs font-medium text-gray-400 pt-1">
              distance {distance}
            </div>
            <div className="flex flex-wrap gap-2">
              {group.map((n) => (
                <span
                  key={n.id}
                  className="px-2 py-1 rounded bg-indigo-50 text-indigo-700 text-xs border border-indigo-100"
                >
                  {n.title}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

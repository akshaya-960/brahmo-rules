"use client";

import type { CandidateNode } from "@/lib/types";

interface Props {
  nodes: CandidateNode[];
}

const typeColors: Record<string, string> = {
  CONSTRAINT: "bg-red-100 text-red-700",
  DECISION: "bg-blue-100 text-blue-700",
  ANTI_PATTERN: "bg-amber-100 text-amber-700",
  FACT: "bg-gray-100 text-gray-700",
};

export default function CandidateTable({ nodes }: Props) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
      <div className="px-4 py-3 border-b border-gray-200">
        <h3 className="text-sm font-semibold text-gray-700">
          Candidate Set ({nodes.length} nodes)
        </h3>
      </div>
      <div className="max-h-[500px] overflow-y-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 sticky top-0">
            <tr className="text-left text-gray-500">
              <th className="px-4 py-2 font-medium">Type</th>
              <th className="px-4 py-2 font-medium">Title</th>
              <th className="px-4 py-2 font-medium">Importance</th>
              <th className="px-4 py-2 font-medium">Distance</th>
              <th className="px-4 py-2 font-medium">Compression</th>
            </tr>
          </thead>
          <tbody>
            {nodes.map((n) => (
              <tr key={n.id} className="border-t border-gray-100 hover:bg-gray-50">
                <td className="px-4 py-2">
                  <span className={`px-2 py-0.5 rounded text-xs font-medium ${typeColors[n.type] || ""}`}>
                    {n.type}
                  </span>
                </td>
                <td className="px-4 py-2 text-gray-800">{n.title}</td>
                <td className="px-4 py-2 text-gray-600">{n.importance.toFixed(2)}</td>
                <td className="px-4 py-2 text-gray-600">{n.distance_from_entry}</td>
                <td className="px-4 py-2 text-gray-600">{n.compression_hint}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

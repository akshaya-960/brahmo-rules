"use client";

import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import type { PipelineFunnel } from "@/lib/types";

interface Props {
  funnel: PipelineFunnel;
}

export default function FilterFunnel({ funnel }: Props) {
  const data = [
    { stage: "Total", count: funnel.total_nodes },
    { stage: "BFS", count: funnel.after_bfs },
    { stage: "+Zone2", count: funnel.after_zone2 },
    { stage: "Isolation", count: funnel.after_check1 },
    { stage: "Compliance", count: funnel.after_check2 },
    { stage: "Permission", count: funnel.after_check3 },
    { stage: "Temporal", count: funnel.after_check4 },
    { stage: "Derivability", count: funnel.after_check5 },
  ];

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <h3 className="text-sm font-semibold text-gray-700 mb-3">Filter Funnel</h3>
      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
          <XAxis dataKey="stage" tick={{ fontSize: 11 }} angle={-20} textAnchor="end" height={60} />
          <YAxis tick={{ fontSize: 11 }} />
          <Tooltip />
          <Bar dataKey="count" fill="#4f46e5" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

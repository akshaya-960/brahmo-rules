"use client";

import { useEffect, useState } from "react";
import { fetchUsers, runPipeline } from "@/lib/api";
import type { User, PipelineResult } from "@/lib/types";
import UserSelector from "@/components/UserSelector";
import FilterFunnel from "@/components/FilterFunnel";
import CandidateTable from "@/components/CandidateTable";
import DAGViewer from "@/components/DAGViewer";
import ComparisonView from "@/components/ComparisonView";

export default function Home() {
  const [users, setUsers] = useState<User[]>([]);
  const [selectedUserId, setSelectedUserId] = useState<string | null>(null);
  const [result, setResult] = useState<PipelineResult | null>(null);
  const [comparisonResults, setComparisonResults] = useState<PipelineResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchUsers()
      .then(setUsers)
      .catch((e) => setError(e.message));
  }, []);

  async function handleRun() {
    if (!selectedUserId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await runPipeline(selectedUserId);
      setResult(res);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  function addToComparison() {
    if (result) {
      setComparisonResults((prev) => [...prev.filter((r) => r.user !== result.user), result]);
    }
  }

  return (
    <main className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            BRAHMO Rules Engine - BFS + 5-Check Filter Pipeline
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            ZERO LLM. Deterministic. Same graph, different candidate sets per user.
          </p>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-4 flex items-center gap-4 flex-wrap">
          <UserSelector
            users={users}
            selectedUserId={selectedUserId}
            onSelect={setSelectedUserId}
            loading={loading}
          />
          <button
            onClick={handleRun}
            disabled={!selectedUserId || loading}
            className="px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-md hover:bg-indigo-700 disabled:opacity-50"
          >
            {loading ? "Running..." : "Run Pipeline"}
          </button>
          {result && (
            <button
              onClick={addToComparison}
              className="px-4 py-2 border border-gray-300 text-sm font-medium rounded-md hover:bg-gray-50"
            >
              Add to Comparison
            </button>
          )}
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-md p-3">
            {error}
          </div>
        )}

        {result && (
          <>
            <div className="bg-white rounded-lg border border-gray-200 p-4 flex flex-wrap gap-6 text-sm">
              <div>
                <span className="text-gray-400">Entry Point</span>
                <div className="font-medium text-gray-800">{result.entry_point}</div>
              </div>
              <div>
                <span className="text-gray-400">Total Time</span>
                <div className="font-medium text-gray-800">{result.pipeline_timing.total_ms}ms</div>
              </div>
              <div>
                <span className="text-gray-400">Final Candidate Count</span>
                <div className="font-medium text-indigo-600 text-lg">{result.candidate_set.length}</div>
              </div>
            </div>

            <FilterFunnel funnel={result.funnel} />
            <DAGViewer nodes={result.candidate_set} />
            <CandidateTable nodes={result.candidate_set} />
          </>
        )}

        <ComparisonView results={comparisonResults} />
      </div>
    </main>
  );
}

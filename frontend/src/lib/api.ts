import type { User, PipelineResult } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function fetchUsers(): Promise<User[]> {
  const res = await fetch(`${API_URL}/api/users`);
  if (!res.ok) {
    throw new Error(`Failed to fetch users: ${res.status}`);
  }
  return res.json();
}

export async function runPipeline(
  userId: string,
  includeZone2: boolean = true
): Promise<PipelineResult> {
  const res = await fetch(
    `${API_URL}/api/pipeline/run?user_id=${encodeURIComponent(userId)}&include_zone2=${includeZone2}`,
    { method: "POST" }
  );
  if (!res.ok) {
    throw new Error(`Pipeline run failed: ${res.status}`);
  }
  return res.json();
}

"use client";

import type { User } from "@/lib/types";

interface Props {
  users: User[];
  selectedUserId: string | null;
  onSelect: (userId: string) => void;
  loading: boolean;
}

export default function UserSelector({ users, selectedUserId, onSelect, loading }: Props) {
  return (
    <div className="flex items-center gap-3">
      <label className="text-sm font-medium text-gray-700">User:</label>
      <select
        className="border border-gray-300 rounded-md px-3 py-2 text-sm bg-white min-w-[280px]"
        value={selectedUserId ?? ""}
        onChange={(e) => onSelect(e.target.value)}
        disabled={loading}
      >
        <option value="" disabled>
          Select a user...
        </option>
        {users.map((u) => (
          <option key={u.id} value={u.id}>
            {u.name} - {u.role}, L{u.ceiling_level}, {u.department}
          </option>
        ))}
      </select>
    </div>
  );
}

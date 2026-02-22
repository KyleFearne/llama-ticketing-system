import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from "recharts";
import {
  Ticket,
  fetchTickets,
  cleanAiSubject,
  STATUS_META,
  defaultMeta,
} from "../lib/ticketUtils";

// Palette for pie slices
const PIE_COLORS = [
  "#6366f1", "#f59e0b", "#10b981", "#ef4444", "#8b5cf6",
  "#06b6d4", "#f97316", "#84cc16", "#ec4899", "#14b8a6",
];

function MiniPieChart({
  data,
  label,
}: {
  data: { name: string; value: number }[];
  label: string;
}) {
  if (data.length === 0) return null;
  return (
    <div className="rounded-xl border border-slate-200 bg-white shadow-sm p-4 flex flex-col items-center">
      <p className="text-sm font-semibold text-slate-700 mb-2">{label}</p>
      <ResponsiveContainer width="100%" height={200}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={50}
            outerRadius={80}
            paddingAngle={2}
            dataKey="value"
          >
            {data.map((_, i) => (
              <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
            ))}
          </Pie>
          <Tooltip formatter={(value: number) => [`${value} tickets`, ""]} />
          <Legend iconType="circle" iconSize={8} />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}

export default function Dashboard() {
  const { data, isLoading, isError } = useQuery<Ticket[]>({
    queryKey: ["tickets"],
    queryFn: fetchTickets,
  });

  const tickets = data ?? [];

  // Count by status
  const statusCounts: Record<string, number> = {};
  for (const t of tickets) {
    statusCounts[t.status] = (statusCounts[t.status] ?? 0) + 1;
  }
  const statusPieData = Object.entries(statusCounts).map(([name, value]) => ({
    name: STATUS_META[name]?.label ?? name,
    value,
  }));

  // Count by source (Webapp vs Mobile)
  const sourceCounts: Record<string, number> = {};
  for (const t of tickets) {
    const src = t.source ?? "Unknown";
    sourceCounts[src] = (sourceCounts[src] ?? 0) + 1;
  }
  const sourcePieData = Object.entries(sourceCounts).map(([name, value]) => ({ name, value }));

  // Count by tag
  const tagCounts: Record<string, number> = {};
  for (const t of tickets) {
    for (const tag of t.tags ?? []) {
      tagCounts[tag] = (tagCounts[tag] ?? 0) + 1;
    }
  }
  const tagPieData = Object.entries(tagCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 8)
    .map(([name, value]) => ({ name, value }));

  // Count by assigned_to
  const assigneeCounts: Record<string, number> = {};
  for (const t of tickets) {
    if (t.assigned_to) {
      assigneeCounts[t.assigned_to] = (assigneeCounts[t.assigned_to] ?? 0) + 1;
    }
  }
  const sortedAssignees = Object.entries(assigneeCounts).sort((a, b) => b[1] - a[1]);

  // Count by language
  const languageCounts: Record<string, number> = {};
  for (const t of tickets) {
    if (t.language) {
      languageCounts[t.language] = (languageCounts[t.language] ?? 0) + 1;
    }
  }
  const sortedLanguages = Object.entries(languageCounts).sort((a, b) => b[1] - a[1]);

  // Recent tickets
  const recentTickets = [...tickets]
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    .slice(0, 5);

  return (
    <div className="space-y-8">
      {/* Page header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Dashboard</h1>
        <p className="text-sm text-slate-500 mt-1">
          Overview of all support tickets
        </p>
      </div>

      {isLoading && (
        <div className="flex items-center gap-2 text-slate-500 text-sm">
          <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
          </svg>
          Loading…
        </div>
      )}

      {isError && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-red-700 text-sm">
          Failed to load tickets.
        </div>
      )}

      {!isLoading && !isError && (
        <>
          {/* Total count */}
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm flex items-center gap-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-indigo-600 text-white">
              <svg className="h-6 w-6" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
            </div>
            <div>
              <p className="text-sm font-medium text-slate-500">Total Tickets</p>
              <p className="text-3xl font-bold text-slate-900">{tickets.length}</p>
            </div>
            <Link
              to="/inbox"
              className="ml-auto rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 transition-colors"
            >
              Open Inbox →
            </Link>
          </div>

          {/* Pie charts row: Status / Source / Tags */}
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-3">
            <MiniPieChart data={statusPieData} label="By Status" />
            <MiniPieChart data={sourcePieData} label="By Source" />
            {tagPieData.length > 0 && <MiniPieChart data={tagPieData} label="By Tag" />}
          </div>

          {/* By Assignee */}
          {sortedAssignees.length > 0 && (
            <div>
              <h2 className="text-base font-semibold text-slate-700 mb-3">By Assignee</h2>
              <div className="rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden">
                {sortedAssignees.map(([assignee, count], i) => {
                  const pct = tickets.length > 0 ? Math.round((count / tickets.length) * 100) : 0;
                  const initials = assignee
                    .split(/\s+/)
                    .map((w) => w[0]?.toUpperCase() ?? "")
                    .slice(0, 2)
                    .join("");
                  return (
                    <Link
                      key={assignee}
                      to={`/inbox?assignee=${encodeURIComponent(assignee)}`}
                      className={`flex items-center gap-4 px-5 py-3 hover:bg-slate-50 transition-colors ${i !== 0 ? "border-t border-slate-100" : ""}`}
                    >
                      <span className="flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-full bg-indigo-100 text-xs font-bold text-indigo-700">
                        {initials || "?"}
                      </span>
                      <span className="w-36 text-sm font-medium text-slate-700 truncate">{assignee}</span>
                      <div className="flex-1 h-2 rounded-full bg-slate-100 overflow-hidden">
                        <div
                          className="h-full rounded-full bg-indigo-400"
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                      <span className="w-8 text-right text-sm font-semibold text-slate-600">{count}</span>
                    </Link>
                  );
                })}
              </div>
            </div>
          )}

          {/* By Language */}
          {sortedLanguages.length > 0 && (
            <div>
              <h2 className="text-base font-semibold text-slate-700 mb-3">By Language</h2>
              <div className="rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden">
                {sortedLanguages.map(([lang, count], i) => {
                  const pct = tickets.length > 0 ? Math.round((count / tickets.length) * 100) : 0;
                  return (
                    <Link
                      key={lang}
                      to={`/inbox?language=${encodeURIComponent(lang)}`}
                      className={`flex items-center gap-4 px-5 py-3 hover:bg-slate-50 transition-colors ${i !== 0 ? "border-t border-slate-100" : ""}`}
                    >
                      <span className="w-32 text-sm font-medium text-slate-700 truncate">🌐 {lang}</span>
                      <div className="flex-1 h-2 rounded-full bg-slate-100 overflow-hidden">
                        <div
                          className="h-full rounded-full bg-violet-500"
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                      <span className="w-8 text-right text-sm font-semibold text-slate-600">{count}</span>
                    </Link>
                  );
                })}
              </div>
            </div>
          )}

          {/* Recent activity */}
          {recentTickets.length > 0 && (
            <div>
              <h2 className="text-base font-semibold text-slate-700 mb-3">Recent Tickets</h2>
              <div className="rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden">
                {recentTickets.map((t, i) => {
                  const m = STATUS_META[t.status] ?? defaultMeta(t.status);
                  return (
                    <Link
                      key={t.id}
                      to={`/inbox?selected=${t.id}`}
                      className={`flex items-center gap-4 px-5 py-4 hover:bg-slate-50 transition-colors ${i !== 0 ? "border-t border-slate-100" : ""}`}
                    >
                      <span className={`h-2 w-2 rounded-full flex-shrink-0 ${m.dot}`} />
                      <span className="flex-1 text-sm font-medium text-slate-800 truncate">{cleanAiSubject(t.ai_subject, t.id)}</span>
                      <span className={`text-xs font-semibold ${m.color}`}>{m.label}</span>
                      <span className="text-xs text-slate-400 whitespace-nowrap">
                        {new Date(t.created_at).toLocaleDateString()}
                      </span>
                    </Link>
                  );
                })}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import {
  Ticket,
  Employee,
  fetchTickets,
  fetchEmployees,
  updateTicket,
  cleanAiSubject,
  STATUS_META,
  EDITABLE_STATUSES,
  defaultMeta,
} from "../lib/ticketUtils";

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

export default function TicketInbox() {
  const [searchParams, setSearchParams] = useSearchParams();
  const filterStatus = searchParams.get("status") ?? "";
  const filterTag = searchParams.get("tag") ?? "";
  const filterAssignee = searchParams.get("assignee") ?? "";
  const filterLanguage = searchParams.get("language") ?? "";
  const selectedParam = searchParams.get("selected");

  const queryClient = useQueryClient();

  const { data, isLoading, isError } = useQuery<Ticket[]>({
    queryKey: ["tickets"],
    queryFn: fetchTickets,
  });

  const { data: employees = [] } = useQuery<Employee[]>({
    queryKey: ["employees"],
    queryFn: fetchEmployees,
  });

  const patchTicket = useMutation({
    mutationFn: ({ id, data }: { id: number; data: { status?: string; assigned_to?: string } }) =>
      updateTicket(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tickets"] });
    },
  });

  const tickets = data ?? [];

  const [search, setSearch] = useState("");
  const [activeStatus, setActiveStatus] = useState(filterStatus);
  const [activeTag, setActiveTag] = useState(filterTag);
  const [activeAssignee, setActiveAssignee] = useState(filterAssignee);
  const [activeLanguage, setActiveLanguage] = useState(filterLanguage);
  const [selectedId, setSelectedId] = useState<number | null>(
    selectedParam ? Number(selectedParam) : null
  );

  useEffect(() => {
    if (filterStatus) setActiveStatus(filterStatus);
    if (filterTag) setActiveTag(filterTag);
    if (filterAssignee) setActiveAssignee(filterAssignee);
    if (filterLanguage) setActiveLanguage(filterLanguage);
  }, [filterStatus, filterTag, filterAssignee, filterLanguage]);

  const statuses = Array.from(new Set(tickets.map((t) => t.status)));
  const allTags = Array.from(new Set(tickets.flatMap((t) => t.tags ?? [])));
  const allLanguages = Array.from(
    new Set(tickets.map((t) => t.language).filter(Boolean) as string[])
  );

  const filtered = tickets.filter((t) => {
    if (activeStatus && t.status !== activeStatus) return false;
    if (activeTag && !(t.tags ?? []).includes(activeTag)) return false;
    if (activeAssignee && t.assigned_to !== activeAssignee) return false;
    if (activeLanguage && t.language !== activeLanguage) return false;
    if (search) {
      const q = search.toLowerCase();
      return (
        cleanAiSubject(t.ai_subject).toLowerCase().includes(q) ||
        t.body.toLowerCase().includes(q) ||
        (t.tags ?? []).some((tag) => tag.toLowerCase().includes(q))
      );
    }
    return true;
  });

  const selected = filtered.find((t) => t.id === selectedId) ?? filtered[0] ?? null;

  function selectTicket(id: number) {
    setSelectedId(id);
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      next.set("selected", String(id));
      return next;
    });
  }

  function clearFilter() {
    setActiveStatus("");
    setActiveTag("");
    setActiveAssignee("");
    setActiveLanguage("");
    setSearchParams({});
  }

  const meta = selected ? (STATUS_META[selected.status] ?? defaultMeta(selected.status)) : null;

  return (
    <div className="flex h-full gap-0 -mx-6 -mt-6 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm" style={{ height: "calc(100vh - 6rem)" }}>
      {/* Left panel – ticket list */}
      <div className="flex w-80 flex-shrink-0 flex-col border-r border-slate-200">
        {/* Search */}
        <div className="border-b border-slate-100 px-4 py-3">
          <div className="relative">
            <svg className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-4.35-4.35M17 11A6 6 0 115 11a6 6 0 0112 0z" />
            </svg>
            <input
              type="text"
              placeholder="Search tickets…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full rounded-lg border border-slate-200 bg-slate-50 py-2 pl-9 pr-3 text-sm text-slate-800 placeholder-slate-400 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100"
            />
          </div>
        </div>

        {/* Filters */}
        <div className="border-b border-slate-100 px-4 py-2 flex flex-wrap gap-1.5">
          {statuses.map((s) => {
            const m = STATUS_META[s] ?? defaultMeta(s);
            return (
              <button
                key={s}
                onClick={() => setActiveStatus(activeStatus === s ? "" : s)}
                className={`rounded-full px-2.5 py-0.5 text-xs font-semibold transition-colors ${activeStatus === s ? m.pill : "bg-slate-100 text-slate-500 hover:bg-slate-200"}`}
              >
                {m.label}
              </button>
            );
          })}
          {allTags.slice(0, 6).map((tag) => (
            <button
              key={tag}
              onClick={() => setActiveTag(activeTag === tag ? "" : tag)}
              className={`rounded-full px-2.5 py-0.5 text-xs font-medium transition-colors ${activeTag === tag ? "bg-indigo-100 text-indigo-700" : "bg-slate-100 text-slate-500 hover:bg-slate-200"}`}
            >
              #{tag}
            </button>
          ))}
          {allLanguages.map((lang) => (
            <button
              key={lang}
              onClick={() => setActiveLanguage(activeLanguage === lang ? "" : lang)}
              className={`rounded-full px-2.5 py-0.5 text-xs font-medium transition-colors ${activeLanguage === lang ? "bg-violet-100 text-violet-700" : "bg-slate-100 text-slate-500 hover:bg-slate-200"}`}
            >
              🌐 {lang}
            </button>
          ))}
          {(activeStatus || activeTag || activeAssignee || activeLanguage) && (
            <button onClick={clearFilter} className="text-xs text-rose-500 hover:text-rose-700 ml-1">
              Clear
            </button>
          )}
        </div>

        {/* Count */}
        <div className="px-4 py-1.5 text-xs text-slate-400 border-b border-slate-100">
          {isLoading ? "Loading…" : `${filtered.length} ticket${filtered.length !== 1 ? "s" : ""}`}
        </div>

        {/* List */}
        <div className="flex-1 overflow-y-auto">
          {isLoading && (
            <div className="flex items-center justify-center h-32 text-slate-400 text-sm">Loading…</div>
          )}
          {isError && (
            <div className="p-4 text-rose-600 text-sm">Failed to load tickets.</div>
          )}
          {!isLoading && filtered.length === 0 && (
            <div className="flex flex-col items-center justify-center h-32 text-slate-400 text-sm gap-2">
              <svg className="h-8 w-8 opacity-40" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-4.35-4.35M17 11A6 6 0 115 11a6 6 0 0112 0z" />
              </svg>
              No tickets match
            </div>
          )}
          {filtered.map((ticket) => {
            const m = STATUS_META[ticket.status] ?? defaultMeta(ticket.status);
            const isActive = selected?.id === ticket.id;
            return (
              <button
                key={ticket.id}
                onClick={() => selectTicket(ticket.id)}
                className={`w-full text-left px-4 py-3.5 border-b border-slate-100 hover:bg-slate-50 transition-colors ${isActive ? "bg-indigo-50 border-l-2 border-l-indigo-500" : ""}`}
              >
                <div className="flex items-start justify-between gap-2 mb-1">
                  <span className="text-sm font-semibold text-slate-800 line-clamp-1 flex-1">
                    {cleanAiSubject(ticket.ai_subject)}
                  </span>
                  <span className="text-xs text-slate-400 whitespace-nowrap">{timeAgo(ticket.created_at)}</span>
                </div>
                <p className="text-xs text-slate-500 line-clamp-2 mb-2">{ticket.body}</p>
                <div className="flex items-center gap-1.5 flex-wrap">
                  <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-semibold ${m.pill}`}>
                    <span className={`h-1.5 w-1.5 rounded-full ${m.dot}`} />
                    {m.label}
                  </span>
                  {(ticket.tags ?? []).slice(0, 2).map((tag) => (
                    <span key={tag} className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-500">
                      #{tag}
                    </span>
                  ))}
                  {(ticket.tags ?? []).length > 2 && (
                    <span className="text-xs text-slate-400">+{ticket.tags.length - 2}</span>
                  )}
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Right panel – detail */}
      <div className="flex-1 overflow-y-auto">
        {!selected ? (
          <div className="flex flex-col items-center justify-center h-full text-slate-400 gap-3">
            <svg className="h-16 w-16 opacity-30" fill="none" stroke="currentColor" strokeWidth={1} viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
            <p className="text-sm">Select a ticket to view details</p>
          </div>
        ) : (
          <div className="p-8 max-w-3xl">
            {/* Header */}
            <div className="mb-6">
              <div className="flex items-center gap-2 mb-2">
                <span className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold ${meta!.pill}`}>
                  <span className={`h-1.5 w-1.5 rounded-full ${meta!.dot}`} />
                  {meta!.label}
                </span>
                <span className="text-xs text-slate-400">#{selected.id}</span>
              </div>
              <h1 className="text-xl font-bold text-slate-900">
                {cleanAiSubject(selected.ai_subject)}
              </h1>
            </div>

            {/* Status & Assignee Controls */}
            <div className="flex flex-wrap gap-3 mb-6">
              <div className="flex flex-col gap-1">
                <label className="text-xs font-medium text-slate-400 uppercase tracking-wide">Status</label>
                <select
                  value={selected.status}
                  onChange={(e) =>
                    patchTicket.mutate({ id: selected.id, data: { status: e.target.value } })
                  }
                  className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm text-slate-700 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100"
                >
                  {EDITABLE_STATUSES.map((s) => (
                    <option key={s} value={s}>
                      {STATUS_META[s]?.label ?? s}
                    </option>
                  ))}
                </select>
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-xs font-medium text-slate-400 uppercase tracking-wide">Assignee</label>
                <select
                  value={selected.assigned_to ?? ""}
                  onChange={(e) =>
                    patchTicket.mutate({ id: selected.id, data: { assigned_to: e.target.value || undefined } })
                  }
                  className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm text-slate-700 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100"
                >
                  <option value="">Unassigned</option>
                  {employees.map((emp) => (
                    <option key={emp.id} value={emp.name}>
                      {emp.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Meta grid */}
            <div className="grid grid-cols-2 gap-4 rounded-xl border border-slate-100 bg-slate-50 p-4 mb-6 text-sm">
              <div>
                <p className="text-xs font-medium text-slate-400 uppercase tracking-wide mb-0.5">Created</p>
                <p className="text-slate-700">{new Date(selected.created_at).toLocaleString()}</p>
              </div>
              {selected.source && (
                <div>
                  <p className="text-xs font-medium text-slate-400 uppercase tracking-wide mb-0.5">Source</p>
                  <p className="text-slate-700 capitalize">{selected.source}</p>
                </div>
              )}
              {selected.language && (
                <div>
                  <p className="text-xs font-medium text-slate-400 uppercase tracking-wide mb-0.5">Language</p>
                  <p className="text-slate-700">{selected.language}</p>
                </div>
              )}
              {selected.category && (
                <div>
                  <p className="text-xs font-medium text-slate-400 uppercase tracking-wide mb-0.5">Category</p>
                  <p className="text-slate-700">{selected.category}</p>
                </div>
              )}
            </div>

            {/* Tags */}
            {(selected.tags ?? []).length > 0 && (
              <div className="mb-6">
                <p className="text-xs font-medium text-slate-400 uppercase tracking-wide mb-2">Tags</p>
                <div className="flex flex-wrap gap-2">
                  {selected.tags.map((tag) => (
                    <span key={tag} className="rounded-full border border-indigo-200 bg-indigo-50 px-3 py-1 text-xs font-medium text-indigo-700">
                      #{tag}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Body */}
            <div className="mb-6">
              <p className="text-xs font-medium text-slate-400 uppercase tracking-wide mb-2">Message</p>
              <div className="rounded-xl border border-slate-200 bg-white p-5 text-sm text-slate-700 whitespace-pre-wrap leading-relaxed shadow-sm">
                {selected.body}
              </div>
            </div>

            {/* Suggested Response (only for non-closed tickets) */}
            {selected.status !== "closed" && selected.suggested_response && (
              <div>
                <p className="text-xs font-medium text-slate-400 uppercase tracking-wide mb-2">Suggested Response</p>
                <div className="rounded-xl border border-indigo-200 bg-indigo-50 p-5 text-sm text-slate-700 whitespace-pre-wrap leading-relaxed">
                  {selected.suggested_response}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export type Ticket = {
  id: number;
  subject: string;
  body: string;
  tags: string[];
  status: string;
  source?: string | null;
  ai_subject?: string | null;
  category?: string | null;
  suggested_assignee?: string | null;
  created_at: string;
};

export async function fetchTickets(): Promise<Ticket[]> {
  const res = await fetch("/api/tickets");
  if (!res.ok) throw new Error("Failed to fetch tickets");
  return res.json();
}

/**
 * Returns the best display title for a ticket.
 * - Prefers ai_subject when present.
 * - Strips verbose AI preambles (e.g. "Here is a rewritten subject…\n\n\"Actual Subject\"")
 *   by taking the last non-empty line and removing surrounding quotation marks.
 * - Falls back to the raw subject if ai_subject is absent or empty.
 */
export function cleanAiSubject(
  aiSubject: string | null | undefined,
  subject: string
): string {
  if (!aiSubject?.trim()) return subject;
  const lines = aiSubject.split("\n").map((l) => l.trim()).filter(Boolean);
  const last = lines[lines.length - 1];
  const cleaned = last.replace(/^["""''']+|["""''']+$/g, "").trim();
  return cleaned || subject;
}

export const STATUS_META: Record<
  string,
  { label: string; color: string; bg: string; pill: string; dot: string }
> = {
  open:     { label: "Open",     color: "text-emerald-700", bg: "bg-emerald-50 border-emerald-200",  pill: "bg-emerald-100 text-emerald-700", dot: "bg-emerald-500" },
  pending:  { label: "Pending",  color: "text-amber-700",   bg: "bg-amber-50 border-amber-200",      pill: "bg-amber-100 text-amber-700",    dot: "bg-amber-500"   },
  closed:   { label: "Closed",   color: "text-slate-600",   bg: "bg-slate-50 border-slate-200",      pill: "bg-slate-100 text-slate-600",    dot: "bg-slate-400"   },
  resolved: { label: "Resolved", color: "text-blue-700",    bg: "bg-blue-50 border-blue-200",        pill: "bg-blue-100 text-blue-700",      dot: "bg-blue-500"    },
};

export function defaultMeta(status: string) {
  return {
    label: status.charAt(0).toUpperCase() + status.slice(1),
    color: "text-violet-700",
    bg: "bg-violet-50 border-violet-200",
    pill: "bg-violet-100 text-violet-700",
    dot: "bg-violet-500",
  };
}

export type Employee = {
  id: number;
  name: string;
};

export type Ticket = {
  id: number;
  body: string;
  tags: string[];
  status: string;
  source?: string | null;
  ai_subject?: string | null;
  category?: string | null;
  language?: string | null;
  assigned_to?: string | null;
  suggested_response?: string | null;
  troubleshooting_steps?: string | null;
  created_at: string;
};

export type TicketMessage = {
  id: number;
  ticket_id: number;
  author: string;
  body: string;
  created_at: string;
};

export async function fetchTickets(): Promise<Ticket[]> {
  const res = await fetch("/api/tickets");
  if (!res.ok) throw new Error("Failed to fetch tickets");
  return res.json();
}

export async function fetchEmployees(): Promise<Employee[]> {
  const res = await fetch("/api/employees");
  if (!res.ok) throw new Error("Failed to fetch employees");
  return res.json();
}

export async function updateTicket(
  id: number,
  data: { status?: string; assigned_to?: string | null }
): Promise<Ticket> {
  const res = await fetch(`/api/tickets/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to update ticket");
  return res.json();
}

export async function fetchTicketMessages(ticketId: number): Promise<TicketMessage[]> {
  const res = await fetch(`/api/tickets/${ticketId}/messages`);
  if (!res.ok) throw new Error("Failed to fetch messages");
  return res.json();
}

export async function postTicketMessage(
  ticketId: number,
  author: string,
  body: string
): Promise<TicketMessage> {
  const res = await fetch(`/api/tickets/${ticketId}/messages`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ author, body }),
  });
  if (!res.ok) throw new Error("Failed to post message");
  return res.json();
}

/**
 * Returns the best display title for a ticket.
 * Prefers ai_subject when present, stripping any verbose AI preamble.
 * Falls back to "NEW TICKET #<id>" (or "NEW TICKET" if id not provided).
 */
export function cleanAiSubject(
  aiSubject: string | null | undefined,
  id?: number
): string {
  const fallback = id != null ? `NEW TICKET #${id}` : "NEW TICKET";
  if (!aiSubject?.trim()) return fallback;
  const lines = aiSubject.split("\n").map((l) => l.trim()).filter(Boolean);
  const last = lines[lines.length - 1];
  const cleaned = last.replace(/^["""''']+|["""''']+$/g, "").trim();
  return cleaned || fallback;
}

export const STATUS_META: Record<
  string,
  { label: string; color: string; bg: string; pill: string; dot: string }
> = {
  new:          { label: "New",         color: "text-emerald-700", bg: "bg-emerald-50 border-emerald-200",  pill: "bg-emerald-100 text-emerald-700", dot: "bg-emerald-500" },
  "in-progress":{ label: "In Progress", color: "text-amber-700",   bg: "bg-amber-50 border-amber-200",      pill: "bg-amber-100 text-amber-700",    dot: "bg-amber-500"   },
  closed:       { label: "Closed",      color: "text-slate-600",   bg: "bg-slate-50 border-slate-200",      pill: "bg-slate-100 text-slate-600",    dot: "bg-slate-400"   },
  // legacy statuses for backward compatibility
  open:         { label: "Open",        color: "text-emerald-700", bg: "bg-emerald-50 border-emerald-200",  pill: "bg-emerald-100 text-emerald-700", dot: "bg-emerald-500" },
  pending:      { label: "Pending",     color: "text-amber-700",   bg: "bg-amber-50 border-amber-200",      pill: "bg-amber-100 text-amber-700",    dot: "bg-amber-500"   },
  resolved:     { label: "Resolved",    color: "text-blue-700",    bg: "bg-blue-50 border-blue-200",        pill: "bg-blue-100 text-blue-700",      dot: "bg-blue-500"    },
};

export const EDITABLE_STATUSES = ["new", "in-progress", "closed"] as const;

export function defaultMeta(status: string) {
  return {
    label: status.charAt(0).toUpperCase() + status.slice(1),
    color: "text-violet-700",
    bg: "bg-violet-50 border-violet-200",
    pill: "bg-violet-100 text-violet-700",
    dot: "bg-violet-500",
  };
}

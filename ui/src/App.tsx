import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

type Ticket = {
  id: number;
  subject: string;
  body: string;
  tags: string[];
  status: string;
  ai_subject?: string | null;
  category?: string | null;
  suggested_assignee?: string | null;
  created_at: string;
};

async function fetchTickets(): Promise<Ticket[]> {
  const res = await fetch("/api/tickets");
  if (!res.ok) {
    throw new Error("Failed to fetch tickets");
  }
  return res.json();
}

export default function App() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["tickets"],
    queryFn: fetchTickets,
  });

  const [selectedId, setSelectedId] = useState<number | null>(null);

  const tickets = data ?? [];
  const selected =
    tickets.find((t) => t.id === selectedId) ?? tickets[0] ?? null;

  return (
    <div style={{ fontFamily: "Arial", padding: "20px" }}>
      <h1>Ticket System</h1>

      {isLoading && <p>Loading tickets...</p>}
      {isError && <p>Failed to load tickets.</p>}

      {!isLoading && (
        <div style={{ display: "flex", gap: "20px" }}>
          {/* Ticket List */}
          <div style={{ width: "40%", borderRight: "1px solid #ddd" }}>
            {tickets.map((ticket) => (
              <div
                key={ticket.id}
                onClick={() => setSelectedId(ticket.id)}
                style={{
                  padding: "10px",
                  cursor: "pointer",
                  background:
                    selected?.id === ticket.id ? "#f0f0f0" : "white",
                  borderBottom: "1px solid #eee",
                }}
              >
                <strong>{ticket.subject}</strong>
                <div style={{ fontSize: "12px", color: "#666" }}>
                  Status: {ticket.status}
                </div>
              </div>
            ))}
          </div>

          {/* Ticket Detail */}
          <div style={{ width: "60%", paddingLeft: "20px" }}>
            {selected ? (
              <>
                <h2>{selected.subject}</h2>
                <p>
                  <strong>Status:</strong> {selected.status}
                </p>
                <p>
                  <strong>Created:</strong>{" "}
                  {new Date(selected.created_at).toLocaleString()}
                </p>

                {selected.tags?.length > 0 && (
                  <p>
                    <strong>Tags:</strong> {selected.tags.join(", ")}
                  </p>
                )}

                {selected.ai_subject && (
                  <>
                    <h3>AI Suggested Subject</h3>
                    <pre>{selected.ai_subject}</pre>
                  </>
                )}

                <h3>Body</h3>
                <pre
                  style={{
                    whiteSpace: "pre-wrap",
                    background: "#fafafa",
                    padding: "10px",
                    border: "1px solid #eee",
                  }}
                >
                  {selected.body}
                </pre>
              </>
            ) : (
              <p>No tickets available.</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}